# **WebC – Treat Websites as Python Objects**

**Version:** 0.1.0
**Author:** Ashwin Prasanth

`webc` is a Python library that allows you to **treat websites as programmable resources**.
It provides a clean abstraction to access **semantic content**, **query elements**, and **perform tasks** like summarization or image downloading — all via an intuitive object-oriented interface.

---

## **Installation**

Install `webc` locally (editable mode):

```bash
pip install -e .
```

Dependencies:

* `requests`
* `beautifulsoup4`

---

## **Core Concepts**

WebC revolves around **three main layers**:

### 1. **Resource Layer**

Access a website as a `Resource` object:

```python
from webc import web

site = web["https://en.wikipedia.org/wiki/Python_(programming_language)"]
```

* `site` now represents the webpage.
* **Lazy loading**: HTML is fetched only when needed.
* Cached internally for repeated accesses.

### 2. **Structure Layer**

Provides **semantic, high-level content**:

```python
site.structure.title       # Returns <title> of the page
site.structure.links       # List of all hyperlinks
site.structure.images      # ImageCollection object for all main content images
```

**Image Handling**:

* `site.structure.images` returns an `ImageCollection` object.
* You can **download images** using:

```python
# Via ImageCollection
images = site.structure.images
images.save_images(folder="python_images")  

# Or via shortcut
site.structure.save_images(folder="python_images")
```

* Automatically resolves:

  * `//` URLs → `https://`
  * `/relative/paths` → full root URL
* Optional delay (`delay=1`) between downloads prevents server blocks.

---

### 3. **Query Layer**

Provides **low-level DOM access** via CSS selectors:

```python
headings = site.query["h1, h2"]
for h in headings:
    print(h.get_text(strip=True))
```

* Returns a list of BeautifulSoup elements.
* Escape hatch for fine-grained control.

---

### 4. **Task Layer**

Provides **intent-driven actions** on the page:

```python
summary = site.task.summarize(max_chars=500)
print(summary)
```

* Currently supports:

  * `summarize(max_chars=500)`: extracts page text and truncates to `max_chars`.
* Can be extended with other tasks like `search()`, `extract_links()`, or `compare()`.

---

## **Advanced Features**

### Lazy Loading & Caching

* HTML is fetched **only once** per `Resource`.
* Parsing into BeautifulSoup is cached for repeated queries.

### Safe Image Downloads

* Only main content images are considered by default (`#content img` on Wikipedia).
* Handles relative URLs and external URLs correctly.
* Optional delay prevents HTTP 403 errors.
* Overwrite control: avoid overwriting existing files unless requested.

---

## **Example: Full Usage**

```python
from webc import web

# Load a webpage
site = web["https://en.wikipedia.org/wiki/Python_(programming_language)"]

# --- Structure Layer ---
print("Title:", site.structure.title)
print("First 5 links:", site.structure.links[:5])

# Image URLs
images = site.structure.images
print("First 5 images:", images[:5])

# Save all images locally
saved_files = site.structure.save_images(folder="python_images", delay=1)
print(f"Saved {len(saved_files)} images.")

# --- Query Layer ---
headings = site.query["h1, h2"]
for h in headings:
    print("-", h.get_text(strip=True))

# --- Task Layer ---
summary = site.task.summarize(max_chars=500)
print("Summary:", summary)
```

---

## **Technical Notes**

* Uses `requests` with a **browser-like User-Agent** to avoid 403 errors.
* Uses `BeautifulSoup` with the `"html.parser"` backend.
* Designed for **static content**; dynamic content rendered via JavaScript may require additional tools like Selenium or Playwright.
* Extensible: you can add more semantic helpers or tasks easily.

---

## **Directory Structure**

```
webc/
│
├── webc/
│   ├── __init__.py        # Entry point: from webc import web
│   ├── web.py             # Core classes: Web, Resource, StructuredView, QueryView, TaskView, ImageCollection
│
└── pyproject.toml         # Project metadata and dependencies
```

---

## **Summary**

WebC makes it easy to:

1. Treat a website as a Python object (`web[...]`)
2. Access **semantic content** (`title`, `links`, `images`)
3. Query elements directly via CSS (`site.query[...]`)
4. Perform **tasks** (`summarize`, `download images`)
5. Extend the library with new helpers or tasks

It’s ideal for **scraping, analyzing, or interacting with static websites** in a structured, Pythonic way.

---
