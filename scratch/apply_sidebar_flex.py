import os

html_path = r"C:\Users\s.anirudh\Downloads\tracker\index.html"
if not os.path.exists(html_path):
    print("index.html not found!")
    exit(1)

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Locate the .sidebar class and add box-sizing: border-box;
old_sidebar = """        .sidebar {
            width: 260px;
            background: var(--sidebar-bg);
            border-right: 1px solid var(--card-border);
            padding: 30px 20px;
            display: flex;
            flex-direction: column;
            gap: 30px;
            height: 100vh;
            position: fixed;
            left: 0;
            top: 0;
            z-index: 100;
        }"""

new_sidebar = """        .sidebar {
            width: 260px;
            background: var(--sidebar-bg);
            border-right: 1px solid var(--card-border);
            padding: 30px 20px;
            display: flex;
            flex-direction: column;
            gap: 30px;
            height: 100vh;
            position: fixed;
            left: 0;
            top: 0;
            z-index: 100;
            box-sizing: border-box;
        }"""

if old_sidebar in content:
    content = content.replace(old_sidebar, new_sidebar)
    print("Successfully added box-sizing to .sidebar!")
else:
    # Attempt a more flexible replacement
    import re
    content, count = re.subn(
        r'(\.sidebar\s*\{[^}]*height:\s*100vh;[^}]*)(\})',
        r'\1    box-sizing: border-box;\n        \2',
        content
    )
    print(f"Regex replaced {count} occurrences in .sidebar.")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("index.html updated and saved.")
