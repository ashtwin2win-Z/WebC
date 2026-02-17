'''from webc import web

site = web["https://en.wikipedia.org/wiki/Porsche"]

# Extract tables
print(f"Found {len(site.structure.tables)} tables")

# Save tables as Excel
saved = site.structure.save_tables(folder="my_tables")
print("Saved tables:", saved)'''

'''site = web["https://en.wikipedia.org/wiki/Porsche"]
tables = site.structure.tables
print(f"Total tables found by BeautifulSoup: {len(site.soup.find_all('table'))}")
print(f"Tables parsed by pandas: {len(tables)}")'''

from webc import web
site = web["https://en.wikipedia.org/wiki/Porsche"]

# These two lines do the actual work of writing to your folders
site.structure.save_images("my_porsche_pics")
site.structure.save_tables("porsche_data")