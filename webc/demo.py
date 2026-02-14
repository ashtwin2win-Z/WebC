url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
from webc import web

# Step 1: Load the site as a Resource
site = web[url]

# Step 2: Access the structured layer
print("=== STRUCTURE ===")
print("Title:", site.structure.title)
print("First 5 links:", site.structure.links[:5])

# Step 3: Access the query layer
print("\n=== QUERY ===")
headings = site.query["h1, h2"]
print("Headings found:")
for h in headings:
    print("-", h.get_text(strip=True))

# Step 4: Access the task layer
print("\n=== TASK ===")
summary = site.task.summarize(max_chars=500)
print("Summary (500 chars):")
print(summary)