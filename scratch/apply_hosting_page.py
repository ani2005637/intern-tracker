import os

html_path = r"C:\Users\s.anirudh\Downloads\tracker\index.html"
if not os.path.exists(html_path):
    print("index.html not found!")
    exit(1)

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update the sidebar navigation list to use the scrollable class and add the Hosting Details nav item
old_ul = '<ul style="list-style: none; display: flex; flex-direction: column; gap: 10px;">'
new_ul = '<ul class="sidebar-nav-list">'

nav_item_to_add = """                <li class="nav-item" id="nav-hosting-details" style="display: none;">
                    <button onclick="switchTab('hosting-details')">
                        <i class="fa-solid fa-server"></i> Hosting Details
                    </button>
                </li>"""

# We insert the new nav item right before the closing </ul> of the sidebar
# Let's find the navigation block
nav_end_idx = content.find('</ul>', content.find('class="sidebar"'))
if nav_end_idx != -1:
    content = content[:nav_end_idx] + nav_item_to_add + "\n            " + content[nav_end_idx:]

if old_ul in content:
    content = content.replace(old_ul, new_ul)

# 2. Add visibility toggles in setupPortalForRole()
# Find the Intern/Employee block:
intern_block = "document.getElementById('nav-attendance-matrix').style.display = 'none';"
if intern_block in content:
    content = content.replace(intern_block, intern_block + "\n                document.getElementById('nav-hosting-details').style.display = 'none';")

# Find the Manager block:
manager_block = "document.getElementById('nav-attendance-matrix').style.display = 'block';"
if manager_block in content:
    content = content.replace(manager_block, manager_block + "\n                document.getElementById('nav-hosting-details').style.display = 'none';")

# Find the Admin block:
admin_block = "document.getElementById('nav-attendance-matrix').style.display = 'block';"
# Since both manager and admin have this line, let's target the Admin section specifically:
# Admin starts around: // Admin
admin_section_start = content.find('// Admin', content.find('function setupPortalForRole'))
if admin_section_start != -1:
    target_idx = content.find("document.getElementById('nav-attendance-matrix').style.display = 'block';", admin_section_start)
    if target_idx != -1:
        end_line_idx = target_idx + len("document.getElementById('nav-attendance-matrix').style.display = 'block';")
        content = content[:end_line_idx] + "\n                document.getElementById('nav-hosting-details').style.display = 'block';" + content[end_line_idx:]

# 3. Add the Hosting Details section HTML
# We can insert it right after the leaves section: </section> (leaves)
leaves_section_end = content.find('</section>', content.find('id="leaves"'))
hosting_section_html = """

            <!-- HOSTING & DOMAIN DETAILS MODULE (Admin Only) -->
            <section id="hosting-details" class="tab-content">
                <div class="panel" style="margin-bottom: 24px; padding: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <i class="fa-solid fa-server" style="color: var(--primary); font-size: 24px;"></i>
                            <h2 style="margin: 0; font-size: 18px; font-weight: 600; color: var(--text-color);">Domain & Hosting Account Details</h2>
                        </div>
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <select id="hosting-sheet-select" onchange="changeHostingSheet()" style="padding: 8px 16px; border-radius: 8px; font-size: 14px; background: var(--bg-card); border: 1px solid var(--border-color); color: var(--text-color); font-weight: 500;">
                                <option value="GoDaddy">GoDaddy Domains</option>
                                <option value="CPanel Domain">cPanel Domains</option>
                                <option value="Domain With Us">Domain With Us</option>
                                <option value="Domain With Client">Domain With Client</option>
                            </select>
                            <button onclick="openHostingModal()" class="btn-submit" style="padding: 8px 16px; border-radius: 8px; font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 8px;">
                                <i class="fa-solid fa-circle-plus"></i> Add Account Detail
                            </button>
                        </div>
                    </div>
                    <div style="margin-top: 15px;">
                        <input type="text" id="hosting-search" oninput="filterHostingTable()" placeholder="Search domains..." style="width: 100%; max-width: 400px; padding: 8px 12px; font-size: 13px; border-radius: 8px;">
                    </div>
                </div>

                <div class="panel" style="padding: 24px;">
                    <div style="overflow-x: auto;">
                        <table class="data-table" style="width: 100%;">
                            <thead id="hosting-table-head">
                                <!-- Populated dynamically -->
                            </thead>
                            <tbody id="hosting-table-body">
                                <!-- Populated dynamically -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </section>

            <!-- Add/Edit Hosting Modal -->
            <div id="hosting-modal" class="modal-overlay" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 2000; align-items: center; justify-content: center; backdrop-filter: blur(5px); -webkit-backdrop-filter: blur(5px);">
                <div class="modal-content" style="width: 100%; max-width: 500px; background: var(--bg-card); border: 1px solid var(--card-border); border-radius: 16px; padding: 24px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.3);">
                    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding-bottom: 15px; margin-bottom: 20px;">
                        <h3 id="hosting-modal-title" style="margin: 0; font-size: 18px; font-weight: 600; color: var(--text-color);">Add Detail</h3>
                        <button onclick="closeHostingModal()" style="background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 18px;"><i class="fa-solid fa-xmark"></i></button>
                    </div>
                    <form id="hostingForm" onsubmit="handleHostingSubmit(event)">
                        <input type="hidden" id="hosting-edit-row-idx">
                        <div id="hosting-dynamic-fields">
                            <!-- Populated dynamically based on selected sheet -->
                        </div>
                        <div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px; border-top: 1px solid var(--border-color); padding-top: 15px;">
                            <button type="button" onclick="closeHostingModal()" class="btn-submit" style="background: rgba(255,255,255,0.05); color: var(--text-color); border: 1px solid var(--border-color);">Cancel</button>
                            <button type="submit" class="btn-submit" id="btn-submit-hosting"><i class="fa-solid fa-floppy-disk"></i> Save Detail</button>
                        </div>
                    </form>
                </div>
            </div>"""

if leaves_section_end != -1:
    end_tag_idx = leaves_section_end + len('</section>')
    content = content[:end_tag_idx] + hosting_section_html + content[end_tag_idx:]

# 4. Add JavaScript logic at the end of the script
# We can find the end of the script tag or right before: /* ----------------- EMPLOYEE DIRECTORY & ATTENDANCE MATRIX LOGIC ----------------- */
# Or right before the closing </script>
script_end_idx = content.rfind('</script>')
hosting_js = """
        /* ----------------- HOSTING & DOMAIN DETAILS LOGIC (Admin Only) ----------------- */
        let hostingData = {};
        let currentHostingSheet = 'GoDaddy';

        async function loadHostingDetails() {
            try {
                const res = await apiFetch('/admin/hosting-details');
                if (!res.ok) {
                    if (res.status === 404) {
                        showToast("Domain & Hosting Excel file not found in Downloads folder.", "error");
                    }
                    return;
                }
                hostingData = await res.json();
                renderHostingTable();
            } catch (err) {
                console.error("Failed to load hosting details:", err);
                showToast("Error loading hosting details: " + err.message, "error");
            }
        }

        function changeHostingSheet() {
            currentHostingSheet = document.getElementById('hosting-sheet-select').value;
            renderHostingTable();
        }

        function renderHostingTable() {
            const rows = hostingData[currentHostingSheet] || [];
            const tableHead = document.getElementById('hosting-table-head');
            const tableBody = document.getElementById('hosting-table-body');
            
            tableHead.innerHTML = '';
            tableBody.innerHTML = '';

            if (rows.length === 0) {
                tableHead.innerHTML = `<tr><th>Domains</th><th>Actions</th></tr>`;
                tableBody.innerHTML = `<tr><td colspan="2" style="text-align:center; color:var(--text-muted); padding:20px;">No details found.</td></tr>`;
                return;
            }

            // Get headers from first row keys, excluding '_row_idx'
            const headers = Object.keys(rows[0]).filter(k => k !== '_row_idx');
            
            // Render Headers
            const thr = document.createElement('tr');
            headers.forEach(h => {
                const th = document.createElement('th');
                th.innerText = h;
                if (h === 'Sl No') th.style.width = '70px';
                thr.appendChild(th);
            });
            const thAction = document.createElement('th');
            thAction.innerText = 'Actions';
            thAction.style.textAlign = 'center';
            thAction.style.width = '150px';
            thr.appendChild(thAction);
            tableHead.appendChild(thr);

            // Render Rows
            rows.forEach(r => {
                const tr = document.createElement('tr');
                headers.forEach(h => {
                    const td = document.createElement('td');
                    td.innerText = r[h] || '';
                    if (h === 'Domains') td.style.fontWeight = '600';
                    tr.appendChild(td);
                });

                // Actions cell
                const tdAction = document.createElement('td');
                tdAction.style.textAlign = 'center';
                tdAction.innerHTML = `
                    <button onclick="openHostingModal(true, ${r._row_idx})" class="btn-action edit" title="Edit" style="background: rgba(99,102,241,0.1); color: var(--primary); padding: 6px 10px; border-radius: 6px; border: none; cursor: pointer; margin-right: 6px; font-weight:600;"><i class="fa-solid fa-pen"></i> Edit</button>
                    <button onclick="deleteHostingRow(${r._row_idx})" class="btn-action delete" title="Delete" style="background: rgba(239,68,68,0.1); color: var(--danger); padding: 6px 10px; border-radius: 6px; border: none; cursor: pointer; font-weight:600;"><i class="fa-solid fa-trash"></i> Delete</button>
                `;
                tr.appendChild(tdAction);
                tableBody.appendChild(tr);
            });
        }

        function filterHostingTable() {
            const query = document.getElementById('hosting-search').value.toLowerCase().trim();
            const rows = document.querySelectorAll('#hosting-table-body tr');
            rows.forEach(row => {
                const cells = Array.from(row.querySelectorAll('td'));
                if (cells.length <= 1) return;
                const match = cells.some(c => c.innerText.toLowerCase().includes(query));
                row.style.display = match ? '' : 'none';
            });
        }

        function openHostingModal(isEdit = false, rowIdx = null) {
            const modal = document.getElementById('hosting-modal');
            const titleEl = document.getElementById('hosting-modal-title');
            const form = document.getElementById('hostingForm');
            const fieldsContainer = document.getElementById('hosting-dynamic-fields');
            
            form.reset();
            fieldsContainer.innerHTML = '';
            
            const rows = hostingData[currentHostingSheet] || [];
            const headers = rows.length > 0 ? Object.keys(rows[0]).filter(k => k !== '_row_idx' && k !== 'Sl No') : ['Domains'];
            
            let rowData = null;
            if (isEdit && rowIdx !== null) {
                titleEl.innerText = `Edit ${currentHostingSheet} Detail`;
                document.getElementById('hosting-edit-row-idx').value = rowIdx;
                rowData = rows.find(r => r._row_idx === rowIdx);
            } else {
                titleEl.innerText = `Add ${currentHostingSheet} Detail`;
                document.getElementById('hosting-edit-row-idx').value = '';
            }

            headers.forEach(h => {
                const group = document.createElement('div');
                group.className = 'form-group';
                group.style.marginBottom = '12px';
                
                const label = document.createElement('label');
                label.innerText = h;
                label.setAttribute('for', `field_${h}`);
                
                let input;
                if (h.toLowerCase().includes('date')) {
                    input = document.createElement('input');
                    input.type = 'date';
                } else {
                    input = document.createElement('input');
                    input.type = 'text';
                    input.placeholder = `Enter ${h.toLowerCase()}`;
                }
                
                input.id = `field_${h}`;
                input.name = h;
                if (h === 'Domains') input.required = true;
                if (rowData) input.value = rowData[h] || '';

                group.appendChild(label);
                group.appendChild(input);
                fieldsContainer.appendChild(group);
            });

            modal.style.display = 'flex';
        }

        function closeHostingModal() {
            document.getElementById('hosting-modal').style.display = 'none';
        }

        async function handleHostingSubmit(e) {
            e.preventDefault();
            const rowIdx = document.getElementById('hosting-edit-row-idx').value;
            const isEdit = !!rowIdx;
            
            const form = document.getElementById('hostingForm');
            const formData = new FormData(form);
            const values = {};
            formData.forEach((val, key) => {
                if (key !== '') values[key] = val;
            });

            const payload = {
                sheet_name: currentHostingSheet,
                values: values
            };

            const submitBtn = document.getElementById('btn-submit-hosting');
            if (submitBtn) submitBtn.disabled = true;

            try {
                let url = '/admin/hosting-details/add';
                let method = 'POST';
                if (isEdit) {
                    url = '/admin/hosting-details/edit';
                    method = 'PUT';
                    payload.row_idx = parseInt(rowIdx);
                }

                const res = await apiFetch(url, {
                    method: method,
                    body: payload
                });

                if (res.ok) {
                    showToast(`Hosting detail ${isEdit ? 'updated' : 'added'} successfully!`, 'success');
                    closeHostingModal();
                    loadHostingDetails();
                } else {
                    const errData = await res.json();
                    showToast(errData.error || 'Failed to save hosting detail', 'error');
                }
            } catch (err) {
                showToast(err.message || 'Failed to save hosting detail', 'error');
            } finally {
                if (submitBtn) submitBtn.disabled = false;
            }
        }

        async function deleteHostingRow(rowIdx) {
            if (!confirm("Are you sure you want to delete this hosting/domain detail? This will update the Excel sheet directly.")) return;

            try {
                const res = await apiFetch('/admin/hosting-details/delete', {
                    method: 'DELETE',
                    body: {
                        sheet_name: currentHostingSheet,
                        row_idx: parseInt(rowIdx)
                    }
                });

                if (res.ok) {
                    showToast("Hosting detail deleted successfully!", "success");
                    loadHostingDetails();
                } else {
                    const errData = await res.json();
                    showToast(errData.error || 'Failed to delete hosting detail', 'error');
                }
            } catch (err) {
                showToast(err.message || 'Failed to delete hosting detail', 'error');
            }
        }
"""

if script_end_idx != -1:
    content = content[:script_end_idx] + hosting_js + "\n        " + content[script_end_idx:]

# Also update switchTab to load hosting details when switching to that tab
switch_tab_call = "} else if (tabId === 'leaves') {\n                    loadLeavesData();"
new_switch_tab_call = "} else if (tabId === 'leaves') {\n                    loadLeavesData();\n                } else if (tabId === 'hosting-details') {\n                    loadHostingDetails();"
if switch_tab_call in content:
    content = content.replace(switch_tab_call, new_switch_tab_call)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("index.html updated successfully!")
