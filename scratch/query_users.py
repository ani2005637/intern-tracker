from pymongo import MongoClient
mongo_uri = 'mongodb+srv://srikakulaanirudh0506_db_user:e9gSM1PbSju6TYek@cluster0.3jbhs01.mongodb.net/?appName=Cluster0'
client = MongoClient(mongo_uri)
db = client['intern_tracker']

users = list(db.users.find({}))
for u in users:
    print(f"Username: {u['username']}, Full Name: {u.get('full_name')}, Role: {u.get('role')}")
