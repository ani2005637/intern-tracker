import sqlite3

def init_db():
    # Connect to SQLite (creates 'tracker.db' if it doesn't exist)
    conn = sqlite3.connect('tracker.db')
    cursor = conn.cursor()

    # Create the intern logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS intern_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intern_name TEXT NOT NULL,
            date_logged TEXT NOT NULL,
            hours_worked REAL NOT NULL,
            tasks_completed TEXT NOT NULL,
            blockers TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("Database and 'intern_logs' table created successfully!")

if __name__ == '__main__':
    init_db()
