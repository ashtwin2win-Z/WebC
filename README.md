<h1 align="center">WebC – Treat Websites as Python Objects</h1>

<p align="center">
<img src="assets/webc.png" alt="WebC Logo" width="280">
</p>

**Version:** 0.1.1
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
* `pandas`

---

## **Core Concepts**

WebC revolves around **four main layers**:

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
site.structure.tables      # List of extracted table data

```

**Image Handling & Filtering**:

* `site.structure.images` returns an `ImageCollection` object.
* **Advanced Extraction**: Automatically parses `srcset`, `data-src`, and `<noscript>` tags to find the highest resolution versions.
* You can **download images** using:

```python
# Save images with a size filter (e.g., only keep files > 10KB to skip icons)
site.structure.save_images(folder="python_images", min_kb=10, batch_size=4)

```

**Table Extraction**:

* Automatically detects and cleans complex tables (e.g., Wikipedia's `wikitable`).
* Removes citation brackets (e.g., `[1]`) and extra whitespace.

```python
# Save all tables to CSV files using caption names
site.structure.save_tables(folder="wiki_data")

```

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

### Safe & Intelligent Downloads

* **Smart Filtering**: Uses file-size checking (`min_kb`) to distinguish between actual content images and UI junk (icons/arrows).
* **Batch Processing**: Downloads occur in groups (e.g., 4 at a time) with cooldown pauses to respect robot policies and prevent IP blocks.
* **Protocol Resolution**: Handles `//` URLs, `/relative/paths`, and resolves them to the full root URL.
* **Sanitized CSVs**: Tables are saved with cleaned text and sanitized filenames derived from table captions.

---

## **Example: Full Usage**

```python
from webc import web

# Load a webpage
site = web["https://en.wikipedia.org/wiki/Python_(programming_language)"]

# --- Structure Layer ---
print("Title:", site.structure.title)

# Save high-res images (ignore tiny icons)
site.structure.save_images(folder="python_images", min_kb=15, batch_size=4)

# Save tables as CSV
site.structure.save_tables(folder="python_data")

# --- Task Layer ---
summary = site.task.summarize(max_chars=500)
print("Summary:", summary)

```

---

## **Technical Notes**

* Uses `requests` with a **browser-like User-Agent** and custom headers to avoid 403 errors.
* Employs **Regex** to strip Wikipedia-style citations and "edit" tags from extracted text.
* Uses `BeautifulSoup` with the `"html.parser"` backend.
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
2. Access **semantic content** (`title`, `links`, `images`, `tables`)
3. Query elements directly via CSS (`site.query[...]`)
4. Perform **tasks** (`summarize`, `download images`)
5. Extend the library with new helpers or tasks

---
