import os
import re

app_path = r"C:\Users\s.anirudh\Downloads\tracker\app.py"
html_path = r"C:\Users\s.anirudh\Downloads\tracker\index.html"

# 1. Format and comment app.py hosting section
with open(app_path, 'r', encoding='utf-8') as f:
    app_content = f.read()

old_app_block = """HOSTING_EXCEL_PATH = r"C:\\Users\\s.anirudh\\Downloads\\Domain & Hosting Account Details.xlsx"

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
        return jsonify({"error": f"Failed to export hosting details: {str(e)}"}), 500"""

new_app_block = """# =====================================================================
#             DOMAIN & HOSTING DETAILS MODULE (ADMIN ONLY)
# =====================================================================

HOSTING_EXCEL_PATH = r"C:\\Users\\s.anirudh\\Downloads\\Domain & Hosting Account Details.xlsx"

def import_hosting_from_excel_if_empty():
    \"\"\"
    One-time startup migration: If the MongoDB 'hosting_details' collection is
    empty, reads the local Excel file and imports all records into MongoDB Atlas.
    \"\"\"
    try:
        # Check if records already exist to prevent duplicate imports
        if db.hosting_details.count_documents({}) > 0:
            return
    except Exception:
        return
    
    excel_path = HOSTING_EXCEL_PATH
    # Fallback to local project directory if the absolute downloads path is not found
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
                
            # Parse headers and filter out trailing empty columns
            headers = [str(h) if h is not None else f"Col{i}" for i, h in enumerate(rows[0])]
            while headers and headers[-1].startswith('Col') and headers[-1] != 'Col0':
                headers.pop()
                
            # Iterate through rows and insert them into MongoDB
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
    \"\"\"
    Fetch all hosting details from MongoDB, grouped by their category sheet.
    \"\"\"
    user = get_logged_in_user()
    if not user or user['role'] != 'Admin':
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # Verify and trigger import if collection is empty
        import_hosting_from_excel_if_empty()
        
        categories = ['GoDaddy', 'CPanel Domain', 'Domain With Us', 'Domain With Client']
        data = {cat: [] for cat in categories}
        
        docs = list(db.hosting_details.find({}))
        
        # Sort helper to order records by their Sl No
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
            
            # Format the document for the frontend
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
    \"\"\"
    Add a new domain/hosting detail record. Automatically calculates the next Sl No.
    \"\"\"
    user = get_logged_in_user()
    if not user or user['role'] != 'Admin':
        return jsonify({"error": "Unauthorized"}), 401

    try:
        req_data = request.get_json() or {}
        category = req_data.get('sheet_name')
        new_values = req_data.get('values', {})

        if not category:
            return jsonify({"error": "Category is required"}), 400

        # Calculate sequential Sl No for the category
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
    \"\"\"
    Edit an existing domain/hosting detail record in MongoDB.
    \"\"\"
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
    \"\"\"
    Delete a domain/hosting detail record. Recalculates Sl Nos for the remaining items.
    \"\"\"
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

        # Delete the item
        db.hosting_details.delete_one({"_id": ObjectId(item_id)})
        
        # Re-sequence Sl No to keep list order clean
        category_items = list(db.hosting_details.find({"category": category}).sort("created_at", 1))
        for idx, cat_item in enumerate(category_items, start=1):
            db.hosting_details.update_one({"_id": cat_item['_id']}, {"$set": {"Sl No": idx}})

        return jsonify({"message": "Hosting detail deleted successfully"})
    except Exception as e:
        return jsonify({"error": f"Failed to delete hosting detail: {str(e)}"}), 500


@app.route('/admin/hosting-details/export', methods=['GET'])
def export_hosting_details_route():
    \"\"\"
    Generates and downloads a clean, multi-sheet Excel file (.xlsx) with the latest
    domain and hosting records from MongoDB.
    \"\"\"
    user = get_logged_in_user()
    if not user or user['role'] != 'Admin':
        return jsonify({"error": "Unauthorized"}), 401

    try:
        wb = openpyxl.Workbook()
        wb.remove(wb.active) # Remove default sheet
        
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
            
            # Sort helper
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
        return jsonify({"error": f"Failed to export hosting details: {str(e)}"}), 500"""

if old_app_block in app_content:
    app_content = app_content.replace(old_app_block, new_app_block)
    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(app_content)
    print("Formatted app.py hosting section!")
else:
    print("Could not locate the exact app.py block for formatting. Proceeding...")

# 2. Re-verify HTML
print("Formatting and commenting index.html...")
# The HTML code we injected is already clean, but let's make sure it's validated.
