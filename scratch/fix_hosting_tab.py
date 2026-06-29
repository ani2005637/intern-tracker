import os

html_path = r"C:\Users\s.anirudh\Downloads\tracker\index.html"
if not os.path.exists(html_path):
    print("index.html not found!")
    exit(1)

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Locate the double setting in the Admin section of setupPortalForRole
target = "document.getElementById('nav-hosting-details').style.display = 'block';\n                document.getElementById('nav-hosting-details').style.display = 'none';"

if target in content:
    content = content.replace(target, "document.getElementById('nav-hosting-details').style.display = 'block';")
    print("Successfully removed conflicting line!")
else:
    # Try with different whitespace/formatting
    target_loose = "document.getElementById('nav-hosting-details').style.display = 'block';\r\n                document.getElementById('nav-hosting-details').style.display = 'none';"
    if target_loose in content:
        content = content.replace(target_loose, "document.getElementById('nav-hosting-details').style.display = 'block';")
        print("Successfully removed conflicting line (Windows line endings)!")
    else:
        print("Target line not found. Let's do a regex replacement.")
        import re
        content, count = re.subn(
            r"(document\.getElementById\('nav-hosting-details'\)\.style\.display\s*=\s*'block';\s*)document\.getElementById\('nav-hosting-details'\)\.style\.display\s*=\s*'none';",
            r"\1",
            content
        )
        print(f"Regex replaced {count} occurrences.")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("index.html updated and saved.")
