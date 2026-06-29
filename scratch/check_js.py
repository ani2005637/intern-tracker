import re
import subprocess

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Extract the script content
scripts = re.findall(r'<script>(.*?)</script>', html, re.DOTALL)
if not scripts:
    print("No script tag found!")
    exit(1)

script_content = scripts[0]
with open('temp_script.js', 'w', encoding='utf-8') as f:
    f.write(script_content)

print("Extracted JS to temp_script.js. Testing with node...")
try:
    res = subprocess.run(['node', '--check', 'temp_script.js'], capture_output=True, text=True)
    if res.returncode == 0:
        print("JS Syntax: OK")
    else:
        print("JS Syntax Error:")
        print(res.stderr)
except FileNotFoundError:
    print("Node.js is not installed, cannot run syntax check. Trying basic brace matching...")
    # Basic brace check
    open_braces = 0
    for i, char in enumerate(script_content):
        if char == '{':
            open_braces += 1
        elif char == '}':
            open_braces -= 1
            if open_braces < 0:
                print(f"Mismatched closing brace at character {i}!")
                break
    print(f"Brace matching: {'OK' if open_braces == 0 else f'Mismatched! Count: {open_braces}'}")
