<h1 align="center"> WebC – Treat Websites as Python Objects</h1>

<p align="center">
<img src="https://github.com/ashtwin2win-Z/WebC/raw/main/assets/webc.png" alt="WebC Logo" width="280">
</p>

**Version:** 0.2.0
**Author:** Ashwin Prasanth

---

## Overview

`webc` is a Python library that allows you to treat websites as programmable Python objects.

Instead of manually handling HTTP requests, parsing HTML, and writing repetitive scraping logic, WebC provides a structured, object-oriented interface to access semantic content, query elements, and perform intent-driven tasks.

The goal is simple:

* Make web data feel native to Python
* Provide meaningful abstractions over raw HTML
* Encourage ethical and secure usage by default

---

## 🚀 New Release – v0.2.0 (The Unlocked Release)

WebC v0.2.0 marks a major architectural milestone.

### Global Access

* Wikipedia-only restriction removed
* Supports **any HTTPS domain**
* Domain-agnostic resource abstraction

### TaskView 2.0

* `summarize(max_chars=500, refine=True)`
* Adjustable summary length
* Optional refinement to remove citation noise and formatting artifacts
* Intelligent fallback behavior when structured content is limited

### Foundation for WebSoc (Beta)

> **Disclaimer ⚠️:** WebSoc is currently in beta. Use only for research, educational, or personal automation purposes. Do not use for mass scraping, commercial exploitation or violating platform Terms of Service. Users are responsible for complying with website Terms of Service.

* Core engine now supports expansion into social platforms
* Designed to extract structured metadata from complex layouts
* Introduction of the first WebSoc module in beta testing

#### Websoc is a beta version: ⚠️ Metadata may still contain noise in this beta release.
* Current beta provides structured previews, engagement metrics, and object-based access.
* Future versions will include refined outputs, noise filtering, and expanded platform coverage.

### Websoc usecase

```python
from webc.websoc import social

# Initialize a WebSoc object for a public video URL.
# This securely fetches and parses the page.
# Note: WebSoc is currently in BETA; metadata may contain noise.
url = "https://www.youtube.com/watch?v=VIDEO_ID"  # Beta example: YouTube video URL for testing
video = social[url]

# --- Basic Identity ---
# Returns a lightweight preview dictionary (e.g., cleaned title).
print("Video Title:", video.preview["title"])

# Extracts the canonical video ID from the URL.
print("Video ID:", video.video_id)

# --- Engagement Metrics ---
# Returns a structured dictionary containing engagement data.
# Example keys: "views", "likes", "metadata"
print("Views:", video.metrics.get("views"))   # Total view count
print("Likes:", video.metrics.get("likes"))   # Total like count

# --- Extended Metadata (Optional) ---
# Returns a decoded metadata block if available.
# In this beta, metadata may still contain noise (unwanted text fragments).
print("Full Metadata & Credits:", video.metrics.get("metadata"))
```


### Centralized Security Maintained

* Mandatory HTTPS enforcement
* SSRF protection
* Restricted internal network access
* Safe file handling
* Controlled request behavior

---

## Installation

Install via pip:

```bash
pip install webc
```

### Dependencies

* requests
* beautifulsoup4

---

## Core Architecture

WebC is organized into four conceptual layers.

---

### 1. Resource Layer

Access a webpage as a `Resource` object:

```python
from webc import web

site = web["https://example.com"]
```

* Represents a single webpage
* Uses lazy loading (fetches HTML only when needed)
* Caches parsed content internally

---

### 2. Structure Layer

Provides semantic, high-level content extracted from the page:

```python
site.structure.title
site.structure.links
site.structure.images
site.structure.tables
```

#### Image Handling

* Extracts from `src`, `srcset`, `data-src`, and `<noscript>`
* Filters UI icons and SVG assets
* Resolves relative URLs automatically

Download images:

```python
site.structure.save_images(folder="images")
```

#### Table Extraction

* Detects structured HTML tables
* Handles rowspan and colspan alignment
* Removes citation brackets (e.g., `[1]`) where applicable

Save tables as CSV:

```python
site.structure.save_tables(folder="data")
```

---

### 3. Query Layer

Provides direct DOM access via CSS selectors:

```python
headings = site.query["h1, h2"]

for h in headings:
    print(h.get_text(strip=True))
```

* Returns BeautifulSoup elements
* Useful for custom extraction logic
* Acts as an advanced access layer

---

### 4. Task Layer (TaskView 2.0)

Provides intent-driven actions:

```python
summary = site.task.summarize(max_chars=500, refine=True)
print(summary)
```

Currently supported:

* `summarize(max_chars=500, refine=True)`

More intelligent tasks will be introduced in future releases.

---

## Security & Usage Policy

WebC is built with security-first defaults.

### Platform Rules

* Only **HTTPS URLs** are allowed
* Private and internal network addresses are blocked
* No login bypass mechanisms
* No CAPTCHA circumvention

### Built-in Protections

WebC includes safeguards against:

* SSRF attacks
* Path traversal
* Unsafe file writes
* Excessive downloads

Requests are controlled and content is cached to prevent unnecessary repeated fetching.

---

## Responsible Use

WebC is designed for:

✔ Educational purposes
✔ Research
✔ Personal automation
✔ Ethical data access

It must not be used for:

* Mass scraping
* Circumventing website policies
* Service disruption
* Data abuse

Users are responsible for complying with website Terms of Service.

---

## Full Usage Example

```python
from webc import web

url = "https://example.com"
site = web[url]

print("=== STRUCTURE ===")
print(f"Title: {site.structure.title}")
print(f"Total Links: {len(site.structure.links)}")
print(f"First 5 links: {site.structure.links[:5]}")

print("\n--- Downloading Resources ---")
site.structure.save_images(folder="images")
site.structure.save_tables(folder="data")

print("\n=== QUERY ===")
headings = site.query["h1, h2"]
print(f"Found {len(headings)} headings:")

for h in headings[:3]:
    print(f" - {h.get_text(strip=True)}")

print("\n=== TASK ===")
summary = site.task.summarize(max_chars=500, refine=True)
print(summary)
```

---

## License

This project is licensed under the **Apache License 2.0**. 

See the [LICENSE](https://github.com/ashtwin2win-Z/WebC/blob/main/LICENSE) file for the full text.

Unless required by applicable law or agreed to in writing, software 
distributed under the License is distributed on an "AS IS" BASIS, 
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. 
See the License for the specific language governing permissions and 
limitations under the License.

© 2026 Ashwin Prasanth
