import os

app_path = r"C:\Users\s.anirudh\Downloads\tracker\app.py"
html_path = r"C:\Users\s.anirudh\Downloads\tracker\index.html"

# 1. Add route to app.py
with open(app_path, 'r', encoding='utf-8') as f:
    app_content = f.read()

verify_route = """@app.route('/admin/onboarding/checklist/<username>', methods=['GET'])
def get_user_onboarding_checklist(username):
    \"\"\"
    Admin fetches the onboarding checklist of a specific user.
    \"\"\"
    user = get_logged_in_user()
    if not user or user['role'] != 'Admin':
        return jsonify({"error": "Unauthorized"}), 401

    try:
        tasks = list(db.onboarding_tasks.find({"username": username}).sort("assigned_at", 1))
        serialized = []
        for t in tasks:
            serialized.append({
                "id": str(t['_id']),
                "task_name": t.get("task_name", ""),
                "description": t.get("description", ""),
                "status": t.get("status", "Pending"),
                "submission_link": t.get("submission_link", ""),
                "notes": t.get("notes", ""),
                "assigned_at": t.get("assigned_at").isoformat() if t.get("assigned_at") else "",
                "completed_at": t.get("completed_at").isoformat() if t.get("completed_at") else ""
            })
        return jsonify(serialized)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch checklist: {str(e)}"}), 500


"""

# Insert before if __name__ == '__main__':
main_idx = app_content.find("if __name__ == '__main__':")
if main_idx != -1:
    app_content = app_content[:main_idx] + verify_route + app_content[main_idx:]
    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(app_content)
    print("Added /admin/onboarding/checklist/<username> route to app.py!")


# 2. Update JS in index.html
with open(html_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

old_verify_modal_func = """        let verifyChecklistTasks = [];
        async function openOnboardingVerifyModal(username, fullName) {
            document.getElementById('onboarding-verify-name').innerText = fullName;
            const container = document.getElementById('onboarding-verify-list');
            container.innerHTML = `<div style="text-align:center; padding:20px;"><i class="fa-solid fa-spinner fa-spin"></i> Loading...</div>`;
            document.getElementById('onboarding-verify-modal').style.display = 'flex';

            try {
                // We'll hit the user's checklist using a parameterized endpoint or by filtering.
                // Since user endpoints fetch active user, we can build a simple endpoint for admin,
                // or just fetch by query. Wait, let's create a database query for admin checklist check
                // or just pass parameter. Oh! In app.py we can use /onboarding/checklist/<username>!
                // Wait, did we implement that? No, but wait!
                // Admin can query /onboarding/my-checklist of the target user if we build a route,
                // or let's create it in app.py or modify our JS to fetch by query.
                // Wait! Let's check how we can fetch tasks.
                // In app.py: we can hit the checklist.
                // Actually, let's create a route for Admin to fetch a user's onboarding tasks!
                // Let's modify app.py to add `GET /admin/onboarding/checklist/<username>`.
                // Let's add that to app.py!
            } catch (err) {}
        }"""

new_verify_modal_func = """        let verifyChecklistTasks = [];
        async function openOnboardingVerifyModal(username, fullName) {
            document.getElementById('onboarding-verify-name').innerText = fullName;
            const container = document.getElementById('onboarding-verify-list');
            container.innerHTML = `<div style="text-align:center; padding:20px;"><i class="fa-solid fa-spinner fa-spin"></i> Loading...</div>`;
            document.getElementById('onboarding-verify-modal').style.display = 'flex';

            try {
                const res = await apiFetch(`/admin/onboarding/checklist/${username}`);
                if (res.ok) {
                    const tasks = await res.json();
                    container.innerHTML = '';
                    
                    if (tasks.length === 0) {
                        container.innerHTML = `<div style="text-align:center; padding:20px; color:var(--text-muted);">No onboarding tasks assigned to this user.</div>`;
                        return;
                    }
                    
                    tasks.forEach(t => {
                        const div = document.createElement('div');
                        div.style.background = 'rgba(255,255,255,0.02)';
                        div.style.border = '1px solid var(--border-color)';
                        div.style.borderRadius = '8px';
                        div.style.padding = '12px';
                        div.style.marginBottom = '10px';
                        
                        let submissionHtml = '';
                        if (t.submission_link) {
                            submissionHtml = `
                                <div style="font-size:12px; margin-top:8px; display:flex; align-items:center; gap:6px;">
                                    <i class="fa-solid fa-link" style="color:var(--primary);"></i>
                                    <a href="${t.submission_link}" target="_blank" style="color:var(--primary); font-weight:600; text-decoration:none;">View Submission Document</a>
                                </div>
                            `;
                        }
                        
                        let notesHtml = '';
                        if (t.notes) {
                            notesHtml = `<div style="font-size:12px; color:var(--text-muted); background:rgba(255,255,255,0.02); padding:8px; border-radius:6px; margin-top:6px;"><strong>Notes:</strong> ${escapeHTML(t.notes)}</div>`;
                        }

                        div.innerHTML = `
                            <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:10px;">
                                <div style="flex:1;">
                                    <strong style="color:var(--text-color); font-size:13px;">${escapeHTML(t.task_name)}</strong>
                                    <div style="font-size:11px; color:var(--text-muted); margin-top:4px;">${escapeHTML(t.description)}</div>
                                </div>
                                <span class="badge ${t.status === 'Completed' ? 'badge-success' : 'badge-warning'}" style="font-size:10px;">${t.status}</span>
                            </div>
                            ${submissionHtml}
                            ${notesHtml}
                        `;
                        container.appendChild(div);
                    });
                } else {
                    container.innerHTML = `<div style="text-align:center; padding:20px; color:var(--danger);">Failed to load checklist.</div>`;
                }
            } catch (err) {
                container.innerHTML = `<div style="text-align:center; padding:20px; color:var(--danger);">Failed to load checklist.</div>`;
            }
        }"""

if old_verify_modal_func in html_content:
    html_content = html_content.replace(old_verify_modal_func, new_verify_modal_func)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("Successfully updated openOnboardingVerifyModal in index.html!")
else:
    print("Could not find old_verify_modal_func in index.html.")
