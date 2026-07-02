import os

html_path = r"C:\Users\s.anirudh\Downloads\tracker\index.html"
if not os.path.exists(html_path):
    print("index.html not found!")
    exit(1)

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Locate the updateTaskStatus function and update body definition
old_status_func = """        async function updateTaskStatus(taskId, status) {
            try {
                const res = await apiFetch(`/tasks/${taskId}`, {
                    method: 'PUT',
                    body: {
                        status: status,
                        percent_done: status === 'Completed' ? 100 : undefined
                    }
                });"""

new_status_func = """        async function updateTaskStatus(taskId, status) {
            try {
                let percent = undefined;
                if (status === 'Not Started') {
                    percent = 0;
                } else if (status === 'In Progress') {
                    percent = 50;
                } else if (status === 'Completed') {
                    percent = 100;
                }

                const res = await apiFetch(`/tasks/${taskId}`, {
                    method: 'PUT',
                    body: {
                        status: status,
                        percent_done: percent
                    }
                });"""

if old_status_func in content:
    content = content.replace(old_status_func, new_status_func)
    print("Successfully updated updateTaskStatus function!")
else:
    print("Could not find the target updateTaskStatus block in index.html.")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("index.html updated and saved.")
