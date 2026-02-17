import requests
from bs4 import BeautifulSoup
import os
import time
import pandas as pd
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import csv
import re

# =========================
# Image Handling
# =========================
class ImageCollection(list):
    def __init__(self, urls, base_url=None):
        super().__init__(urls)
        self.base_url = base_url

    def save_images(self, folder="images", overwrite=False, delay=0.5):
        os.makedirs(folder, exist_ok=True)
        saved_files = []

        for i, url in enumerate(self):
            # Resolve URL
            if url.startswith("//"):
                url = "https:" + url
            elif url.startswith("/"):
                url = self.base_url.rstrip("/") + url if self.base_url else url
            elif url.startswith("http"):
                pass
            else:
                if self.base_url:
                    url = self.base_url.rstrip("/") + "/" + url

            ext = os.path.splitext(url)[-1].split("?")[0] or ".jpg"
            filename = os.path.join(folder, f"image_{i+1}{ext}")

            if not overwrite and os.path.exists(filename):
                saved_files.append(filename)
                continue

            try:
                resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                resp.raise_for_status()
                with open(filename, "wb") as f:
                    f.write(resp.content)
                saved_files.append(filename)
                if delay:
                    time.sleep(delay)
            except Exception as e:
                print(f"Failed to download {url}: {e}")

        return saved_files

# =========================
# Core Web Resource
# =========================
class Web:
    def __getitem__(self, url: str):
        return Resource(url)

web = Web()

class Resource:
    def __init__(self, url: str):
        self.url = url
        self._html = None
        self.structure = StructuredView(self)
        self.query = QueryView(self)
        self.session = requests.Session()
        # ... (keep your retry logic)

    @property
    def html(self):
        if self._html is None:
            headers = {
    "User-Agent": "MyScraperProject/1.0 (https://github.com/AshwinPrasanth/Webc; educational use)",
    "Accept-Encoding": "gzip"
}
            try:
                # IMPORTANT: Slow down. Spaming requests triggers the 403 block.
                time.sleep(2.0) 
                response = self.session.get(self.url, headers=headers, timeout=15)
                response.raise_for_status()
                self._html = response.text
            except Exception as e:
                print(f"Fetch failed: {e}")
                return ""
        return self._html

    @property
    def soup(self):
        return BeautifulSoup(self.html, "html.parser")

# =========================
# Structured View (Title, Links, Images, Tables)
# =========================
class StructuredView:
    def __init__(self, resource: Resource):
        self.resource = resource

    @property
    def title(self):
        title_tag = self.resource.soup.find("title")
        return title_tag.text.strip() if title_tag else None

    @property
    def links(self):
        return [a.get("href") for a in self.resource.soup.find_all("a") if a.get("href")]

    @property
    def images(self):
        content_area = self.resource.soup.find(id="bodyContent") or self.resource.soup
        
        # 1. Collect every <img> tag
        all_tags = content_area.find_all("img")
        
        # 2. Collect every <img> hidden in <noscript>
        for noscript in content_area.find_all("noscript"):
            ns_soup = BeautifulSoup(noscript.text, "html.parser")
            all_tags.extend(ns_soup.find_all("img"))
        
        urls = []
        for img in all_tags:
            # Check srcset for high-res first, then data-src, then src
            src = None
            srcset = img.get("srcset")
            if srcset:
                # Get the highest quality link (usually at the end of the list)
                src = srcset.split(",")[-1].strip().split(" ")[0]
            
            if not src:
                src = img.get("data-src") or img.get("src")

            if not src: continue

            # Fix protocol
            if src.startswith("//"): src = "https:" + src
            elif src.startswith("/"): src = "https://en.wikipedia.org" + src

            # Only block the absolute junk (SVGs and UI icons)
            if any(x in src.lower() for x in [".svg", "/static/images/"]):
                continue

            urls.append(src)
            
        unique_urls = list(dict.fromkeys(urls))
        print(f"Found {len(unique_urls)} potential images. Starting download...")
        return ImageCollection(unique_urls, base_url=self.resource.url)

    def save_images(self, folder="images", overwrite=False):
        os.makedirs(folder, exist_ok=True)
        image_list = self.images  
        saved_files = []

        for i, url in enumerate(image_list):
            # Resolve extension
            ext = os.path.splitext(url)[-1].split("?")[0].lower()
            if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
                ext = ".jpg"

            # CRITICAL: Unique filename per index
            filename = os.path.join(folder, f"image_{i+1}{ext}")

            try:
                # Add a 1s delay to avoid being blocked mid-download
                time.sleep(1.0)
                headers = {"User-Agent": "Mozilla/5.0"}
                resp = requests.get(url, headers=headers, timeout=10)
                resp.raise_for_status()
                
                with open(filename, "wb") as f:
                    f.write(resp.content)
                saved_files.append(filename)
                print(f"Saved: {filename}")
            except Exception as e:
                print(f"Failed {url}: {e}")

        return saved_files

    @property

    def tables(self):
        extracted_tables = []
        content_tables = self.resource.soup.find_all("table", class_="wikitable")
        for table in content_tables:
            rows = table.find_all('tr')
            # Map out the grid (rows x columns)
            grid = {} 
            for r_idx, row in enumerate(rows):
                cells = row.find_all(['td', 'th'])
                c_idx = 0
                for cell in cells:
                    # Find the next empty slot in the grid for this row
                    while (r_idx, c_idx) in grid:
                        c_idx += 1
                
                    # Get cell properties
                    text = re.sub(r'\[.*?\]', '', cell.get_text(strip=True))
                    rowspan = int(cell.get('rowspan', 1))
                    colspan = int(cell.get('colspan', 1))

                    # Fill the grid for all covered spans
                    for r in range(r_idx, r_idx + rowspan):
                        for c in range(c_idx, c_idx + colspan):
                            grid[(r, c)] = text
                    c_idx += colspan

            # Convert the grid dictionary back into a list of lists
            max_r = max(key[0] for key in grid.keys()) + 1 if grid else 0
            max_c = max(key[1] for key in grid.keys()) + 1 if grid else 0
        
            table_data = []
            for r in range(max_r):
                row_data = [grid.get((r, c), "") for c in range(max_c)]
                table_data.append(row_data)

            extracted_tables.append({"name": table.find('caption').get_text(strip=True) if table.find('caption') else None,
            "data": table_data})
        return extracted_tables

    def save_tables(self, folder="tables"):
        os.makedirs(folder, exist_ok=True)
        table_list = self.tables 
        saved_files = []

        for i, table_obj in enumerate(table_list, start=1):
            # Use caption for filename if it exists, otherwise use the index
            raw_name = table_obj["name"] if table_obj["name"] else f"table_{i}"
            # Sanitize filename (remove spaces and special characters)
            clean_name = re.sub(r'[^\w\-_\. ]', '_', raw_name).replace(' ', '_')
            filename = os.path.join(folder, f"{clean_name}.csv")
            
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerows(table_obj["data"])
                saved_files.append(filename)
            except Exception as e:
                print(f"Error saving {filename}: {e}")
                
        return saved_files

# =========================
# Query View
# =========================
class QueryView:
    def __init__(self, resource: Resource):
        self.resource = resource

    def __getitem__(self, selector: str):
        return self.resource.soup.select(selector)