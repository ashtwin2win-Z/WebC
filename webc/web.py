import requests
from bs4 import BeautifulSoup
import os
import time
import csv
import re
import uuid
from urllib.parse import urlparse, urljoin

# =========================
# Image Handling
# =========================
class ImageCollection(list):
    """A list-like collection of image URLs with a built-in downloader."""
    def __init__(self, urls, base_url=None, session=None):
        super().__init__(urls)
        self.base_url = base_url
        self.session = session or requests.Session()

    def save_images(self, folder="images", overwrite=False, delay=0.5):
        os.makedirs(folder, exist_ok=True)
        saved_files = []
        
        for i, url in enumerate(self):
            # Resolve relative URLs to absolute ones
            full_url = urljoin(self.base_url, url) if self.base_url else url
            
            # Extract extension and sanitize
            ext = os.path.splitext(full_url)[-1].split("?")[0].lower()
            if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
                ext = ".jpg"
                
            filename = os.path.join(folder, f"image_{i+1}{ext}")

            if not overwrite and os.path.exists(filename):
                saved_files.append(filename)
                continue

            try:
                time.sleep(delay)
                # Downloads using the session containing our Identity/Headers
                resp = self.session.get(full_url, timeout=10)
                resp.raise_for_status()
                with open(filename, "wb") as f:
                    f.write(resp.content)
                saved_files.append(filename)
                print(f"Saved Image: {filename}")
            except Exception as e:
                print(f"Failed to download {full_url}: {e}")

        return saved_files

# =========================
# Core Web Resource
# =========================
class Web:
    """Main entry point. Manages sessions and security policy."""
    def __init__(self, contact=None):
        self.session = requests.Session()
        
        # 1. Identity Layer: Unique Machine ID protects you from global bans
        machine_id = hex(uuid.getnode())[-6:]
        version = "0.1.1"
        project_home = "https://github.com/AshwinPrasanth/Webc"
        
        # Professional User-Agent string
        ua = f"WebC/{version} (User: {contact or 'Anonymous'}; ID:{machine_id}; +{project_home})"
        self.session.headers.update({
            "User-Agent": ua,
            "Accept-Encoding": "gzip"
        })

    def _is_safe(self, url):
        """Security Guard: Blocks SSRF attacks to internal networks."""
        parsed = urlparse(url)
        private_ips = ["127.0.0.1", "localhost", "169.254.169.254", "0.0.0.0"]
        if any(ip in parsed.netloc for ip in private_ips):
            print(f"🛑 Security Block: Internal address {parsed.netloc} is restricted.")
            return False
        return True

    def __getitem__(self, url: str):
        if not self._is_safe(url):
            raise PermissionError(f"Security Policy prevents access to {url}")
        return Resource(url, self.session)

# Global singleton for easy import
web = Web()

class Resource:
    """Represents a single webpage and its data views."""
    def __init__(self, url, session):
        self.url = url
        self.session = session
        self._html = None
        self.structure = StructuredView(self)
        self.query = QueryView(self)

    @property
    def html(self):
        if self._html is None:
            try:
                # 2. Ethical Layer: Forced delay to prevent accidental DoS
                time.sleep(1.0) 
                response = self.session.get(self.url, timeout=15)
                response.raise_for_status()
                
                # 3. RAM Safety: Ignore files larger than 15MB
                if len(response.content) > 15 * 1024 * 1024:
                    print("⚠️ Page too large. Skipping to protect memory.")
                    return ""
                self._html = response.text
            except Exception as e:
                print(f"Fetch failed: {e}")
                return ""
        return self._html

    @property
    def soup(self):
        return BeautifulSoup(self.html, "html.parser")

# =========================
# Structured View (Title, Images, Tables)
# =========================
class StructuredView:
    def __init__(self, resource):
        self.resource = resource

    @property
    def title(self):
        tag = self.resource.soup.find("title")
        return tag.text.strip() if tag else None

    @property
    def images(self):
        """Finds and organizes image URLs into an ImageCollection."""
        content = self.resource.soup.find(id="bodyContent") or self.resource.soup
        all_tags = content.find_all("img")
        
        # Capture images inside <noscript> tags
        for noscript in content.find_all("noscript"):
            ns_soup = BeautifulSoup(noscript.text, "html.parser")
            all_tags.extend(ns_soup.find_all("img"))
        
        urls = []
        for img in all_tags:
            # Prioritize high-res (srcset) then fallback
            src = img.get("srcset", "").split(",")[-1].strip().split(" ")[0] or \
                  img.get("data-src") or img.get("src")
            
            if not src: continue
            
            # Clean junk/UI icons
            if any(x in src.lower() for x in [".svg", "/static/images/"]):
                continue

            urls.append(src)
            
        return ImageCollection(list(dict.fromkeys(urls)), 
                               base_url=self.resource.url, 
                               session=self.resource.session)

    def save_images(self, folder="images", overwrite=False):
        """Action: Saves the collected images to disk."""
        return self.images.save_images(folder=folder, overwrite=overwrite)

    @property
    def tables(self):
        """Extracts wikitable classes using a coordinate grid system for perfect alignment."""
        extracted = []
        for table in self.resource.soup.find_all("table", class_="wikitable"):
            grid = {}
            for r_idx, row in enumerate(table.find_all('tr')):
                cells = row.find_all(['td', 'th'])
                c_idx = 0
                for cell in cells:
                    # Move to next available column in the grid
                    while (r_idx, c_idx) in grid:
                        c_idx += 1
                
                    # Clean text (remove [1] citations)
                    text = re.sub(r'\[.*?\]', '', cell.get_text(strip=True))
                    rowspan = int(cell.get('rowspan', 1))
                    colspan = int(cell.get('colspan', 1))

                    # Fill the coordinate matrix
                    for r in range(r_idx, r_idx + rowspan):
                        for c in range(c_idx, c_idx + colspan):
                            grid[(r, c)] = text
                    c_idx += colspan

            if not grid: continue
            
            # Reconstruct list-of-lists from grid
            max_r = max(k[0] for k in grid.keys()) + 1
            max_c = max(k[1] for k in grid.keys()) + 1
            data = [[grid.get((r, c), "") for c in range(max_c)] for r in range(max_r)]
            
            name = table.find('caption').get_text(strip=True) if table.find('caption') else None
            extracted.append({"name": name, "data": data})
            
        return extracted

    def save_tables(self, folder="tables"):
        """Action: Saves all extracted tables as CSV files."""
        os.makedirs(folder, exist_ok=True)
        saved_paths = []
        for i, table_obj in enumerate(self.tables, 1):
            raw_name = table_obj["name"] or f"table_{i}"
            clean_name = re.sub(r'[^\w\-]', '_', raw_name)
            filename = os.path.join(folder, f"{clean_name}.csv")
            
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    csv.writer(f).writerows(table_obj["data"])
                saved_paths.append(filename)
                print(f"Table Saved: {filename}")
            except Exception as e:
                print(f"Error saving {filename}: {e}")
        return saved_paths

# =========================
# Query View
# =========================
class QueryView:
    """Allows manual CSS selector querying."""
    def __init__(self, resource):
        self.resource = resource

    def __getitem__(self, selector: str):
        return self.resource.soup.select(selector)
