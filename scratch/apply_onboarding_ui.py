import os

html_path = r"C:\Users\s.anirudh\Downloads\tracker\index.html"
if not os.path.exists(html_path):
    print("index.html not found!")
    exit(1)

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add Sidebar Navigation Tabs
nav_items_html = """                <li class="nav-item" data-tab="onboarding-admin" id="nav-onboarding-admin" style="display: none;">
                    <button onclick="switchTab('onboarding-admin')">
                        <i class="fa-solid fa-user-plus"></i> Onboarding Admin
                    </button>
                </li>
                <li class="nav-item" data-tab="onboarding-checklist" id="nav-onboarding-checklist" style="display: none;">
                    <button onclick="switchTab('onboarding-checklist')">
                        <i class="fa-solid fa-list-check"></i> Onboarding Checklist
                    </button>
                </li>"""

nav_end_idx = content.find('</ul>', content.find('class="sidebar"'))
if nav_end_idx != -1:
    content = content[:nav_end_idx] + nav_items_html + "\n            " + content[nav_end_idx:]

# 2. Add visibility toggles in setupPortalForRole()
# For Intern:
intern_block = "document.getElementById('nav-hosting-details').style.display = 'none';"
# Let's replace the first occurrence (usually Intern/Employee block)
intern_idx = content.find(intern_block)
if intern_idx != -1:
    content = content[:intern_idx + len(intern_block)] + "\n                document.getElementById('nav-onboarding-admin').style.display = 'none';" + content[intern_idx + len(intern_block):]

# For Manager:
# Let's find manager block:
manager_section = "document.getElementById('nav-hosting-details').style.display = 'none';"
manager_idx = content.find(manager_section, intern_idx + len(intern_block) + 100)
if manager_idx != -1:
    content = content[:manager_idx + len(manager_section)] + "\n                document.getElementById('nav-onboarding-admin').style.display = 'none';" + content[manager_idx + len(manager_section):]

# For Admin:
# Let's find where Admin block sets nav-hosting-details display:
admin_block = "document.getElementById('nav-hosting-details').style.display = 'block';"
admin_idx = content.find(admin_block)
if admin_idx != -1:
    content = content[:admin_idx + len(admin_block)] + "\n                document.getElementById('nav-onboarding-admin').style.display = 'block';" + content[admin_idx + len(admin_block):]

# 3. Add the HTML sections
# We'll insert it right after the hosting-details section end
hosting_end_idx = content.find('</section>', content.find('id="hosting-details"'))
onboarding_html = """

            <!-- ONBOARDING ADMIN MODULE (Admin Only) -->
            <section id="onboarding-admin" class="tab-content">
                <div class="panel" style="margin-bottom: 24px; padding: 20px;">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <i class="fa-solid fa-user-plus" style="color: var(--primary); font-size: 24px;"></i>
                        <h2 style="margin: 0; font-size: 18px; font-weight: 600; color: var(--text-color);">Employee Onboarding Management</h2>
                    </div>
                </div>

                <div class="grid-3" style="grid-template-columns: 1.2fr 1.8fr; gap: 24px; margin-bottom: 30px;">
                    <!-- Onboarding Templates Panel -->
                    <div class="panel" style="padding: 24px;">
                        <div class="panel-title" style="margin-bottom: 20px;">
                            <i class="fa-solid fa-list-check"></i>
                            <span>Default Checklist Templates</span>
                        </div>
                        <form id="onboardingTemplateForm" onsubmit="handleCreateTemplate(event)" style="margin-bottom: 20px; border-bottom: 1px solid var(--border-color); padding-bottom: 20px;">
                            <div class="form-group" style="margin-bottom: 12px;">
                                <label for="tpl_task_name">Task Title</label>
                                <input type="text" id="tpl_task_name" placeholder="e.g. Submit ID & Address Proof" required>
                            </div>
                            <div class="form-group" style="margin-bottom: 12px;">
                                <label for="tpl_description">Description / Instructions</label>
                                <textarea id="tpl_description" placeholder="Specify document upload requirements or setup instructions..." style="width:100%; min-height:80px; padding:8px 12px; border-radius:8px;" required></textarea>
                            </div>
                            <button type="submit" class="btn-submit" style="width: 100%; padding: 8px 16px;"><i class="fa-solid fa-plus"></i> Add Template Task</button>
                        </form>
                        <div id="onboarding-templates-list" style="display: flex; flex-direction: column; gap: 12px; max-height: 400px; overflow-y: auto;">
                            <!-- Populated dynamically -->
                        </div>
                    </div>

                    <!-- Onboarding Employee Progress Panel -->
                    <div class="panel" style="padding: 24px;">
                        <div class="panel-title" style="margin-bottom: 20px;">
                            <i class="fa-solid fa-chart-line"></i>
                            <span>Employee Onboarding Progress</span>
                        </div>
                        <div style="overflow-x: auto;">
                            <table class="data-table" style="width: 100%;">
                                <thead>
                                    <tr>
                                        <th>Employee Name</th>
                                        <th>Role / Title</th>
                                        <th style="text-align: center; width: 120px;">Progress</th>
                                        <th style="text-align: center; width: 180px;">Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="onboarding-progress-body">
                                    <!-- Populated dynamically -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Employee Onboarding Detail Verification Modal -->
            <div id="onboarding-verify-modal" class="modal-overlay" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 2000; align-items: center; justify-content: center; backdrop-filter: blur(5px); -webkit-backdrop-filter: blur(5px);">
                <div class="modal-content" style="width: 100%; max-width: 600px; background: var(--bg-card); border: 1px solid var(--card-border); border-radius: 16px; padding: 24px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding-bottom: 15px; margin-bottom: 20px;">
                        <h3 style="margin: 0; font-size: 18px; font-weight: 600; color: var(--text-color);">Onboarding Checklist: <span id="onboarding-verify-name"></span></h3>
                        <button onclick="closeOnboardingVerifyModal()" style="background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 18px;"><i class="fa-solid fa-xmark"></i></button>
                    </div>
                    <div id="onboarding-verify-list" style="display: flex; flex-direction: column; gap: 15px; max-height: 450px; overflow-y: auto; padding-right: 5px;">
                        <!-- Populated dynamically -->
                    </div>
                </div>
            </div>

            <!-- PERSONAL ONBOARDING CHECKLIST MODULE -->
            <section id="onboarding-checklist" class="tab-content">
                <div class="panel" style="margin-bottom: 24px; padding: 20px;">
                    <div style="display: flex; flex-direction: column; gap: 12px;">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <i class="fa-solid fa-list-check" style="color: var(--primary); font-size: 24px;"></i>
                            <h2 style="margin: 0; font-size: 18px; font-weight: 600; color: var(--text-color);">Your Onboarding Checklist</h2>
                        </div>
                        <div style="margin-top: 10px;">
                            <div style="display: flex; justify-content: space-between; font-size: 14px; font-weight: 600; color: var(--text-color); margin-bottom: 8px;">
                                <span>Checklist Completion</span>
                                <span id="onboarding-checklist-percentage">0%</span>
                            </div>
                            <div style="width: 100%; height: 10px; background: rgba(255,255,255,0.05); border-radius: 5px; overflow: hidden;">
                                <div id="onboarding-checklist-progress-bar" style="width: 0%; height: 100%; background: linear-gradient(90deg, var(--primary), var(--secondary)); transition: width 0.4s ease;"></div>
                            </div>
                        </div>
                    </div>
                </div>

                <div id="onboarding-checklist-cards" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px; margin-bottom: 30px;">
                    <!-- Populated dynamically -->
                </div>
            </section>

            <!-- Complete Onboarding Task Modal -->
            <div id="onboarding-complete-modal" class="modal-overlay" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 2000; align-items: center; justify-content: center; backdrop-filter: blur(5px); -webkit-backdrop-filter: blur(5px);">
                <div class="modal-content" style="width: 100%; max-width: 500px; background: var(--bg-card); border: 1px solid var(--card-border); border-radius: 16px; padding: 24px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding-bottom: 15px; margin-bottom: 20px;">
                        <h3 style="margin: 0; font-size: 16px; font-weight: 600; color: var(--text-color);">Submit Task: <span id="onboarding-complete-task-title"></span></h3>
                        <button onclick="closeOnboardingCompleteModal()" style="background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 18px;"><i class="fa-solid fa-xmark"></i></button>
                    </div>
                    <form id="onboardingCompleteForm" onsubmit="handleOnboardingSubmitTask(event)">
                        <input type="hidden" id="onboarding-complete-task-id">
                        <div class="form-group" style="margin-bottom: 15px;">
                            <label for="ob_submission_link">Document / Submission Link (Optional)</label>
                            <input type="url" id="ob_submission_link" placeholder="e.g. Google Drive folder or GitHub URL">
                        </div>
                        <div class="form-group" style="margin-bottom: 15px;">
                            <label for="ob_notes">Submission Notes (Optional)</label>
                            <textarea id="ob_notes" placeholder="Any comments or verification notes for the administrator..." style="width:100%; min-height:80px; padding:8px 12px; border-radius:8px;"></textarea>
                        </div>
                        <div style="display: flex; justify-content: flex-end; gap: 12px; border-top: 1px solid var(--border-color); padding-top: 15px; margin-top: 20px;">
                            <button type="button" onclick="closeOnboardingCompleteModal()" class="btn-submit" style="background: rgba(255,255,255,0.05); color: var(--text-color); border: 1px solid var(--border-color);">Cancel</button>
                            <button type="submit" class="btn-submit" style="background: var(--success); color: white;"><i class="fa-solid fa-circle-check"></i> Complete Task</button>
                        </div>
                    </form>
                </div>
            </div>"""

if hosting_end_idx != -1:
    end_tag_idx = hosting_end_idx + len('</section>')
    content = content[:end_tag_idx] + onboarding_html + content[end_tag_idx:]

# 4. Add Javascript logic before </script>
script_end_idx = content.rfind('</script>')
onboarding_js = """
        /* ----------------- EMPLOYEE ONBOARDING LOGIC ----------------- */
        let onboardingTemplates = [];
        let onboardingProgress = [];
        let myOnboardingChecklist = [];

        async function checkOnboardingVisibility() {
            try {
                const res = await apiFetch('/onboarding/my-checklist');
                if (res.ok) {
                    myOnboardingChecklist = await res.json();
                    const navChecklist = document.getElementById('nav-onboarding-checklist');
                    if (navChecklist) {
                        navChecklist.style.display = myOnboardingChecklist.length > 0 ? 'block' : 'none';
                    }
                }
            } catch (err) {
                console.error("Failed to check onboarding checklist visibility:", err);
            }
        }

        async function loadOnboardingAdmin() {
            try {
                // Fetch Templates
                const tplRes = await apiFetch('/admin/onboarding/templates');
                if (tplRes.ok) {
                    onboardingTemplates = await tplRes.json();
                    renderOnboardingTemplates();
                }

                // Fetch Employee Progress
                const progRes = await apiFetch('/admin/onboarding/progress');
                if (progRes.ok) {
                    onboardingProgress = await progRes.json();
                    renderOnboardingProgress();
                }
            } catch (err) {
                showToast("Failed to load onboarding admin data", "error");
            }
        }

        function renderOnboardingTemplates() {
            const container = document.getElementById('onboarding-templates-list');
            container.innerHTML = '';
            
            if (onboardingTemplates.length === 0) {
                container.innerHTML = `<div style="text-align:center; color:var(--text-muted); padding:20px; font-size:13px;">No default templates created yet.</div>`;
                return;
            }

            onboardingTemplates.forEach(t => {
                const card = document.createElement('div');
                card.style.background = 'rgba(255,255,255,0.02)';
                card.style.border = '1px solid var(--border-color)';
                card.style.borderRadius = '8px';
                card.style.padding = '12px';
                card.style.display = 'flex';
                card.style.justifyContent = 'space-between';
                card.style.alignItems = 'flex-start';
                card.style.gap = '10px';

                card.innerHTML = `
                    <div style="flex:1;">
                        <div style="font-weight:600; font-size:13px; color:var(--text-color);">${escapeHTML(t.task_name)}</div>
                        <div style="font-size:11px; color:var(--text-muted); margin-top:4px;">${escapeHTML(t.description || 'No description')}</div>
                    </div>
                    <button onclick="deleteOnboardingTemplate('${t.id}')" style="background:none; border:none; color:var(--danger); cursor:pointer; font-size:14px; padding:4px;"><i class="fa-solid fa-trash-can"></i></button>
                `;
                container.appendChild(card);
            });
        }

        function renderOnboardingProgress() {
            const tbody = document.getElementById('onboarding-progress-body');
            tbody.innerHTML = '';

            if (onboardingProgress.length === 0) {
                tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:var(--text-muted); padding:20px;">No employees found.</td></tr>`;
                return;
            }

            onboardingProgress.forEach(p => {
                const tr = document.createElement('tr');
                const hasAssigned = p.total_tasks > 0;
                
                let progressHtml = '';
                if (hasAssigned) {
                    const pct = p.total_tasks > 0 ? Math.round((p.completed_tasks / p.total_tasks) * 100) : 0;
                    progressHtml = `
                        <div style="display:flex; flex-direction:column; gap:4px; align-items:center;">
                            <div style="font-size:12px; font-weight:600; color:var(--text-color);">${pct}%</div>
                            <div style="width:80px; height:6px; background:rgba(255,255,255,0.05); border-radius:3px; overflow:hidden;">
                                <div style="width:${pct}%; height:100%; background:var(--primary);"></div>
                            </div>
                            <div style="font-size:10px; color:var(--text-muted);">${p.completed_tasks}/${p.total_tasks} completed</div>
                        </div>
                    `;
                } else {
                    progressHtml = `<span style="font-size:11px; color:var(--text-muted);">Not Assigned</span>`;
                }

                let actionsHtml = '';
                if (hasAssigned) {
                    actionsHtml = `
                        <div style="display:flex; gap:6px; justify-content:center;">
                            <button onclick="openOnboardingVerifyModal('${p.username}', '${escapeHTML(p.full_name)}')" class="btn-action edit" style="background:rgba(99,102,241,0.1); color:var(--primary); padding:6px 10px; border-radius:6px; font-size:11px; font-weight:600; border:none; cursor:pointer;"><i class="fa-solid fa-eye"></i> View Checklist</button>
                            <button onclick="assignOnboardingChecklist('${p.username}')" class="btn-action delete" style="background:rgba(255,255,255,0.05); color:var(--text-color); padding:6px 10px; border-radius:6px; font-size:11px; font-weight:600; border:1px solid var(--border-color); cursor:pointer;"><i class="fa-solid fa-arrows-rotate"></i> Re-assign</button>
                        </div>
                    `;
                } else {
                    actionsHtml = `
                        <button onclick="assignOnboardingChecklist('${p.username}')" class="btn-submit" style="padding:6px 12px; font-size:11px; font-weight:600; display:block; margin:0 auto;"><i class="fa-solid fa-circle-plus"></i> Assign Checklist</button>
                    `;
                }

                tr.innerHTML = `
                    <td style="font-weight:600;">${escapeHTML(p.full_name)} <span style="font-size:10px; color:var(--text-muted); font-weight:normal; display:block;">@${p.username}</span></td>
                    <td><span class="badge ${p.role === 'Employee' ? 'badge-primary' : 'badge-success'}">${p.role}</span> <span style="font-size:11px; color:var(--text-muted); display:block; margin-top:2px;">${escapeHTML(p.title || 'Staff')}</span></td>
                    <td style="text-align:center;">${progressHtml}</td>
                    <td>${actionsHtml}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        async function handleCreateTemplate(e) {
            e.preventDefault();
            const nameEl = document.getElementById('tpl_task_name');
            const descEl = document.getElementById('tpl_description');
            
            try {
                const res = await apiFetch('/admin/onboarding/templates', {
                    method: 'POST',
                    body: {
                        task_name: nameEl.value,
                        description: descEl.value,
                        required: true
                    }
                });
                if (res.ok) {
                    showToast("Onboarding template task added successfully!", "success");
                    nameEl.value = '';
                    descEl.value = '';
                    loadOnboardingAdmin();
                } else {
                    const data = await res.json();
                    showToast(data.error || "Failed to add template", "error");
                }
            } catch (err) {
                showToast("Failed to add template", "error");
            }
        }

        async function deleteOnboardingTemplate(id) {
            if (!confirm("Are you sure you want to delete this template task?")) return;
            try {
                const res = await apiFetch(`/admin/onboarding/templates/${id}`, {
                    method: 'DELETE'
                });
                if (res.ok) {
                    showToast("Template task deleted successfully!", "success");
                    loadOnboardingAdmin();
                }
            } catch (err) {
                showToast("Failed to delete template task", "error");
            }
        }

        async function assignOnboardingChecklist(username) {
            if (!confirm(`Are you sure you want to assign/reset the onboarding checklist for @${username}? This will create new task instances for them.`)) return;
            try {
                const res = await apiFetch('/admin/onboarding/assign', {
                    method: 'POST',
                    body: { username }
                });
                if (res.ok) {
                    showToast("Checklist assigned successfully!", "success");
                    loadOnboardingAdmin();
                } else {
                    const data = await res.json();
                    showToast(data.error || "Failed to assign checklist", "error");
                }
            } catch (err) {
                showToast("Failed to assign checklist", "error");
            }
        }

        let verifyChecklistTasks = [];
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
        }
        
        function closeOnboardingVerifyModal() {
            document.getElementById('onboarding-verify-modal').style.display = 'none';
        }

        /* PERSONAL CHECKLIST LOGIC */
        async function loadOnboardingChecklist() {
            try {
                const res = await apiFetch('/onboarding/my-checklist');
                if (res.ok) {
                    myOnboardingChecklist = await res.json();
                    renderOnboardingChecklist();
                }
            } catch (err) {
                console.error("Failed to load onboarding checklist:", err);
            }
        }

        function renderOnboardingChecklist() {
            const container = document.getElementById('onboarding-checklist-cards');
            const pctEl = document.getElementById('onboarding-checklist-percentage');
            const barEl = document.getElementById('onboarding-checklist-progress-bar');
            
            container.innerHTML = '';

            if (myOnboardingChecklist.length === 0) {
                container.innerHTML = `<div style="grid-column: span 3; text-align:center; padding:40px; color:var(--text-muted);">No onboarding tasks assigned to you.</div>`;
                pctEl.innerText = '0%';
                barEl.style.width = '0%';
                return;
            }

            const total = myOnboardingChecklist.length;
            const completed = myOnboardingChecklist.filter(t => t.status === 'Completed').length;
            const pct = Math.round((completed / total) * 100);
            
            pctEl.innerText = `${pct}% (${completed} of ${total} completed)`;
            barEl.style.width = `${pct}%`;

            myOnboardingChecklist.forEach(t => {
                const card = document.createElement('div');
                card.className = 'panel';
                card.style.padding = '20px';
                card.style.display = 'flex';
                card.style.flexDirection = 'column';
                card.style.justifyContent = 'space-between';
                card.style.gap = '15px';
                card.style.borderLeft = t.status === 'Completed' ? '4px solid var(--success)' : '4px solid var(--warning)';
                
                let submissionHtml = '';
                if (t.submission_link) {
                    submissionHtml = `
                        <div style="font-size:11px; margin-top:8px; display:flex; align-items:center; gap:6px;">
                            <i class="fa-solid fa-link" style="color:var(--primary);"></i>
                            <a href="${t.submission_link}" target="_blank" style="color:var(--primary); font-weight:600; text-decoration:none;">View Submission</a>
                        </div>
                    `;
                }
                
                let notesHtml = '';
                if (t.notes) {
                    notesHtml = `<div style="font-size:11px; color:var(--text-muted); background:rgba(255,255,255,0.02); padding:6px; border-radius:6px; margin-top:6px;"><strong>Notes:</strong> ${escapeHTML(t.notes)}</div>`;
                }

                let btnHtml = '';
                if (t.status === 'Completed') {
                    btnHtml = `
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-size:12px; font-weight:700; color:var(--success);"><i class="fa-solid fa-circle-check"></i> Completed</span>
                            <button onclick="toggleOnboardingTaskPending('${t.id}')" style="background:none; border:none; color:var(--text-muted); cursor:pointer; font-size:11px; text-decoration:underline;">Undo</button>
                        </div>
                    `;
                } else {
                    btnHtml = `
                        <button onclick="openOnboardingCompleteModal('${t.id}', '${escapeHTML(t.task_name)}')" class="btn-submit" style="width:100%; padding:6px 12px; font-size:12px; font-weight:600; background:rgba(99,102,241,0.1); color:var(--primary); border:1px solid rgba(99,102,241,0.2);"><i class="fa-solid fa-circle-arrow-up"></i> Submit & Complete</button>
                    `;
                }

                card.innerHTML = `
                    <div>
                        <div style="font-weight:700; font-size:14px; color:var(--text-color);">${escapeHTML(t.task_name)}</div>
                        <div style="font-size:12px; color:var(--text-muted); margin-top:6px; line-height:1.4;">${escapeHTML(t.description)}</div>
                        ${submissionHtml}
                        ${notesHtml}
                    </div>
                    <div>
                        ${btnHtml}
                    </div>
                `;
                container.appendChild(card);
            });
        }

        function openOnboardingCompleteModal(id, title) {
            document.getElementById('onboarding-complete-task-id').value = id;
            document.getElementById('onboarding-complete-task-title').innerText = title;
            document.getElementById('onboardingCompleteForm').reset();
            document.getElementById('onboarding-complete-modal').style.display = 'flex';
        }

        function closeOnboardingCompleteModal() {
            document.getElementById('onboarding-complete-modal').style.display = 'none';
        }

        async function handleOnboardingSubmitTask(e) {
            e.preventDefault();
            const id = document.getElementById('onboarding-complete-task-id').value;
            const link = document.getElementById('ob_submission_link').value;
            const notes = document.getElementById('ob_notes').value;

            try {
                const res = await apiFetch(`/onboarding/my-checklist/${id}`, {
                    method: 'PUT',
                    body: {
                        status: 'Completed',
                        submission_link: link,
                        notes: notes
                    }
                });
                if (res.ok) {
                    showToast("Task completed successfully!", "success");
                    closeOnboardingCompleteModal();
                    loadOnboardingChecklist();
                } else {
                    const data = await res.json();
                    showToast(data.error || "Failed to update task", "error");
                }
            } catch (err) {
                showToast("Failed to update task", "error");
            }
        }

        async function toggleOnboardingTaskPending(id) {
            if (!confirm("Are you sure you want to mark this onboarding task as pending again?")) return;
            try {
                const res = await apiFetch(`/onboarding/my-checklist/${id}`, {
                    method: 'PUT',
                    body: {
                        status: 'Pending'
                    }
                });
                if (res.ok) {
                    showToast("Task marked as pending.", "info");
                    loadOnboardingChecklist();
                }
            } catch (err) {
                showToast("Failed to update task", "error");
            }
        }
"""

if script_end_idx != -1:
    content = content[:script_end_idx] + onboarding_js + "\n        " + content[script_end_idx:]

# Update switchTab to load onboarding data when switching to tabs
switch_tab_call = "} else if (tabId === 'leaves') {\n                    loadLeavesData();"
new_switch_tab_call = "} else if (tabId === 'leaves') {\n                    loadLeavesData();\n                } else if (tabId === 'onboarding-admin') {\n                    loadOnboardingAdmin();\n                } else if (tabId === 'onboarding-checklist') {\n                    loadOnboardingChecklist();"
if switch_tab_call in content:
    content = content.replace(switch_tab_call, new_switch_tab_call)

# Trigger onboarding check during checkAuth
check_auth_success = "currentUser = await res.json();\n                setupPortalForRole();"
new_check_auth_success = "currentUser = await res.json();\n                setupPortalForRole();\n                checkOnboardingVisibility();"
if check_auth_success in content:
    content = content.replace(check_auth_success, new_check_auth_success)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("index.html updated successfully!")
