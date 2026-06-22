import sqlite3
import os

def init_db():
    db_url = os.environ.get('DATABASE_URL')
    
    if db_url:
        print("Connecting to cloud PostgreSQL database...")
        import psycopg2
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # PostgreSQL Drop Tables
        cursor.execute("DROP TABLE IF EXISTS intern_logs CASCADE")
        cursor.execute("DROP TABLE IF EXISTS tasks CASCADE")
        cursor.execute("DROP TABLE IF EXISTS skills_log CASCADE")
        cursor.execute("DROP TABLE IF EXISTS mentor_feedback CASCADE")
        
        # PostgreSQL Create Tables
        cursor.execute('''
            CREATE TABLE intern_logs (
                id SERIAL PRIMARY KEY,
                intern_name VARCHAR(255) NOT NULL,
                date_logged VARCHAR(50) NOT NULL,
                check_in VARCHAR(50),
                check_out VARCHAR(50),
                hours_worked REAL NOT NULL,
                task_category VARCHAR(255),
                tasks_completed TEXT NOT NULL,
                deliverable_completed VARCHAR(50),
                blockers TEXT,
                skills_used TEXT,
                mood INTEGER,
                notes TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE tasks (
                id SERIAL PRIMARY KEY,
                intern_name VARCHAR(255) NOT NULL,
                task_name VARCHAR(255) NOT NULL,
                category VARCHAR(255),
                assigned_date VARCHAR(50) NOT NULL,
                due_date VARCHAR(50),
                completed_date VARCHAR(50),
                priority VARCHAR(50),
                status VARCHAR(50) NOT NULL,
                percent_done INTEGER DEFAULT 0,
                assigned_by VARCHAR(255),
                notes TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE skills_log (
                id SERIAL PRIMARY KEY,
                intern_name VARCHAR(255) NOT NULL,
                date_logged VARCHAR(50) NOT NULL,
                skill_tool VARCHAR(255) NOT NULL,
                category VARCHAR(255),
                resource_course VARCHAR(255),
                hours_spent REAL NOT NULL,
                proficiency_before INTEGER,
                proficiency_after INTEGER,
                certificate VARCHAR(50),
                notes TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE mentor_feedback (
                id SERIAL PRIMARY KEY,
                intern_name VARCHAR(255) NOT NULL,
                date_logged VARCHAR(50) NOT NULL,
                feedback_from VARCHAR(255) NOT NULL,
                type VARCHAR(255) NOT NULL,
                feedback_summary TEXT NOT NULL,
                area_to_improve TEXT,
                strength_noted TEXT,
                action_taken TEXT,
                follow_up VARCHAR(50),
                follow_up_date VARCHAR(50)
            )
        ''')
        
    else:
        print("Connecting to local SQLite database...")
        conn = sqlite3.connect('tracker.db')
        cursor = conn.cursor()
        
        cursor.execute("DROP TABLE IF EXISTS intern_logs")
        cursor.execute("DROP TABLE IF EXISTS tasks")
        cursor.execute("DROP TABLE IF EXISTS skills_log")
        cursor.execute("DROP TABLE IF EXISTS mentor_feedback")
        
        cursor.execute('''
            CREATE TABLE intern_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                intern_name TEXT NOT NULL,
                date_logged TEXT NOT NULL,
                check_in TEXT,
                check_out TEXT,
                hours_worked REAL NOT NULL,
                task_category TEXT,
                tasks_completed TEXT NOT NULL,
                deliverable_completed TEXT,
                blockers TEXT,
                skills_used TEXT,
                mood INTEGER,
                notes TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                intern_name TEXT NOT NULL,
                task_name TEXT NOT NULL,
                category TEXT,
                assigned_date TEXT NOT NULL,
                due_date TEXT,
                completed_date TEXT,
                priority TEXT,
                status TEXT NOT NULL,
                percent_done INTEGER DEFAULT 0,
                assigned_by TEXT,
                notes TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE skills_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                intern_name TEXT NOT NULL,
                date_logged TEXT NOT NULL,
                skill_tool TEXT NOT NULL,
                category TEXT,
                resource_course TEXT,
                hours_spent REAL NOT NULL,
                proficiency_before INTEGER,
                proficiency_after INTEGER,
                certificate TEXT,
                notes TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE mentor_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                intern_name TEXT NOT NULL,
                date_logged TEXT NOT NULL,
                feedback_from TEXT NOT NULL,
                type TEXT NOT NULL,
                feedback_summary TEXT NOT NULL,
                area_to_improve TEXT,
                strength_noted TEXT,
                action_taken TEXT,
                follow_up TEXT,
                follow_up_date TEXT
            )
        ''')

    conn.commit()
    conn.close()
    print("Database tables created successfully!")

if __name__ == '__main__':
    init_db()
