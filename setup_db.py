import sqlite3

def init_db():
    conn = sqlite3.connect('tracker.db')
    cursor = conn.cursor()

    # Drop existing tables to recreate them with the new schemas cleanly
    cursor.execute("DROP TABLE IF EXISTS intern_logs")
    cursor.execute("DROP TABLE IF EXISTS tasks")
    cursor.execute("DROP TABLE IF EXISTS skills_log")
    cursor.execute("DROP TABLE IF EXISTS mentor_feedback")

    # 1. Create the expanded intern logs table
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

    # 2. Create the tasks table
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

    # 3. Create the skills log table
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

    # 4. Create the mentor feedback table
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
    print("Database expanded and tables created successfully!")

if __name__ == '__main__':
    init_db()
