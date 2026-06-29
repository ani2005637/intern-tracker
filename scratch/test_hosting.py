import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
import json

client = app.test_client()

admin_user = db.users.find_one({"role": "Admin"})
if not admin_user:
    print("No Admin user found in DB!")
    exit(1)

with client.session_transaction() as sess:
    sess['user_id'] = str(admin_user['_id'])
    sess['username'] = admin_user['username']
    sess['role'] = admin_user['role']

res = client.get('/admin/hosting-details')
print("Status:", res.status_code)
try:
    data = res.get_json()
    if data:
        if 'error' in data:
            print("Error response:", data)
        else:
            print("Keys:", list(data.keys()))
            for k in data.keys():
                print(f"Sheet {k}: {len(data[k])} rows")
                if data[k]:
                    print("First row:", data[k][0])
    else:
        print("Response is empty")
except Exception as e:
    print("Failed to parse JSON:", e)
    print("Raw response:", res.data)
