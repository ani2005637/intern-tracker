import os

html_path = r"C:\Users\s.anirudh\Downloads\tracker\index.html"
if not os.path.exists(html_path):
    print("index.html not found!")
    exit(1)

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Locate the headers filtering in renderHostingTable
old_headers_line = "const headers = Object.keys(rows[0]).filter(k => k !== '_row_idx');"
new_headers_line = "const headers = Object.keys(rows[0]).filter(k => k !== '_row_idx' && k !== 'id');"

if old_headers_line in content:
    content = content.replace(old_headers_line, new_headers_line)
    print("Successfully hid the ID column!")
else:
    # Try with double quotes or spacing variations
    print("Trying alternative search patterns...")
    import re
    content, count = re.subn(
        r"const headers\s*=\s*Object\.keys\(rows\[0\]\)\.filter\(k\s*=>\s*k\s*!==\s*['_\"]_row_idx['_\"]\);",
        "const headers = Object.keys(rows[0]).filter(k => k !== '_row_idx' && k !== 'id');",
        content
    )
    print(f"Regex replaced {count} occurrences.")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("index.html updated and saved.")
