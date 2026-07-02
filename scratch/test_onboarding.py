import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app, db
from bson import ObjectId

client = app.test_client()

def run_tests():
    print("==================================================")
    print("       STARTING ONBOARDING MODULE TESTS           ")
    print("==================================================")

    # 1. Setup Admin session
    admin_user = db.users.find_one({"role": "Admin"})
    if not admin_user:
        print("Error: No Admin user found in database.")
        sys.exit(1)
        
    admin_id = str(admin_user['_id'])
    
    # 2. Setup Intern session (Bhuvan Sai Adithya - empsi10)
    intern_user = db.users.find_one({"username": "empsi10"})
    if not intern_user:
        print("Error: No Intern empsi10 found in database.")
        sys.exit(1)
        
    intern_id = str(intern_user['_id'])

    # 3. Setup Manager session (Jyothi - empsi02)
    manager_user = db.users.find_one({"role": "Manager"})
    if not manager_user:
        print("Error: No Manager found in database.")
        sys.exit(1)
        
    manager_id = str(manager_user['_id'])

    print("\n--- Test 1: Admin creates onboarding templates ---")
    with client.session_transaction() as sess:
        sess['user_id'] = admin_id
        sess['username'] = admin_user['username']
        sess['role'] = 'Admin'

    # Clear existing templates to start fresh
    db.onboarding_templates.delete_many({})
    
    tasks = [
        {"task_name": "Submit Documents", "description": "ID copy, Address copy"},
        {"task_name": "Setup Git Workspace", "description": "Configure Git global user email and sign key"}
    ]
    
    for t in tasks:
        res = client.post('/admin/onboarding/templates', json=t)
        print(f"Create Template '{t['task_name']}': Status {res.status_code}, Response {res.get_json()}")
        assert res.status_code == 200

    # Fetch templates
    res = client.get('/admin/onboarding/templates')
    templates = res.get_json()
    print(f"Templates in DB: {len(templates)}")
    assert len(templates) == 2
    template_ids = [t['id'] for t in templates]

    print("\n--- Test 2: Admin assigns templates to Intern ---")
    res = client.post('/admin/onboarding/assign', json={"username": "empsi10"})
    print(f"Assign Checklist to empsi10: Status {res.status_code}, Response {res.get_json()}")
    assert res.status_code == 200

    print("\n--- Test 3: Intern views checklist and completes a task ---")
    with client.session_transaction() as sess:
        sess['user_id'] = intern_id
        sess['username'] = 'empsi10'
        sess['role'] = 'Intern'

    # Fetch my checklist
    res = client.get('/onboarding/my-checklist')
    checklist = res.get_json()
    print(f"Intern checklist length: {len(checklist)}")
    assert len(checklist) == 2
    task_id = checklist[0]['id']

    # Update task status (Complete it)
    res = client.put(f'/onboarding/my-checklist/{task_id}', json={
        "status": "Completed",
        "submission_link": "https://drive.google.com/drive/folders/mock_ob",
        "notes": "Here are my docs."
    })
    print(f"Complete Task: Status {res.status_code}, Response {res.get_json()}")
    assert res.status_code == 200

    # Fetch checklist again to verify status
    res = client.get('/onboarding/my-checklist')
    checklist = res.get_json()
    assert checklist[0]['status'] == 'Completed'
    print(f"Task updated status verified: {checklist[0]['status']}")

    print("\n--- Test 4: Admin views progress and verified employee checklist ---")
    with client.session_transaction() as sess:
        sess['user_id'] = admin_id
        sess['username'] = admin_user['username']
        sess['role'] = 'Admin'

    # Get overall onboarding progress
    res = client.get('/admin/onboarding/progress')
    progress = res.get_json()
    empsi10_progress = next(p for p in progress if p['username'] == 'empsi10')
    print(f"empsi10 Progress: {empsi10_progress['completed_tasks']}/{empsi10_progress['total_tasks']} completed")
    assert empsi10_progress['completed_tasks'] == 1
    assert empsi10_progress['total_tasks'] == 2

    # Get detailed checklist of empsi10
    res = client.get('/admin/onboarding/checklist/empsi10')
    checklist_details = res.get_json()
    print(f"Checklist item 1 status: {checklist_details[0]['status']}, Link: {checklist_details[0]['submission_link']}")
    assert checklist_details[0]['status'] == 'Completed'
    assert checklist_details[0]['submission_link'] == 'https://drive.google.com/drive/folders/mock_ob'

    print("\n--- Test 5: Manager is blocked from Onboarding Admin endpoints ---")
    with client.session_transaction() as sess:
        sess['user_id'] = manager_id
        sess['username'] = manager_user['username']
        sess['role'] = 'Manager'

    res = client.get('/admin/onboarding/progress')
    print(f"Manager gets Onboarding Progress: Status {res.status_code} (Expected 401/403)")
    assert res.status_code in [401, 403]

    res = client.post('/admin/onboarding/assign', json={"username": "empsi10"})
    print(f"Manager assigns checklist: Status {res.status_code} (Expected 401/403)")
    assert res.status_code in [401, 403]

    print("\n==================================================")
    print("      ALL ONBOARDING TESTS PASSED SUCCESSFULLY!    ")
    print("==================================================")

if __name__ == '__main__':
    run_tests()
