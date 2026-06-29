import os

html_path = r"C:\Users\s.anirudh\Downloads\tracker\index.html"
if not os.path.exists(html_path):
    print("index.html not found!")
    exit(1)

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the li tag to include data-tab
old_li = '<li class="nav-item" id="nav-hosting-details" style="display: none;">'
new_li = '<li class="nav-item" data-tab="hosting-details" id="nav-hosting-details" style="display: none;">'

if old_li in content:
    content = content.replace(old_li, new_li)
    print("Successfully added data-tab attribute!")
else:
    print("Could not find the target li tag. Trying regex...")
    import re
    content, count = re.subn(
        r'<li class="nav-item" id="nav-hosting-details"',
        r'<li class="nav-item" data-tab="hosting-details" id="nav-hosting-details"',
        content
    )
    print(f"Regex replaced {count} occurrences.")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("index.html updated and saved.")
