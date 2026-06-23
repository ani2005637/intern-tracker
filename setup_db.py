import os
from pymongo import MongoClient

def init_db():
    mongo_uri = os.environ.get('MONGO_URI')
    if not mongo_uri:
        mongo_uri = 'mongodb+srv://srikakulaanirudh0506_db_user:e9gSM1PbSju6TYek@cluster0.3jbhs01.mongodb.net/?appName=Cluster0'
    
    print("Connecting to MongoDB Atlas...")
    client = MongoClient(mongo_uri)
    db = client['intern_tracker']
    
    # Drop existing collections to start fresh
    print("Dropping existing collections...")
    db.users.drop()
    db.intern_logs.drop()
    db.tasks.drop()
    db.skills_log.drop()
    db.mentor_feedback.drop()
    
    # Create unique index on username in users collection
    print("Creating index constraints...")
    db.users.create_index("username", unique=True)
    
    print("MongoDB initialization complete!")
    client.close()

if __name__ == '__main__':
    init_db()
