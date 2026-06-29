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

    # Seed default role testing accounts
    print("Seeding default testing user accounts...")
    default_users = [
        ('admin', 'admin123', 'Admin User', 'Admin', 'admin@sannainnovations.com', 'System Administrator')
    ]
    for username, password, full_name, role, email, title in default_users:
        # Avoid duplicate seed if user somehow already exists
        if not db.users.find_one({'username': username}):
            db.users.insert_one({
                'username': username,
                'password_hash': generate_password_hash(password),
                'full_name': full_name,
                'role': role,
                'email': email,
                'title': title,
                'approved': True
            })

    client.close()
    print("Database cleared and seeded successfully with srikakula anirudh only!")

if __name__ == '__main__':
    seed()
