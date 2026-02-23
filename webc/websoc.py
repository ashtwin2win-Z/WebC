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

import json
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
        self._structured_data = {}  # <--- FIX: This was missing!
        self._credits = {}          # <--- FIX: This was missing!
        
        self.session = requests.Session()
        # Bypasses the "Before you continue to YouTube" consent page
        self.session.cookies.set("CONSENT", "YES+cb.20210328-17-p0.en+FX+406", domain=".youtube.com")
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/"
        })

    def __getitem__(self, url):
        """Allows social['url'] usage with inherited safety."""
        # 1. SECURITY HANDOFF
        # Import the global 'web' instance from your core library
        try:
            from .web import web as web_core
            web_core._is_safe(url)
        except (ImportError, AttributeError):
            # If for some reason web.py isn't accessible, we fallback to basic HTTPS check
            if not url.startswith("https://"):
                raise PermissionError("SocialView requires HTTPS.")

        self._standalone_url = url
        
        # 2. TARGET PREPARATION
        # Reddit JSON endpoint trick remains for reliability
        target_url = url.rstrip('/') + ".json" if "reddit.com/r/" in url else url
        
        try:
            # We use the SocialView's dedicated session (with the consent cookies)
            resp = self.session.get(target_url, timeout=10)
            
            if target_url.endswith(".json"):
                # Reddit deep data path
                self._standalone_meta = {"_json_source": resp.json()}
            else:
                # Standard HTML path (YouTube, X, etc.)
                soup = BeautifulSoup(resp.text, "html.parser")
                self._standalone_title = soup.title.string if soup.title else ""
                
                # This triggers the 'Global Vacuum' you just perfected
                self._extract_all(soup)
                
        except Exception:
            pass  # Maintain robustness for batch processing
            
        return self

    @property
    def platform(self):
        url = self.resource.url if self.resource else self._standalone_url
        if not url: return "Unknown"
        host = urlparse(url).hostname or ""
        mapping = {
            "youtube.com": "YouTube", "youtu.be": "YouTube",
            "twitter.com": "X", "x.com": "X",
            "reddit.com": "Reddit", "github.com": "GitHub",
            "instagram.com": "Instagram", "facebook.com": "Facebook"
        }
        for domain, name in mapping.items():
            if domain in host.lower(): return name
        return "Generic Web"


    @property
    def preview(self):
        """Standardizes data into a clean 'Share Card' dictionary."""
        # Use web.py metadata if available, otherwise use standalone meta
        meta = self.resource.structure.metadata if self.resource else self._standalone_meta
        title_bkp = self.resource.structure.title if self.resource else self._standalone_title

        # Check Reddit JSON first for high-fidelity data
        if "_json_source" in self._standalone_meta:
            post = self._standalone_meta["_json_source"][0]['data']['children'][0]['data']
            return {
                "title": post.get("title"),
                "description": post.get("selftext")[:200],
                "image": post.get("thumbnail"),
                "brand": f"r/{post.get('subreddit')}",
                "content_type": "reddit_post"
            }

        # Fallback to standard OpenGraph / JSON-LD
        return {
            "title": meta.get("og:title") or self._structured_data.get("name") or title_bkp,
            "description": meta.get("og:description") or self._structured_data.get("description"),
            "image": meta.get("og:image") or meta.get("twitter:image"),
            "brand": meta.get("og:site_name") or self.platform,
            "content_type": meta.get("og:type", "website")
        }

    @property
    def video_id(self):
        url = self.resource.url if self.resource else self._standalone_url
        if self.platform != "YouTube" or not url: return None
        parsed = urlparse(url)
        queries = parse_qs(parsed.query)
        if "v" in queries: return queries["v"][0]
        return parsed.path.strip("/") if "youtu.be" in parsed.netloc else None

    def auto_bio(self, include_metrics=True):
        data = self.preview
        title = (data.get("title") or "").strip()
        desc = (data.get("description") or "").strip()
        
        if title and desc:
            short_title = re.split(r' [|:\-–] ', title)[0]
            bio = f"{short_title}: {desc}"
        else:
            bio = title or desc or "Resource preview unavailable."

        # Attach metrics if requested
        m = self.metrics
        if include_metrics and any(m.values()):
            stats = " | ".join([f"{k.capitalize()}: {v}" for k, v in m.items() if v])
            bio += f" [{stats}]"

        return (bio[:250] + "...") if len(bio) > 253 else bio
    
    
    def _extract_all(self, soup):
        raw_html = str(soup)
        
        # 1. SNIPE THE TITLE
        title_match = re.search(r'\"title\":\{\"runs\":\[\{\"text\":\"(.*?)\"\}\]', raw_html)
        if title_match:
            self._standalone_title = title_match.group(1)

        # 2. THE ULTIMATE VIEW HUNTER (Keep your working version)
        v_match = re.search(r'\"viewCount\":\"(\d+)\"', raw_html) or \
                  re.search(r'\"viewCountText\":\{\"simpleText\":\"([\d,.]+)\s*views\"\}', raw_html) or \
                  re.search(r'\"videoViewCountRenderer\":\{\"viewCount\":\{\"simpleText\":\"([\d,.]+)', raw_html)
        if v_match:
            self._standalone_meta["_views"] = re.sub(r'[^\d]', '', v_match.group(1))

        # 3. THE LIKE SNIPER (Keep your working version)
        like_match = re.search(r'like this video along with ([\d,]+)', raw_html)
        if like_match:
            self._standalone_meta["_likes"] = like_match.group(1).replace(',', '')

        # 4. THE GLOBAL VACUUM SNIPER
        desc = None
        
        # We search for the TWO major places YouTube hides the description fragments
        # 1. description (Standard/Music) 
        # 2. attributedDescriptionBodyText (New 2026 Layout)
        
        # We use re.findall to find EVERY piece of text in the entire file 
        # that looks like a description fragment.
        
        # This finds text inside "runs" or "content" blocks
        all_fragments = re.findall(r'\"(?:text|content)\"\:\"(.*?)(?<!\\)\"', raw_html)
        
        if all_fragments:
            # We filter for the "Sweet Spot": fragments that appear after 
            # the video title but before the comment section starts.
            # We are looking for the "Provided to YouTube" or "Presenting" footprint.
            
            # Find where the description starts in the list
            start_index = 0
            for i, frag in enumerate(all_fragments):
                if "Provided to YouTube" in frag or "Presenting" in frag or "Director of Photography" in frag:
                    start_index = i
                    break
            
            # Capture the next 200 fragments (usually enough for any credit list)
            # This stops it from grabbing random UI text like "Subscribe" or "Comments"
            target_frags = all_fragments[start_index : start_index + 150]
            
            # Join and decode
            raw_combined = "".join(target_frags)
            try:
                desc = raw_combined.encode().decode('unicode-escape').replace('\\"', '"').replace('\\n', '\n')
            except:
                desc = raw_combined.replace('\\n', '\n').replace('\\"', '"')

        # FINAL CLEANUP (Replace your current final block with this)
        if desc and "Enjoy the videos" not in desc and len(desc) > 20:
            desc = desc.replace('&amp;', '&').strip()
            self._standalone_meta["og:description"] = desc
        else:
            m = soup.find("meta", {"name": "description"})
            self._standalone_meta["og:description"] = m.get("content") if m else "No metadata found."

        # THE NEW LINE TO ADD:
        return self._refine_metadata(self._standalone_meta["og:description"])



    @property
    def metrics(self):
        return {
            "views": self._standalone_meta.get("_views", "0"),
            "likes": self._standalone_meta.get("_likes", "0"),
            "metadata": self._standalone_meta.get("og:description", "No metadata found.")
        }
    

# Global instance
social = SocialView()
