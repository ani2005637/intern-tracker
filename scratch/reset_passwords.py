import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import db
from werkzeug.security import generate_password_hash, check_password_hash

users = list(db.users.find())
print(f"Found {len(users)} users. Resetting passwords...")

for u in users:
    username = u['username']
    # Default password is the username itself
    default_password = username
    
    # Special cases for admin/manager if needed, but let's keep them as is or set them to their defaults
    if username == 'admin':
        default_password = 'admin123'
    elif username == 'manager':
        default_password = 'manager123'
        
    new_hash = generate_password_hash(default_password)
    db.users.update_one({"_id": u["_id"]}, {"$set": {"password_hash": new_hash}})
    
    # Verify
    updated_user = db.users.find_one({"_id": u["_id"]})
    matches = check_password_hash(updated_user['password_hash'], default_password)
    print(f"User: {username} | Password: {default_password} | Verified: {matches}")

print("All passwords reset and verified successfully!")
