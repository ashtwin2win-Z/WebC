import requests
from bs4 import BeautifulSoup
import os
import time
import requests

class ImageCollection(list):
    def __init__(self, urls, base_url=None):
        super().__init__(urls)
        self.base_url = base_url  # for resolving relative URLs

    def save_images(self, folder="images", overwrite=False, delay=0.5):
        """
        Download all images in this collection to a folder.
        delay: seconds to wait between downloads (default 0.5s)
        """
        os.makedirs(folder, exist_ok=True)
        saved_files = []

        for i, url in enumerate(self):
            # Resolve URL
            if url.startswith("//"):
                url = "https:" + url
            elif url.startswith("/"):
                url = "https://en.wikipedia.org" + url
            elif url.startswith("http"):
                pass
            else:
                # relative to page URL
                if self.base_url:
                    url = self.base_url.rstrip("/") + "/" + url

            # Determine local filename
            ext = os.path.splitext(url)[-1].split("?")[0] or ".jpg"
            filename = os.path.join(folder, f"image_{i+1}{ext}")

            if not overwrite and os.path.exists(filename):
                saved_files.append(filename)
                continue

            try:
                resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
                resp.raise_for_status()
                with open(filename, "wb") as f:
                    f.write(resp.content)
                saved_files.append(filename)
                if delay:
                    time.sleep(delay)
            except Exception as e:
                print(f"Failed to download {url}: {e}")

        return saved_files


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
        self.task = TaskView(self)

    @property
    def html(self):
        if self._html is None:
            headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/114.0.0.0 Safari/537.36"
        }

            response = requests.get(self.url, headers=headers)
            response.raise_for_status()
            self._html = response.text
        return self._html

    @property
    def soup(self):
        return BeautifulSoup(self.html, "html.parser")
    
class StructuredView:
    def __init__(self, resource: 'Resource'):
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
        """
        Return ImageCollection of main content images only (avoid nav/footer).
        """
        # Grab images only inside the article/main content
        content_imgs = self.resource.soup.select("#content img")
        urls = [img.get("src") for img in content_imgs if img.get("src")]
        return ImageCollection(urls, base_url=self.resource.url)

    def save_images(self, folder="images", overwrite=False, delay=0.5):
        """Shortcut: download all main content images"""
        return self.images.save_images(folder=folder, overwrite=overwrite, delay=delay)

class QueryView:
    def __init__(self, resource: Resource):
        self.resource = resource

    def __getitem__(self, selector: str):
        return self.resource.soup.select(selector)

class TaskView:
    def __init__(self, resource: Resource):
        self.resource = resource

    def summarize(self, max_chars: int = 500):
        text = self.resource.soup.get_text(separator=" ", strip=True)
        return text[:max_chars] + "..." if len(text) > max_chars else text