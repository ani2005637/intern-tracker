import json
from pymongo import MongoClient
from bson import ObjectId

class Encoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

db = MongoClient('mongodb://localhost:27017/').sanna_tracker
reqs = list(db.leave_requests.find({}))
print(json.dumps(reqs, cls=Encoder, indent=2))
