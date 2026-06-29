from pymongo import MongoClient
import json
from bson import ObjectId

class Encoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

mongo_uri = 'mongodb+srv://srikakulaanirudh0506_db_user:e9gSM1PbSju6TYek@cluster0.3jbhs01.mongodb.net/?appName=Cluster0'
client = MongoClient(mongo_uri)
db = client['intern_tracker']

reqs = list(db.leave_requests.find({}))
print("Leave requests:")
print(json.dumps(reqs, cls=Encoder, indent=2))

users = list(db.users.find({}))
print("\nUsers:")
print(json.dumps([{k: v for k, v in u.items() if k != 'password_hash'} for u in users], cls=Encoder, indent=2))
