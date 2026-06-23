import os
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

def get_db():
    mongo_uri = os.environ.get('MONGO_URI')
    if not mongo_uri:
        mongo_uri = 'mongodb+srv://srikakulaanirudh0506_db_user:e9gSM1PbSju6TYek@cluster0.3jbhs01.mongodb.net/?appName=Cluster0'
    client = MongoClient(mongo_uri)
    return client, client['intern_tracker']

def seed():
    client, db = get_db()

    # Clear existing data completely
    print("Clearing database collections...")
    db.users.delete_many({})
    db.intern_logs.delete_many({})
    db.tasks.delete_many({})
    db.skills_log.delete_many({})
    db.mentor_feedback.delete_many({})

    # Seed ONLY srikakula anirudh intern account
    print("Seeding srikakula anirudh intern user account...")
    hashed_pw = generate_password_hash('anirudh123')
    db.users.insert_one({
        'username': 'srikakula anirudh',
        'password_hash': hashed_pw,
        'full_name': 'SRIKAKULA ANIRUDH',
        'role': 'Intern'
    })

    client.close()
    print("Database cleared and seeded successfully with srikakula anirudh only!")

if __name__ == '__main__':
    seed()
