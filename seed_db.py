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

    # Clear existing data
    print("Clearing database collections...")
    db.users.delete_many({})
    db.intern_logs.delete_many({})
    db.tasks.delete_many({})
    db.skills_log.delete_many({})
    db.mentor_feedback.delete_many({})

    # Define users to seed
    users_to_seed = [
        # System Roles
        ('admin', 'admin123', 'Admin User', 'Admin'),
        ('manager', 'manager123', 'Manager User', 'Manager'),
        ('employee', 'employee123', 'Employee User', 'Employee'),
        ('intern', 'intern123', 'Intern User', 'Intern'),
        # Specific Intern Users
        ('srikakula anirudh', 'anirudh123', 'SRIKAKULA ANIRUDH', 'Intern'),
        ('masarapu bhuvan sai adithya', 'bhuvan123', 'MASARAPU BHUVAN SAI ADITHYA', 'Intern'),
        ('jakka balaji mahendra', 'balaji123', 'JAKKA BALAJI MAHENDRA', 'Intern'),
        ('motepalli shalinisree', 'shalini123', 'MOTEPALLI SHALINISREE', 'Intern'),
        ('vansh goyal', 'vansh123', 'VANSH GOYAL', 'Intern')
    ]

    print("Seeding users...")
    for username, raw_pw, full_name, role in users_to_seed:
        hashed_pw = generate_password_hash(raw_pw)
        db.users.insert_one({
            'username': username,
            'password_hash': hashed_pw,
            'full_name': full_name,
            'role': role
        })

    print("Seeding logs, tasks, skills, and feedback...")

    # 1. SRIKAKULA ANIRUDH Logs
    db.intern_logs.insert_many([
        {
            'intern_name': 'srikakula anirudh',
            'date_logged': '2026-06-22',
            'check_in': '09:00',
            'check_out': '17:00',
            'hours_worked': 8.0,
            'task_category': 'Backend Development',
            'tasks_completed': 'Designed SQLite schema and added REST API routes in Flask.',
            'deliverable_completed': 'Yes',
            'blockers': 'None',
            'skills_used': 'Python, SQL, Flask',
            'mood': 5,
            'notes': 'Setup first day task'
        },
        {
            'intern_name': 'srikakula anirudh',
            'date_logged': '2026-06-23',
            'check_in': '09:00',
            'check_out': '17:00',
            'hours_worked': 8.0,
            'task_category': 'Frontend Development',
            'tasks_completed': 'Redesigned index.html dashboard layout with tabbed sidebar.',
            'deliverable_completed': 'Yes',
            'blockers': 'None',
            'skills_used': 'HTML, CSS, JS',
            'mood': 5,
            'notes': 'Matches excel mockup'
        }
    ])

    # 2. MASARAPU BHUVAN SAI ADITHYA Logs
    db.intern_logs.insert_one({
        'intern_name': 'masarapu bhuvan sai adithya',
        'date_logged': '2026-06-22',
        'check_in': '09:30',
        'check_out': '18:00',
        'hours_worked': 8.5,
        'task_category': 'Backend Development',
        'tasks_completed': 'Refactored server response structures and optimized queries.',
        'deliverable_completed': 'Yes',
        'blockers': 'None',
        'skills_used': 'Python, SQLite',
        'mood': 5,
        'notes': 'Completed optimization checks'
    })

    # 3. JAKKA BALAJI MAHENDRA Logs
    db.intern_logs.insert_one({
        'intern_name': 'jakka balaji mahendra',
        'date_logged': '2026-06-22',
        'check_in': '09:00',
        'check_out': '17:00',
        'hours_worked': 8.0,
        'task_category': 'Documentation',
        'tasks_completed': 'Created API endpoint specs and project structure map.',
        'deliverable_completed': 'Yes',
        'blockers': 'None',
        'skills_used': 'Markdown',
        'mood': 4,
        'notes': 'Ready for review'
    })

    # 4. MOTEPALLI SHALINISREE Logs
    db.intern_logs.insert_one({
        'intern_name': 'motepalli shalinisree',
        'date_logged': '2026-06-22',
        'check_in': '09:15',
        'check_out': '17:15',
        'hours_worked': 8.0,
        'task_category': 'Bug Fixing & QA',
        'tasks_completed': 'Investigated CORS bugs and tested preflight options.',
        'deliverable_completed': 'Yes',
        'blockers': 'None',
        'skills_used': 'Chrome DevTools',
        'mood': 4,
        'notes': 'CORS fix works locally'
    })

    # 5. VANSH GOYAL Logs
    db.intern_logs.insert_one({
        'intern_name': 'vansh goyal',
        'date_logged': '2026-06-22',
        'check_in': '09:00',
        'check_out': '17:00',
        'hours_worked': 8.0,
        'task_category': 'Frontend Development',
        'tasks_completed': 'Polished Glassmorphism cards styling and CSS animations.',
        'deliverable_completed': 'Yes',
        'blockers': 'None',
        'skills_used': 'Vanilla CSS',
        'mood': 5,
        'notes': 'Smooth transitions added'
    })

    # Add mock tasks
    db.tasks.insert_many([
        {
            'intern_name': 'srikakula anirudh',
            'task_name': 'Connect PostgreSQL database',
            'category': 'Database',
            'assigned_date': '2026-06-22',
            'due_date': '2026-06-25',
            'priority': 'High',
            'status': 'In Progress',
            'percent_done': 40,
            'assigned_by': 'manager',
            'notes': 'SQLite-to-Postgre transition.'
        },
        {
            'intern_name': 'masarapu bhuvan sai adithya',
            'task_name': 'Weekly Summary Aggregation',
            'category': 'Backend',
            'assigned_date': '2026-06-22',
            'due_date': '2026-06-24',
            'priority': 'Medium',
            'status': 'Not Started',
            'percent_done': 0,
            'assigned_by': 'manager',
            'notes': 'Build automated weekly summary.'
        }
    ])

    # Add mock skills log
    db.skills_log.insert_one({
        'intern_name': 'srikakula anirudh',
        'date_logged': '2026-06-22',
        'skill_tool': 'SQL Optimization',
        'category': 'SQL',
        'resource_course': 'LeetCode SQL 50',
        'hours_spent': 4.0,
        'proficiency_before': 2,
        'proficiency_after': 4,
        'certificate': 'No',
        'notes': 'Focused on joins and indexes.'
    })

    # Add mock mentor feedback
    db.mentor_feedback.insert_one({
        'intern_name': 'srikakula anirudh',
        'date_logged': '2026-06-22',
        'feedback_from': 'manager',
        'type': '1-on-1 Session',
        'feedback_summary': 'Great progress on backend schema. Recommended production ready config.',
        'area_to_improve': 'Gunicorn configuration details',
        'strength_noted': 'Independent research capabilities',
        'action_taken': 'Will add Gunicorn and requirements.txt',
        'follow_up': 'Yes',
        'follow_up_date': '2026-06-26'
    })

    client.close()
    print("Database seeded successfully in MongoDB Atlas!")

if __name__ == '__main__':
    seed()
