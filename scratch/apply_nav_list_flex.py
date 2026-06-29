import os

html_path = r"C:\Users\s.anirudh\Downloads\tracker\index.html"
if not os.path.exists(html_path):
    print("index.html not found!")
    exit(1)

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Locate .nav-list class and add flex-grow: 1; overflow-y: auto; and scrollbar hiding
old_nav_list = """        /* Sidebar Navigation */
        .nav-list {
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }"""

new_nav_list = """        /* Sidebar Navigation */
        .nav-list {
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 8px;
            flex-grow: 1;
            overflow-y: auto;
            -ms-overflow-style: none;  /* IE and Edge */
            scrollbar-width: none;  /* Firefox */
        }
        .nav-list::-webkit-scrollbar {
            display: none; /* Chrome, Safari and Opera */
        }"""

if old_nav_list in content:
    content = content.replace(old_nav_list, new_nav_list)
    print("Successfully updated .nav-list CSS!")
else:
    import re
    content, count = re.subn(
        r'(\.nav-list\s*\{[^}]*)(\})',
        r'\1    flex-grow: 1;\n            overflow-y: auto;\n            -ms-overflow-style: none;\n            scrollbar-width: none;\n        }\n        .nav-list::-webkit-scrollbar {\n            display: none;\n        \2',
        content
    )
    print(f"Regex replaced {count} occurrences in .nav-list.")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("index.html updated and saved.")
