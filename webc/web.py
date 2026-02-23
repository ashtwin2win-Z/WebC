import requests
from bs4 import BeautifulSoup
import os
import time
import csv
import re
import uuid
from urllib.parse import urlparse, urljoin
from .websoc import SocialView

# =========================
# Image Handling
# =========================
class ImageCollection(list):
    def __init__(self, urls, base_url=None, session=None):
        super().__init__(urls)
        self.base_url = base_url
        self.session = session or requests.Session()

    def save_images(self, folder="images", overwrite=False, delay=0.5):
        safe_folder = os.path.basename(folder)
        target_dir = os.path.join(os.getcwd(), safe_folder)
        os.makedirs(target_dir, exist_ok=True)
        
        if len(self) > 50:
            print("⚠️ Too many images found. Limiting download to first 50 for safety.")
            download_list = self[:50]
        else:
            download_list = self

        saved_files = []
        for i, url in enumerate(download_list):
            full_url = urljoin(self.base_url, url) if self.base_url else url
            ext = os.path.splitext(full_url)[-1].split("?")[0].lower()
            if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
                ext = ".jpg"
                
            filename = os.path.join(target_dir, f"image_{i+1}{ext}")

            if not overwrite and os.path.exists(filename):
                saved_files.append(filename)
                continue

            try:
                time.sleep(delay)
                resp = self.session.get(full_url, timeout=10)
                resp.raise_for_status()
                with open(filename, "wb") as f:
                    f.write(resp.content)
                saved_files.append(filename)
            except Exception as e:
                print(f"Failed to download {full_url}: {e}")
        return saved_files

# =========================
# Core Web Resource
# =========================
class Web:
    def __init__(self, contact=None):
        self.session = requests.Session()
        machine_id = hex(uuid.getnode())[-6:]
        
        # VERSION BUMP: 0.2.0 marks the Unlocked Release
        version = "0.2.0"
        project_home = "https://github.com/ashtwin2win-Z/WebC"
        
        ua = f"WebC/{version} (User: {contact or 'Anonymous'}; ID:{machine_id}; +{project_home})"
        self.session.headers.update({
            "User-Agent": ua,
            "Accept-Encoding": "gzip"
        })

    def _is_safe(self, url):
        """Security Guard: Protocol Enforcement & SSRF Protection."""
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()

        # 1. REMOVED: Wikipedia-Only Restriction is gone.
        
        # 2. SECURITY: HTTPS Enforcement (Crucial for public web)
        if parsed.scheme != "https":
            raise PermissionError("WebC requires HTTPS for secure data transmission.")

        # 3. SECURITY: SSRF Protection (Prevents hitting internal networks)
        private_ips = ["127.0.0.1", "localhost", "169.254.169.254", "0.0.0.0", "::1"]
        if any(ip in host for ip in private_ips) or host.startswith("192.168.") or host.startswith("10."):
            raise PermissionError(f"Security Block: {host} is a private address and is restricted.")
            
        return True

    def __getitem__(self, url: str):
        self._is_safe(url)
        return Resource(url, self.session)

web = Web()

class Resource:
    def __init__(self, url, session):
        self.url = url
        self.session = session
        self._html = None
        self.structure = StructuredView(self)
        self.query = QueryView(self)
        self.task = TaskView(self)
        self.social = SocialView(self)

    @property
    def html(self):
        if self._html is None:
            try:
                time.sleep(1.0) 
                response = self.session.get(self.url, timeout=15)
                response.raise_for_status()
                
                if len(response.content) > 15 * 1024 * 1024:
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
# Structured View
# =========================
class StructuredView:
    def __init__(self, resource):
        self.resource = resource

    @property
    def title(self):
        tag = self.resource.soup.find("title")
        return tag.text.strip() if tag else None
    
    @property
    def links(self):
        tags = self.resource.soup.find_all("a", href=True)
        urls = []
        for tag in tags:
            full_url = urljoin(self.resource.url, tag['href'])
            urls.append(full_url)
        return list(dict.fromkeys(urls))

    @property
    def images(self):
        # Fallback for non-Wikipedia sites that don't use 'bodyContent'
        content = self.resource.soup.find(id="bodyContent") or self.resource.soup
        all_tags = content.find_all("img")
        
        for noscript in content.find_all("noscript"):
            ns_soup = BeautifulSoup(noscript.text, "html.parser")
            all_tags.extend(ns_soup.find_all("img"))
        
        urls = []
        for img in all_tags:
            src = img.get("srcset", "").split(",")[-1].strip().split(" ")[0] or \
                  img.get("data-src") or img.get("src")
            
            if not src: continue
            if any(x in src.lower() for x in [".svg", "/static/images/"]):
                continue
            urls.append(src)
            
        return ImageCollection(list(dict.fromkeys(urls)), 
                               base_url=self.resource.url, 
                               session=self.resource.session)

    def save_images(self, folder="images", overwrite=False):
        return self.images.save_images(folder=folder, overwrite=overwrite)

    @property
    def tables(self):
        extracted = []
        # Generalize: look for 'wikitable' first, then any standard 'table'
        tables = self.resource.soup.find_all("table", class_="wikitable") or \
                 self.resource.soup.find_all("table")

        for table in tables:
            grid = {}
            for r_idx, row in enumerate(table.find_all('tr')):
                cells = row.find_all(['td', 'th'])
                c_idx = 0
                for cell in cells:
                    while (r_idx, c_idx) in grid:
                        c_idx += 1
                
                    text = re.sub(r'\[.*?\]', '', cell.get_text(strip=True))
                    rowspan = int(cell.get('rowspan', 1))
                    colspan = int(cell.get('colspan', 1))

                    for r in range(r_idx, r_idx + rowspan):
                        for c in range(c_idx, c_idx + colspan):
                            grid[(r, c)] = text
                    c_idx += colspan

            if not grid: continue
            
            max_r = max(k[0] for k in grid.keys()) + 1
            max_c = max(k[1] for k in grid.keys()) + 1
            data = [[grid.get((r, c), "") for c in range(max_c)] for r in range(max_r)]
            
            name = table.find('caption').get_text(strip=True) if table.find('caption') else None
            extracted.append({"name": name, "data": data})
            
        return extracted

    def save_tables(self, folder="tables"):
        safe_folder = os.path.basename(folder)
        target_dir = os.path.join(os.getcwd(), safe_folder)
        os.makedirs(target_dir, exist_ok=True)
        
        saved_paths = []
        for i, table_obj in enumerate(self.tables, 1):
            raw_name = table_obj["name"] or f"table_{i}"
            clean_name = re.sub(r'[^\w\-]', '_', raw_name)
            filename = os.path.join(target_dir, f"{clean_name}.csv")
            
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    csv.writer(f).writerows(table_obj["data"])
                saved_paths.append(filename)
            except Exception as e:
                print(f"Error saving {filename}: {e}")
        return saved_paths
    @property
    def metadata(self):
        """Mines OpenGraph, Twitter, and standard Meta tags for SocialView."""
        meta_data = {}
        tags = self.resource.soup.find_all("meta")
        for tag in tags:
            # Looks for 'property' (OG tags) or 'name' (Twitter/Standard tags)
            key = tag.get("property") or tag.get("name")
            value = tag.get("content")
            if key and value:
                meta_data[key] = value
        return meta_data

# =========================
# Query View
# =========================
class QueryView:
    def __init__(self, resource):
        self.resource = resource

    def __getitem__(self, selector: str):
        return self.resource.soup.select(selector)

class TaskView:
    def __init__(self, resource):
        self.resource = resource

    def summarize(self, max_chars=200, refine=True):
        """
        Extracts and cleans page content.
        :param max_chars: Maximum length of the returned string.
        :param refine: If True, removes citations [1], [edit] tags, and extra noise.
        """
        # 1. Extraction logic
        paragraphs = self.resource.soup.find_all('p')
        text = " ".join([p.get_text().strip() for p in paragraphs])
        
        # Fallback to social description if body text is empty
        if not text or len(text) < 20:
            text = self.resource.social.preview.get("description") or ""

        # 2. Refinement Layer (Optional)
        if refine:
            # Remove Wikipedia-style citations [1], [23], etc.
            text = re.sub(r'\[\d+\]', '', text)
            # Remove "[edit]" and bracketed noise
            text = re.sub(r'\[edit\]|\[.*?\]', '', text)
            # Standardize whitespace
            text = re.sub(r'\s+', ' ', text).strip()

        # 3. Truncation
        if len(text) <= max_chars:
            return text
            
        # Cut at last space to avoid breaking words
        truncated = text[:max_chars].rsplit(' ', 1)[0]
        return f"{truncated.rstrip(',;:-—')}..."