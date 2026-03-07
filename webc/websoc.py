# Copyright 2026 Ashwin Prasanth
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import re


class SocialView:
    """Standalone Intelligence layer for social media normalization."""

    def __init__(self, resource=None):
        self.resource = resource
        self._standalone_meta = {}
        self._standalone_url = None
        self._standalone_title = ""
        self._structured_data = {}
        self._credits = {}

        self.session = requests.Session()
        # Bypasses the "Before you continue to YouTube" consent page
        self.session.cookies.set("CONSENT", "YES+cb.20210328-17-p0.en+FX+406", domain=".youtube.com")
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/"
        })

    # =========================
    # Entry Point
    # =========================
    def __getitem__(self, url: str):
        """Allows social['url'] usage with inherited safety."""
        # Security handoff to web.py if available
        try:
            from .web import web as web_core
            web_core._is_safe(url)
        except (ImportError, AttributeError):
            if not url.startswith("https://"):
                raise PermissionError("SocialView requires HTTPS.")

        self._standalone_url = url

        # Reddit JSON endpoint trick for high-fidelity data
        target_url = url.rstrip('/') + ".json" if "reddit.com/r/" in url else url

        try:
            resp = self.session.get(target_url, timeout=10)

            if target_url.endswith(".json"):
                self._standalone_meta = {"_json_source": resp.json()}
            else:
                soup = BeautifulSoup(resp.text, "html.parser")
                self._standalone_title = soup.title.string if soup.title else ""
                self._extract_all(soup)

        except Exception:
            pass  # Maintain robustness for batch processing

        return self

    # =========================
    # Platform Detection
    # =========================
    @property
    def platform(self):
        url = self.resource.url if self.resource else self._standalone_url
        if not url:
            return "Unknown"
        host = urlparse(url).hostname or ""
        mapping = {
            "youtube.com": "YouTube", "youtu.be": "YouTube",
            "twitter.com": "X",       "x.com": "X",
            "reddit.com": "Reddit",   "github.com": "GitHub",
            "instagram.com": "Instagram", "facebook.com": "Facebook"
        }
        for domain, name in mapping.items():
            if domain in host.lower():
                return name
        return "Generic Web"

    # =========================
    # Preview Card
    # =========================
    @property
    def preview(self):
        """Standardizes data into a clean 'Share Card' dictionary."""
        meta = self.resource.structure.metadata if self.resource else self._standalone_meta
        title_bkp = self.resource.structure.title if self.resource else self._standalone_title

        # Reddit high-fidelity path
        if "_json_source" in self._standalone_meta:
            post = self._standalone_meta["_json_source"][0]['data']['children'][0]['data']
            return {
                "title":        post.get("title"),
                "description":  post.get("selftext", "")[:200],
                "image":        post.get("thumbnail"),
                "brand":        f"r/{post.get('subreddit')}",
                "content_type": "reddit_post"
            }

        # Standard OpenGraph / JSON-LD path
        return {
            "title":        meta.get("og:title") or self._structured_data.get("name") or title_bkp,
            "description":  meta.get("og:description") or self._structured_data.get("description"),
            "image":        meta.get("og:image") or meta.get("twitter:image"),
            "brand":        meta.get("og:site_name") or self.platform,
            "content_type": meta.get("og:type", "website")
        }

    # =========================
    # Video ID
    # =========================
    @property
    def video_id(self):
        url = self.resource.url if self.resource else self._standalone_url
        if self.platform != "YouTube" or not url:
            return None
        parsed = urlparse(url)
        queries = parse_qs(parsed.query)
        if "v" in queries:
            return queries["v"][0]
        return parsed.path.strip("/") if "youtu.be" in parsed.netloc else None

    # =========================
    # Auto Bio
    # =========================
    def auto_bio(self, include_metrics=True):
        data = self.preview
        title = (data.get("title") or "").strip()
        desc  = (data.get("description") or "").strip()

        if title and desc:
            short_title = re.split(r' [|:\-–] ', title)[0]
            bio = f"{short_title}: {desc}"
        else:
            bio = title or desc or "Resource preview unavailable."

        m = self.metrics
        if include_metrics and any(m.values()):
            stats = " | ".join([f"{k.capitalize()}: {v}" for k, v in m.items() if v])
            bio += f" [{stats}]"

        return (bio[:250] + "...") if len(bio) > 253 else bio

    # =========================
    # Metrics
    # =========================
    @property
    def metrics(self):
        return {
            "views":    self._standalone_meta.get("_views", "0"),
            "likes":    self._standalone_meta.get("_likes", "0"),
            "metadata": self._standalone_meta.get("og:description", "No metadata found.")
        }

    # =========================
    # Core Extraction
    # =========================
    def _extract_all(self, soup):
        raw_html = str(soup)

        # 1. TITLE SNIPER
        title_match = re.search(r'\"title\":\{\"runs\":\[\{\"text\":\"(.*?)\"\}\]', raw_html)
        if title_match:
            self._standalone_title = title_match.group(1)

        # 2. VIEW COUNT HUNTER
        v_match = (
            re.search(r'\"viewCount\":\"(\d+)\"', raw_html) or
            re.search(r'\"viewCountText\":\{\"simpleText\":\"([\d,.]+)\s*views\"\}', raw_html) or
            re.search(r'\"videoViewCountRenderer\":\{\"viewCount\":\{\"simpleText\":\"([\d,.]+)', raw_html)
        )
        if v_match:
            self._standalone_meta["_views"] = re.sub(r'[^\d]', '', v_match.group(1))

        # 3. LIKE COUNT SNIPER
        like_match = re.search(r'like this video along with ([\d,]+)', raw_html)
        if like_match:
            self._standalone_meta["_likes"] = like_match.group(1).replace(',', '')

        # 4. DESCRIPTION VACUUM
        desc = None
        all_fragments = re.findall(r'\"(?:text|content)\"\:\"(.*?)(?<!\\)\"', raw_html)

        if all_fragments:
            # Find the start of the credits/description block
            start_index = 0
            for i, frag in enumerate(all_fragments):
                if any(kw in frag for kw in ["Provided to YouTube", "Presenting", "Director of Photography"]):
                    start_index = i
                    break

            target_frags = all_fragments[start_index: start_index + 150]
            raw_combined = "".join(target_frags)

            try:
                desc = raw_combined.encode().decode('unicode-escape').replace('\\"', '"').replace('\\n', '\n')
            except Exception:
                desc = raw_combined.replace('\\n', '\n').replace('\\"', '"')

        # Store raw desc or fallback
        if desc and "Enjoy the videos" not in desc and len(desc) > 20:
            self._standalone_meta["og:description"] = desc.replace('&amp;', '&').strip()
        else:
            m = soup.find("meta", {"name": "description"})
            self._standalone_meta["og:description"] = m.get("content") if m else "No metadata found."

        # Refine and store the cleaned version
        self._standalone_meta["og:description"] = self._refine_metadata(
            self._standalone_meta["og:description"]
        )

    # =========================
    # Metadata Refinement
    # =========================
    def _refine_metadata(self, raw: str) -> str:
        if not raw:
            return "No metadata found."

        # 1. ENCODING FIX: Repair mojibake characters
        replacements = {
            'â\x80\x9c': '"', 'â\x80\x9d': '"',
            'â\x80\x94': '—', 'â\x80\x93': '–',
            'â\x80\x99': "'", 'â\x80\x98': "'",
            'â\x80\xa2': '•', 'Â©': '©',
            'Â®': '®', 'Â': '', 'â¥': '♥',
        }
        for bad, good in replacements.items():
            raw = raw.replace(bad, good)

        # 2. CUTOFF: Stop where recommended videos bleed in
        cutoff_signals = [
            "Add to queue",
            "Save to playlist",
            "views ago",
            "Subscribe",
            "Watch later",
        ]
        for signal in cutoff_signals:
            idx = raw.find(signal)
            if idx != -1:
                raw = raw[:idx].strip()
                break

        # 3. CLEANUP: Remove social follow lines and blank lines
        lines = raw.splitlines()
        cleaned = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if any(skip in line for skip in ["Follow us:", "Like us:", "Twitter:", "Facebook:"]):
                continue
            cleaned.append(line)

        return "\n".join(cleaned)


# Global instance
social = SocialView()