import os

html_path = r"C:\Users\s.anirudh\Downloads\tracker\index.html"
if not os.path.exists(html_path):
    print("index.html not found!")
    exit(1)

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Locate the Pending Deliverables card and remove it
old_card = """                    <div class="stat-card" id="stat-pending-deliverables-card" style="position: relative;">
                        <div class="stat-icon" style="color: var(--danger);"><i class="fa-solid fa-triangle-exclamation"></i></div>
                        <div style="flex: 1;">
                            <div class="stat-value" id="stat-pending-deliverables" style="color: var(--danger); cursor: default;">0</div>
                            <div class="stat-label">Pending Deliverables</div>
                            <div id="stat-pending-deliverables-names" style="display:none; position: absolute; left: 0; top: 100%; z-index: 999; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 10px; padding: 12px 16px; min-width: 220px; box-shadow: 0 8px 30px rgba(0,0,0,0.4); font-size: 13px; line-height: 1.8;"></div>
                        </div>
                    </div>"""

if old_card in content:
    content = content.replace(old_card, "")
    print("Successfully removed Pending Deliverables card!")
else:
    # Try with different line endings
    old_card_crlf = old_card.replace("\n", "\r\n")
    if old_card_crlf in content:
        content = content.replace(old_card_crlf, "")
        print("Successfully removed Pending Deliverables card (CRLF)!")
    else:
        print("Could not find the target card block in index.html.")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("index.html updated and saved.")
