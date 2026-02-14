from webc import web

site = web["https://en.wikipedia.org/wiki/Python_(programming_language)"]

# List main images
images = site.structure.images
print(f"Found {len(images)} main content images")
print(images[:5])

# Save images safely
saved_files = site.structure.save_images(folder="python_images", delay=1)
print(f"Saved {len(saved_files)} images locally")