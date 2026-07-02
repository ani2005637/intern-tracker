import os

html_path = r"C:\Users\s.anirudh\Downloads\tracker\index.html"
if not os.path.exists(html_path):
    print("index.html not found!")
    exit(1)

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Locate the filtering section in renderDashboard
old_filter_block = """            // If Admin/Manager is logged in, they can filter the stats by a selected user
            if (role === 'Admin' || role === 'Manager') {
                const userVal = document.getElementById('dash-user-filter').value;
                if (userVal !== 'ALL') {
                    filteredLogs = filteredLogs.filter(l => l.intern_name && l.intern_name.toLowerCase().trim() === userVal.toLowerCase().trim());
                    filteredTasks = filteredTasks.filter(t => t.intern_name && t.intern_name.toLowerCase().trim() === userVal.toLowerCase().trim());
                    filteredSkills = filteredSkills.filter(s => s.intern_name && s.intern_name.toLowerCase().trim() === userVal.toLowerCase().trim());
                }
            }"""

new_filter_block = """            // If Admin/Manager is logged in, they can filter the stats by a selected user
            if (role === 'Admin' || role === 'Manager') {
                const userVal = document.getElementById('dash-user-filter').value;
                if (userVal !== 'ALL') {
                    filteredLogs = filteredLogs.filter(l => l.intern_name && l.intern_name.toLowerCase().trim() === userVal.toLowerCase().trim());
                    filteredTasks = filteredTasks.filter(t => t.intern_name && t.intern_name.toLowerCase().trim() === userVal.toLowerCase().trim());
                    filteredSkills = filteredSkills.filter(s => s.intern_name && s.intern_name.toLowerCase().trim() === userVal.toLowerCase().trim());
                }
            } else {
                // Employees and Interns should only see their own personal statistics on their dashboard
                const myUname = currentUser.username.toLowerCase().trim();
                filteredLogs = filteredLogs.filter(l => l.intern_name && l.intern_name.toLowerCase().trim() === myUname);
                filteredTasks = filteredTasks.filter(t => t.intern_name && t.intern_name.toLowerCase().trim() === myUname);
                filteredSkills = filteredSkills.filter(s => s.intern_name && s.intern_name.toLowerCase().trim() === myUname);
            }"""

if old_filter_block in content:
    content = content.replace(old_filter_block, new_filter_block)
    print("Successfully updated dashboard filtering logic!")
else:
    print("Could not find the target filter block in index.html.")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("index.html updated and saved.")
