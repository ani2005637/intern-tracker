import os

html_path = r"C:\Users\s.anirudh\Downloads\tracker\index.html"
if not os.path.exists(html_path):
    print("index.html not found!")
    exit(1)

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update the JS calls from appendChild to prepend
content = content.replace("activityLogsSection.appendChild(assignPanel);", "activityLogsSection.prepend(assignPanel);")

# 2. Move the HTML block to the top of the section
# Let's extract the task-assign-panel HTML block
panel_start_marker = '<!-- Add Task Panel (Moved here) -->'
panel_end_marker = '</form>\n                </div>'

start_idx = content.find(panel_start_marker)
if start_idx != -1:
    end_idx = content.find(panel_end_marker, start_idx)
    if end_idx != -1:
        full_end_idx = end_idx + len(panel_end_marker)
        panel_html = content[start_idx:full_end_idx]
        
        # Remove the panel from its current bottom position
        content = content[:start_idx] + content[full_end_idx:]
        
        # Find the start of the activity-logs section to prepend the panel
        section_start_marker = '<section id="activity-logs" class="tab-content">'
        section_idx = content.find(section_start_marker)
        if section_idx != -1:
            insert_idx = section_idx + len(section_start_marker)
            # Insert the panel HTML right at the beginning of the section
            content = content[:insert_idx] + "\n                " + panel_html + "\n" + content[insert_idx:]
            print("Successfully moved HTML panel to the top of the section!")
        else:
            print("Could not find the activity-logs section start.")
    else:
        print("Could not find the end of the task-assign-panel HTML.")
else:
    print("Could not find the start of the task-assign-panel HTML.")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("index.html updated and saved.")
