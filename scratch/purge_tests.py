import os
import pymongo

mongo_uri = os.environ.get('MONGO_URI')
if not mongo_uri:
    mongo_uri = 'mongodb+srv://srikakulaanirudh0506_db_user:e9gSM1PbSju6TYek@cluster0.3jbhs01.mongodb.net/?appName=Cluster0'

client = pymongo.MongoClient(mongo_uri)
db = client['intern_tracker']

print("--- PURGING TEST DATA FROM DATABASE ---")

# Delete matching users
u_res = db.users.delete_many({
    "$or": [
        {"username": {"$regex": "test", "$options": "i"}},
        {"full_name": {"$regex": "test", "$options": "i"}},
        {"username": {"$regex": "pending", "$options": "i"}},
        {"full_name": {"$regex": "pending", "$options": "i"}}
    ]
})
print(f"Purged Users: {u_res.deleted_count}")

# Delete matching logs
l_res = db.intern_logs.delete_many({
    "$or": [
        {"intern_name": {"$regex": "test", "$options": "i"}},
        {"intern_fullname": {"$regex": "test", "$options": "i"}}
    ]
})
print(f"Purged Logs: {l_res.deleted_count}")

# Delete matching sessions
s_res = db.session_logs.delete_many({
    "$or": [
        {"username": {"$regex": "test", "$options": "i"}},
        {"username": {"$regex": "pending", "$options": "i"}}
    ]
})
print(f"Purged Sessions: {s_res.deleted_count}")

# Delete matching tasks
t_res = db.tasks.delete_many({
    "$or": [
        {"intern_name": {"$regex": "test", "$options": "i"}},
        {"assigned_by": {"$regex": "test", "$options": "i"}}
    ]
})
print(f"Purged Tasks: {t_res.deleted_count}")

# Delete matching leave requests
lr_res = db.leave_requests.delete_many({
    "$or": [
        {"username": {"$regex": "test", "$options": "i"}},
        {"actioned_by": {"$regex": "test", "$options": "i"}}
    ]
})
print(f"Purged Leave Requests: {lr_res.deleted_count}")

# Delete matching leave balances
lb_res = db.leave_balances.delete_many({
    "username": {"$regex": "test", "$options": "i"}
})
print(f"Purged Leave Balances: {lb_res.deleted_count}")

# Delete matching notifications
n_res = db.notifications.delete_many({
    "$or": [
        {"username": {"$regex": "test", "$options": "i"}},
        {"message": {"$regex": "test", "$options": "i"}},
        {"message": {"$regex": "pending", "$options": "i"}}
    ]
})
print(f"Purged Notifications: {n_res.deleted_count}")

print("--- PURGE COMPLETED ---")
