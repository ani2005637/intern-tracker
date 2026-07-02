import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app, db
from bson import ObjectId

client = app.test_client()

def run_tests():
    print("==================================================")
    print("  ONBOARDING MULTI-DOCUMENT FUNCTIONAL TESTS      ")
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

    # 3. Setup Manager session (Jyothi - empsi02)
    manager_user = db.users.find_one({"role": "Manager"})
    if not manager_user:
        print("Error: No Manager found in database.")
        sys.exit(1)
        
    manager_id = str(manager_user['_id'])

    print("\n--- Test 1: Admin creates onboarding template with multiple required docs ---")
    with client.session_transaction() as sess:
        sess['user_id'] = admin_id
        sess['username'] = admin_user['username']
        sess['role'] = 'Admin'

    # Clear templates to start fresh
    db.onboarding_templates.delete_many({})
    db.onboarding_tasks.delete_many({"username": "empsi13"})
    
    task_data = {
        "task_name": "Submit Verification Documents",
        "description": "Please upload clear scanned copies of the requested proofs.",
        "required_docs": ["ID Proof", "Address Proof", "PAN Card"],
        "required": True
    }
    
    res = client.post('/admin/onboarding/templates', json=task_data)
    print(f"Create Template: Status {res.status_code}, Response {res.get_json()}")
    assert res.status_code == 200

    # Fetch templates
    res = client.get('/admin/onboarding/templates')
    templates = res.get_json()
    print(f"Templates in DB: {len(templates)}")
    assert len(templates) == 1
    assert templates[0]['required_docs'] == ["ID Proof", "Address Proof", "PAN Card"]

    print("\n--- Test 2: Admin assigns templates to Srikakula Anirudh (empsi13) ---")
    res = client.post('/admin/onboarding/assign', json={"username": "empsi13"})
    print(f"Assign Checklist to empsi13: Status {res.status_code}, Response {res.get_json()}")
    assert res.status_code == 200

    print("\n--- Test 3: Employee views checklist and submits multiple URLs ---")
    with client.session_transaction() as sess:
        sess['user_id'] = target_id
        sess['username'] = 'empsi13'
        sess['role'] = 'Intern'

    # Fetch my checklist
    res = client.get('/onboarding/my-checklist')
    checklist = res.get_json()
    print(f"Employee checklist length: {len(checklist)}")
    assert len(checklist) == 1
    assert checklist[0]['required_docs'] == ["ID Proof", "Address Proof", "PAN Card"]
    task_id = checklist[0]['id']

    # Update task with separate submissions for each document type
    ob_submissions = {
        "ID Proof": "https://drive.google.com/file/d/mock_id_proof",
        "Address Proof": "https://drive.google.com/file/d/mock_address_proof",
        "PAN Card": "https://drive.google.com/file/d/mock_pan_card"
    }
    res = client.put(f'/onboarding/my-checklist/{task_id}', json={
        "status": "Completed",
        "submissions": ob_submissions,
        "notes": "Submitted all three documents successfully."
    })
    print(f"Complete Task: Status {res.status_code}, Response {res.get_json()}")
    assert res.status_code == 200

    # Fetch checklist again to verify submissions
    res = client.get('/onboarding/my-checklist')
    checklist = res.get_json()
    assert checklist[0]['status'] == 'Completed'
    assert checklist[0]['submissions'] == ob_submissions
    print("Employee submissions verified successfully!")

    print("\n--- Test 4: Admin views progress and accesses all three document links ---")
    with client.session_transaction() as sess:
        sess['user_id'] = admin_id
        sess['username'] = admin_user['username']
        sess['role'] = 'Admin'

    # Get overall onboarding progress
    res = client.get('/admin/onboarding/progress')
    progress = res.get_json()
    user_progress = next(p for p in progress if p['username'] == 'empsi13')
    print(f"empsi13 Progress: {user_progress['completed_tasks']}/{user_progress['total_tasks']} completed")
    assert user_progress['completed_tasks'] == 1
    assert user_progress['total_tasks'] == 1

    # Get detailed checklist of empsi13
    res = client.get('/admin/onboarding/checklist/empsi13')
    checklist_details = res.get_json()
    print(f"Checklist Status: {checklist_details[0]['status']}")
    print(f"Checklist Submissions: {json.dumps(checklist_details[0]['submissions'], indent=2)}")
    assert checklist_details[0]['status'] == 'Completed'
    assert checklist_details[0]['submissions']["PAN Card"] == "https://drive.google.com/file/d/mock_pan_card"

    print("\n==================================================")
    print("    ALL MULTI-DOCUMENT TESTS PASSED SUCCESSFULLY! ")
    print("==================================================")

if __name__ == '__main__':
    run_tests()
