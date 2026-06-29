import os
import re

app_path = r"C:\Users\s.anirudh\Downloads\tracker\app.py"
html_path = r"C:\Users\s.anirudh\Downloads\tracker\index.html"

# 1. Update app.py
with open(app_path, 'r', encoding='utf-8') as f:
    app_content = f.read()

# Replace the Excel-based hosting routes with the new MongoDB-backed ones
hosting_routes_start = app_content.find('HOSTING_EXCEL_PATH =')
if hosting_routes_start != -1:
    main_block_idx = app_content.find("if __name__ == '__main__':")
    app_content = app_content[:hosting_routes_start] + app_content[main_block_idx:]

# Define the new MongoDB-backed hosting logic and routes
new_hosting_code = """HOSTING_EXCEL_PATH = r"C:\\Users\\s.anirudh\\Downloads\\Domain & Hosting Account Details.xlsx"

def import_hosting_from_excel_if_empty():
    try:
        if db.hosting_details.count_documents({}) > 0:
            return
    except Exception:
        return
    
    excel_path = HOSTING_EXCEL_PATH
    if not os.path.exists(excel_path):
        excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Domain & Hosting Account Details.xlsx")
        
    if not os.path.exists(excel_path):
        return
        
    try:
        wb = openpyxl.load_workbook(excel_path, read_only=True)
        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            rows = list(sheet.iter_rows(values_only=True))
            if not rows:
                continue
            headers = [str(h) if h is not None else f"Col{i}" for i, h in enumerate(rows[0])]
            while headers and headers[-1].startswith('Col') and headers[-1] != 'Col0':
                headers.pop()
                
            for r_idx, r in enumerate(rows[1:], start=2):
                if all(v is None for v in r):
                    continue
                doc = {
                    "category": sheet_name,
                    "created_at": datetime.datetime.utcnow()
                }
                for c_idx, val in enumerate(r):
                    if c_idx < len(headers):
                        header = headers[c_idx]
                        if isinstance(val, (datetime.datetime, datetime.date)):
                            val = val.strftime("%Y-%m-%d")
                        doc[header] = val if val is not None else ""
                db.hosting_details.insert_one(doc)
        print("Successfully imported hosting details from Excel to MongoDB!")
    except Exception as e:
        print(f"Failed to import hosting details: {e}")

@app.route('/admin/hosting-details', methods=['GET'])
def get_hosting_details_route():
    user = get_logged_in_user()
    if not user or user['role'] != 'Admin':
        return jsonify({"error": "Unauthorized"}), 401

    try:
        import_hosting_from_excel_if_empty()
        
        categories = ['GoDaddy', 'CPanel Domain', 'Domain With Us', 'Domain With Client']
        data = {cat: [] for cat in categories}
        
        docs = list(db.hosting_details.find({}))
        # Sort manually by Sl No if it is numeric
        def get_sl_no(d):
            try:
                return int(d.get('Sl No', 9999))
            except (ValueError, TypeError):
                return 9999

        docs.sort(key=get_sl_no)

        for doc in docs:
            cat = doc.get('category', 'GoDaddy')
            if cat not in data:
                data[cat] = []
            
            item = {
                "id": str(doc['_id'])
            }
            for k, v in doc.items():
                if k not in ['_id', 'category', 'created_at']:
                    item[k] = v
            data[cat].append(item)
            
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": f"Failed to read hosting details: {str(e)}"}), 500

@app.route('/admin/hosting-details/add', methods=['POST'])
def add_hosting_detail_route():
    user = get_logged_in_user()
    if not user or user['role'] != 'Admin':
        return jsonify({"error": "Unauthorized"}), 401

    try:
        req_data = request.get_json() or {}
        category = req_data.get('sheet_name')
        new_values = req_data.get('values', {})

        if not category:
            return jsonify({"error": "Category is required"}), 400

        last_item = db.hosting_details.find_one({"category": category}, sort=[("Sl No", -1)])
        sl_no = 1
        if last_item and last_item.get('Sl No'):
            try:
                sl_no = int(last_item['Sl No']) + 1
            except (ValueError, TypeError):
                pass

        doc = {
            "category": category,
            "created_at": datetime.datetime.utcnow(),
            "Sl No": sl_no
        }
        for k, v in new_values.items():
            if k not in ['id', 'category', 'created_at', 'Sl No']:
                doc[k] = v

        db.hosting_details.insert_one(doc)
        return jsonify({"message": "Hosting detail added successfully"})
    except Exception as e:
        return jsonify({"error": f"Failed to add hosting detail: {str(e)}"}), 500

@app.route('/admin/hosting-details/edit', methods=['PUT'])
def edit_hosting_detail_route():
    user = get_logged_in_user()
    if not user or user['role'] != 'Admin':
        return jsonify({"error": "Unauthorized"}), 401

    try:
        req_data = request.get_json() or {}
        item_id = req_data.get('row_idx')
        updated_values = req_data.get('values', {})

        if not item_id:
            return jsonify({"error": "Item ID is required"}), 400

        update_fields = {}
        for k, v in updated_values.items():
            if k not in ['id', 'category', 'created_at', 'Sl No']:
                update_fields[k] = v

        db.hosting_details.update_one({"_id": ObjectId(item_id)}, {"$set": update_fields})
        return jsonify({"message": "Hosting detail updated successfully"})
    except Exception as e:
        return jsonify({"error": f"Failed to update hosting detail: {str(e)}"}), 500

@app.route('/admin/hosting-details/delete', methods=['DELETE'])
def delete_hosting_detail_route():
    user = get_logged_in_user()
    if not user or user['role'] != 'Admin':
        return jsonify({"error": "Unauthorized"}), 401

    try:
        req_data = request.get_json() or {}
        item_id = req_data.get('row_idx')

        if not item_id:
            return jsonify({"error": "Item ID is required"}), 400

        item = db.hosting_details.find_one({"_id": ObjectId(item_id)})
        if not item:
            return jsonify({"error": "Item not found"}), 404
        category = item['category']

        db.hosting_details.delete_one({"_id": ObjectId(item_id)})
        
        category_items = list(db.hosting_details.find({"category": category}).sort("created_at", 1))
        for idx, cat_item in enumerate(category_items, start=1):
            db.hosting_details.update_one({"_id": cat_item['_id']}, {"$set": {"Sl No": idx}})

        return jsonify({"message": "Hosting detail deleted successfully"})
    except Exception as e:
        return jsonify({"error": f"Failed to delete hosting detail: {str(e)}"}), 500

@app.route('/admin/hosting-details/export', methods=['GET'])
def export_hosting_details_route():
    user = get_logged_in_user()
    if not user or user['role'] != 'Admin':
        return jsonify({"error": "Unauthorized"}), 401

    try:
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        
        categories = ['GoDaddy', 'CPanel Domain', 'Domain With Us', 'Domain With Client']
        headers_map = {
            'GoDaddy': ['Sl No', 'Domains', 'Renewal Date', 'domain cost'],
            'CPanel Domain': ['Sl No', 'Domains', 'hosting renewal cost', 'date'],
            'Domain With Us': ['Sl No', 'Domains', 'Domain With Us or Client'],
            'Domain With Client': ['Sl No', 'Domains']
        }
        
        for cat in categories:
            sheet = wb.create_sheet(title=cat)
            headers = headers_map[cat]
            sheet.append(headers)
            
            docs = list(db.hosting_details.find({"category": cat}))
            def get_sl_no(d):
                try:
                    return int(d.get('Sl No', 9999))
                except (ValueError, TypeError):
                    return 9999
            docs.sort(key=get_sl_no)

            for doc in docs:
                row_data = []
                for h in headers:
                    row_data.append(doc.get(h, ""))
                sheet.append(row_data)
                
        temp_filename = "Domain_Hosting_Account_Details_Export.xlsx"
        wb.save(temp_filename)
        
        return send_from_directory(
            os.path.abspath(os.path.dirname(__file__)),
            temp_filename,
            as_attachment=True,
            download_name="Domain & Hosting Account Details.xlsx"
        )
    except Exception as e:
        return jsonify({"error": f"Failed to export hosting details: {str(e)}"}), 500


"""

main_block_idx = app_content.find("if __name__ == '__main__':")
app_content = app_content[:main_block_idx] + new_hosting_code + app_content[main_block_idx:]

with open(app_path, 'w', encoding='utf-8') as f:
    f.write(app_content)
print("app.py updated with MongoDB hosting logic!")


# 2. Update index.html
with open(html_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

# Add Download Excel button next to Add Account Detail
old_btn_group = """                        <div style="display: flex; align-items: center; gap: 12px;">
                            <select id="hosting-sheet-select" onchange="changeHostingSheet()" style="padding: 8px 16px; border-radius: 8px; font-size: 14px; background: var(--bg-card); border: 1px solid var(--border-color); color: var(--text-color); font-weight: 500;">"""

new_btn_group = """                        <div style="display: flex; align-items: center; gap: 12px;">
                            <a href="/admin/hosting-details/export" target="_blank" class="btn-submit" style="padding: 8px 16px; border-radius: 8px; font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 8px; text-decoration: none; background: rgba(16, 185, 129, 0.1); color: var(--success); border: 1px solid rgba(16, 185, 129, 0.2);">
                                <i class="fa-solid fa-file-excel"></i> Download Excel
                            </a>
                            <select id="hosting-sheet-select" onchange="changeHostingSheet()" style="padding: 8px 16px; border-radius: 8px; font-size: 14px; background: var(--bg-card); border: 1px solid var(--border-color); color: var(--text-color); font-weight: 500;">"""

if old_btn_group in html_content:
    html_content = html_content.replace(old_btn_group, new_btn_group)

# Replace Javascript string ID passing in renderHostingTable
old_js_actions = """                // Actions cell
                const tdAction = document.createElement('td');
                tdAction.style.textAlign = 'center';
                tdAction.innerHTML = `
                    <button onclick="openHostingModal(true, ${r._row_idx})" class="btn-action edit" title="Edit" style="background: rgba(99,102,241,0.1); color: var(--primary); padding: 6px 10px; border-radius: 6px; border: none; cursor: pointer; margin-right: 6px; font-weight:600;"><i class="fa-solid fa-pen"></i> Edit</button>
                    <button onclick="deleteHostingRow(${r._row_idx})" class="btn-action delete" title="Delete" style="background: rgba(239,68,68,0.1); color: var(--danger); padding: 6px 10px; border-radius: 6px; border: none; cursor: pointer; font-weight:600;"><i class="fa-solid fa-trash"></i> Delete</button>
                `;"""

new_js_actions = """                // Actions cell
                const tdAction = document.createElement('td');
                tdAction.style.textAlign = 'center';
                tdAction.innerHTML = `
                    <button onclick="openHostingModal(true, '${r.id}')" class="btn-action edit" title="Edit" style="background: rgba(99,102,241,0.1); color: var(--primary); padding: 6px 10px; border-radius: 6px; border: none; cursor: pointer; margin-right: 6px; font-weight:600;"><i class="fa-solid fa-pen"></i> Edit</button>
                    <button onclick="deleteHostingRow('${r.id}')" class="btn-action delete" title="Delete" style="background: rgba(239,68,68,0.1); color: var(--danger); padding: 6px 10px; border-radius: 6px; border: none; cursor: pointer; font-weight:600;"><i class="fa-solid fa-trash"></i> Delete</button>
                `;"""

if old_js_actions in html_content:
    html_content = html_content.replace(old_js_actions, new_js_actions)

# Update openHostingModal parameter signature and row finding logic
old_modal_open = """        function openHostingModal(isEdit = false, rowIdx = null) {
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
            } else {"""

new_modal_open = """        function openHostingModal(isEdit = false, itemId = null) {
            const modal = document.getElementById('hosting-modal');
            const titleEl = document.getElementById('hosting-modal-title');
            const form = document.getElementById('hostingForm');
            const fieldsContainer = document.getElementById('hosting-dynamic-fields');
            
            form.reset();
            fieldsContainer.innerHTML = '';
            
            const rows = hostingData[currentHostingSheet] || [];
            const headers = rows.length > 0 ? Object.keys(rows[0]).filter(k => k !== '_row_idx' && k !== 'Sl No' && k !== 'id') : ['Domains'];
            
            let rowData = null;
            if (isEdit && itemId !== null) {
                titleEl.innerText = `Edit ${currentHostingSheet} Detail`;
                document.getElementById('hosting-edit-row-idx').value = itemId;
                rowData = rows.find(r => r.id === itemId);
            } else {"""

if old_modal_open in html_content:
    html_content = html_content.replace(old_modal_open, new_modal_open)

# Update deleteHostingRow parameter signature
old_delete_row = "async function deleteHostingRow(rowIdx) {"
new_delete_row = "async function deleteHostingRow(itemId) {"
if old_delete_row in html_content:
    html_content = html_content.replace(old_delete_row, new_delete_row)

old_delete_body = """                    body: {
                        sheet_name: currentHostingSheet,
                        row_idx: parseInt(rowIdx)
                    }"""

new_delete_body = """                    body: {
                        sheet_name: currentHostingSheet,
                        row_idx: itemId
                    }"""

if old_delete_body in html_content:
    html_content = html_content.replace(old_delete_body, new_delete_body)

# Update handleHostingSubmit parsing
old_submit_parse = """                if (isEdit) {
                    url = '/admin/hosting-details/edit';
                    method = 'PUT';
                    payload.row_idx = parseInt(rowIdx);
                }"""

new_submit_parse = """                if (isEdit) {
                    url = '/admin/hosting-details/edit';
                    method = 'PUT';
                    payload.row_idx = rowIdx;
                }"""

if old_submit_parse in html_content:
    html_content = html_content.replace(old_submit_parse, new_submit_parse)

# Update loadHostingDetails to show generic errors instead of silent failure
old_load_err = """                if (!res.ok) {
                    if (res.status === 404) {
                        showToast("Domain & Hosting Excel file not found in Downloads folder.", "error");
                    }
                    return;
                }"""

new_load_err = """                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    showToast(errData.error || "Failed to load hosting details from server.", "error");
                    return;
                }"""

if old_load_err in html_content:
    html_content = html_content.replace(old_load_err, new_load_err)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)
print("index.html updated with ID-based modal handling and Download Excel button!")
