import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app, db
from bson import ObjectId

client = app.test_client()

def run_tests():
    print("==================================================")
    print("  ONBOARDING FILE UPLOAD INTEGRATION TESTS       ")
    print("==================================================")

    # 1. Setup Admin session
    admin_user = db.users.find_one({"role": "Admin"})
    if not admin_user:
        print("Error: No Admin user found in database.")
        sys.exit(1)
        
    admin_id = str(admin_user['_id'])
    
    # 2. Setup Srikakula Anirudh session (empsi13)
    target_user = db.users.find_one({"username": "empsi13"})
    if not target_user:
        print("Error: No Intern empsi13 found in database.")
        sys.exit(1)
        
    target_id = str(target_user['_id'])

    print("\n--- Test 1: Admin creates onboarding template with multiple files ---")
    with client.session_transaction() as sess:
        sess['user_id'] = admin_id
        sess['username'] = admin_user['username']
        sess['role'] = 'Admin'

    # Clear templates to start fresh
    db.onboarding_templates.delete_many({})
    db.onboarding_tasks.delete_many({"username": "empsi13"})
    
    task_data = {
        "task_name": "Upload Required Scans",
        "description": "Please upload clear scans of your ID card and Address utility bill.",
        "required_docs": ["ID Proof Scan", "Address Proof PDF"],
        "required": True
    }
    
    res = client.post('/admin/onboarding/templates', json=task_data)
    print(f"Create Template: Status {res.status_code}, Response {res.get_json()}")
    assert res.status_code == 200

    print("\n--- Test 2: Admin assigns templates to Srikakula Anirudh (empsi13) ---")
    res = client.post('/admin/onboarding/assign', json={"username": "empsi13"})
    print(f"Assign Checklist to empsi13: Status {res.status_code}, Response {res.get_json()}")
    assert res.status_code == 200

    print("\n--- Test 3: Employee views checklist and uploads JPG and PDF files ---")
    with client.session_transaction() as sess:
        sess['user_id'] = target_id
        sess['username'] = 'empsi13'
        sess['role'] = 'Intern'

    # Fetch checklist
    res = client.get('/onboarding/my-checklist')
    checklist = res.get_json()
    print(f"Employee checklist length: {len(checklist)}")
    assert len(checklist) == 1
    task_id = checklist[0]['id']

    # Simulate uploads with Base64 payloads
    ob_submissions = {
        "ID Proof Scan": {
            "filename": "my_national_id.jpg",
            "data": "data:image/jpeg;base64,MOCK_BASE64_IMAGE_BYTES_STR"
        },
        "Address Proof PDF": {
            "filename": "utility_bill.pdf",
            "data": "data:application/pdf;base64,MOCK_BASE64_PDF_BYTES_STR"
        }
    }
    
    res = client.put(f'/onboarding/my-checklist/{task_id}', json={
        "status": "Completed",
        "submissions": ob_submissions,
        "notes": "Uploaded national ID scan (JPG) and utility bill (PDF) successfully."
    })
    print(f"Complete Task: Status {res.status_code}, Response {res.get_json()}")
    assert res.status_code == 200

    # Fetch checklist again to verify saved data
    res = client.get('/onboarding/my-checklist')
    checklist = res.get_json()
    assert checklist[0]['status'] == 'Completed'
    assert checklist[0]['submissions']["ID Proof Scan"]["filename"] == "my_national_id.jpg"
    assert checklist[0]['submissions']["Address Proof PDF"]["data"] == "data:application/pdf;base64,MOCK_BASE64_PDF_BYTES_STR"
    print("Employee Base64 submissions verified successfully!")

    print("\n--- Test 4: Admin views progress and accesses the uploaded files ---")
    with client.session_transaction() as sess:
        sess['user_id'] = admin_id
        sess['username'] = admin_user['username']
        sess['role'] = 'Admin'

    # Get detailed checklist of empsi13
    res = client.get('/admin/onboarding/checklist/empsi13')
    checklist_details = res.get_json()
    print(f"Checklist Status: {checklist_details[0]['status']}")
    print(f"File 1: {checklist_details[0]['submissions']['ID Proof Scan']['filename']}")
    print(f"File 2: {checklist_details[0]['submissions']['Address Proof PDF']['filename']}")
    assert checklist_details[0]['status'] == 'Completed'
    assert checklist_details[0]['submissions']["ID Proof Scan"]["filename"] == "my_national_id.jpg"
    assert checklist_details[0]['submissions']["Address Proof PDF"]["filename"] == "utility_bill.pdf"

    print("\n==================================================")
    print("    ALL FILE UPLOAD TESTS PASSED SUCCESSFULLY!    ")
    print("==================================================")

if __name__ == '__main__':
    run_tests()
