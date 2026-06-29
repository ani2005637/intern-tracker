import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
import json

client = app.test_client()

# Let's see who the users are first to choose a valid login
user_doc = db.users.find_one({"role": "Admin"})
admin_username = user_doc['username'] if user_doc else 'admin'
print(f"Admin username: {admin_username}")

# Let's find manager
manager_doc = db.users.find_one({"username": "manager"})
print(f"Manager doc: {manager_doc}")

def test_as_user(username):
    print(f"\n--- Testing as {username} ---")
    with client.session_transaction() as sess:
        sess['username'] = username
        u = db.users.find_one({"username": username})
        if u:
            sess['user_id'] = str(u['_id'])
            sess['role'] = u['role']
            sess['full_name'] = u['full_name']
    
    # Now fetch /leaves/requests
    res = client.get('/leaves/requests')
    print(f"GET /leaves/requests status: {res.status_code}")
    try:
        print("Response:")
        print(json.dumps(res.get_json(), indent=2))
    except Exception as e:
        print(f"Failed to parse json: {res.data}")

    # Fetch /leaves/team-balances
    res_tb = client.get('/leaves/team-balances')
    print(f"GET /leaves/team-balances status: {res_tb.status_code}")
    try:
        print("Response:")
        print(json.dumps(res_tb.get_json(), indent=2))
    except Exception as e:
        print(f"Failed to parse json: {res_tb.data}")

# Test for admin
test_as_user(admin_username)

# Test for manager
if manager_doc:
    test_as_user(manager_doc['username'])
