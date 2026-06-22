from flask import Flask, request, jsonify, send_from_directory
import sqlite3
from flask_cors import CORS
import os

app = Flask(__name__)
# Enable CORS so our frontend can interact with the server easily
CORS(app)

# Helper function to connect to SQLite
def get_db_connection():
    conn = sqlite3.connect('tracker.db')
    conn.row_factory = sqlite3.Row  # Returns database rows as dict-like objects
    return conn

# ----------------- FRONTEND ROUTE -----------------
@app.route('/')
def serve_frontend():
    return send_from_directory('.', 'index.html')

# ----------------- DAILY LOGS ROUTE -----------------
@app.route('/logs', methods=['GET'])
def get_logs():
    conn = get_db_connection()
    logs = conn.execute('SELECT * FROM intern_logs ORDER BY date_logged DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in logs])

@app.route('/submit', methods=['POST'])
def submit_log():
    data = request.json
    if not data:
        return jsonify({"error": "No payload provided"}), 400

    name = data.get('intern_name')
    date = data.get('date_logged')
    check_in = data.get('check_in', '')
    check_out = data.get('check_out', '')
    hours = data.get('hours_worked')
    task_category = data.get('task_category', '')
    tasks = data.get('tasks_completed')
    deliverable = data.get('deliverable_completed', 'No')
    blockers = data.get('blockers', 'None')
    skills_used = data.get('skills_used', '')
    mood = data.get('mood', 5)
    notes = data.get('notes', '')

    if not name or not date or hours is None or not tasks:
        return jsonify({"error": "Missing required fields (intern_name, date_logged, hours_worked, tasks_completed)"}), 400

    try:
        hours = float(hours)
        mood = int(mood)
    except ValueError:
        return jsonify({"error": "Invalid numeric format for hours or mood"}), 400

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO intern_logs (
            intern_name, date_logged, check_in, check_out, hours_worked,
            task_category, tasks_completed, deliverable_completed, blockers,
            skills_used, mood, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, date, check_in, check_out, hours, task_category, tasks, deliverable, blockers, skills_used, mood, notes))
    conn.commit()
    conn.close()

    return jsonify({"message": "Daily log submitted successfully!"}), 201


# ----------------- TASKS / PROJECT TRACKER ROUTES -----------------
@app.route('/tasks', methods=['GET'])
def get_tasks():
    conn = get_db_connection()
    tasks = conn.execute('SELECT * FROM tasks ORDER BY due_date ASC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in tasks])

@app.route('/tasks', methods=['POST'])
def add_task():
    data = request.json
    if not data:
        return jsonify({"error": "No payload provided"}), 400

    name = data.get('intern_name')
    task_name = data.get('task_name')
    category = data.get('category', '')
    assigned_date = data.get('assigned_date')
    due_date = data.get('due_date', '')
    priority = data.get('priority', 'Medium')
    status = data.get('status', 'Not Started')
    percent_done = data.get('percent_done', 0)
    assigned_by = data.get('assigned_by', '')
    notes = data.get('notes', '')

    if not name or not task_name or not assigned_date:
        return jsonify({"error": "Missing required fields (intern_name, task_name, assigned_date)"}), 400

    try:
        percent_done = int(percent_done)
    except ValueError:
        percent_done = 0

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO tasks (
            intern_name, task_name, category, assigned_date, due_date,
            priority, status, percent_done, assigned_by, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, task_name, category, assigned_date, due_date, priority, status, percent_done, assigned_by, notes))
    conn.commit()
    conn.close()

    return jsonify({"message": "Task created successfully!"}), 201

@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.json
    if not data:
        return jsonify({"error": "No payload provided"}), 400

    status = data.get('status')
    percent_done = data.get('percent_done')
    completed_date = data.get('completed_date', '')
    notes = data.get('notes')

    conn = get_db_connection()
    task = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
    if not task:
        conn.close()
        return jsonify({"error": "Task not found"}), 404

    # Dynamically build update query
    updates = []
    params = []
    if status is not None:
        updates.append("status = ?")
        params.append(status)
        # If marked completed and completed_date is empty, default to today
        if status == 'Completed' and not completed_date:
            import datetime
            completed_date = datetime.date.today().isoformat()
            updates.append("completed_date = ?")
            params.append(completed_date)
    if percent_done is not None:
        try:
            updates.append("percent_done = ?")
            params.append(int(percent_done))
        except ValueError:
            pass
    if completed_date is not None:
        updates.append("completed_date = ?")
        params.append(completed_date)
    if notes is not None:
        updates.append("notes = ?")
        params.append(notes)

    if updates:
        params.append(task_id)
        conn.execute(f'UPDATE tasks SET {", ".join(updates)} WHERE id = ?', params)
        conn.commit()

    conn.close()
    return jsonify({"message": "Task updated successfully!"})

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    conn = get_db_connection()
    task = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
    if not task:
        conn.close()
        return jsonify({"error": "Task not found"}), 404

    conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Task deleted successfully!"})


# ----------------- SKILLS LOG ROUTES -----------------
@app.route('/skills', methods=['GET'])
def get_skills():
    conn = get_db_connection()
    skills = conn.execute('SELECT * FROM skills_log ORDER BY date_logged DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in skills])

@app.route('/skills', methods=['POST'])
def add_skill():
    data = request.json
    if not data:
        return jsonify({"error": "No payload provided"}), 400

    name = data.get('intern_name')
    date = data.get('date_logged')
    skill_tool = data.get('skill_tool')
    category = data.get('category', '')
    resource = data.get('resource_course', '')
    hours = data.get('hours_spent')
    prof_before = data.get('proficiency_before')
    prof_after = data.get('proficiency_after')
    certificate = data.get('certificate', 'No')
    notes = data.get('notes', '')

    if not name or not date or not skill_tool or hours is None:
        return jsonify({"error": "Missing required fields (intern_name, date_logged, skill_tool, hours_spent)"}), 400

    try:
        hours = float(hours)
        prof_before = int(prof_before) if prof_before is not None else None
        prof_after = int(prof_after) if prof_after is not None else None
    except ValueError:
        return jsonify({"error": "Invalid format for hours or proficiency levels"}), 400

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO skills_log (
            intern_name, date_logged, skill_tool, category, resource_course,
            hours_spent, proficiency_before, proficiency_after, certificate, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, date, skill_tool, category, resource, hours, prof_before, prof_after, certificate, notes))
    conn.commit()
    conn.close()

    return jsonify({"message": "Skill logged successfully!"}), 201


# ----------------- MENTOR FEEDBACK ROUTES -----------------
@app.route('/feedback', methods=['GET'])
def get_feedback():
    conn = get_db_connection()
    feedbacks = conn.execute('SELECT * FROM mentor_feedback ORDER BY date_logged DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in feedbacks])

@app.route('/feedback', methods=['POST'])
def add_feedback():
    data = request.json
    if not data:
        return jsonify({"error": "No payload provided"}), 400

    name = data.get('intern_name')
    date = data.get('date_logged')
    feedback_from = data.get('feedback_from')
    feedback_type = data.get('type')
    summary = data.get('feedback_summary')
    area_improve = data.get('area_to_improve', '')
    strength = data.get('strength_noted', '')
    action = data.get('action_taken', '')
    follow_up = data.get('follow_up', 'No')
    follow_up_date = data.get('follow_up_date', '')

    if not name or not date or not feedback_from or not feedback_type or not summary:
        return jsonify({"error": "Missing required fields (intern_name, date_logged, feedback_from, type, feedback_summary)"}), 400

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO mentor_feedback (
            intern_name, date_logged, feedback_from, type, feedback_summary,
            area_to_improve, strength_noted, action_taken, follow_up, follow_up_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, date, feedback_from, feedback_type, summary, area_improve, strength, action, follow_up, follow_up_date))
    conn.commit()
    conn.close()

    return jsonify({"message": "Mentor feedback logged successfully!"}), 201


if __name__ == '__main__':
    app.run(debug=True, port=5000)
