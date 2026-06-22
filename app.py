from flask import Flask, request, jsonify, send_from_directory
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
# Enable CORS for all routes so the frontend can communicate with the backend
CORS(app)

# Serve the frontend
@app.route('/')
def serve_frontend():
    return send_from_directory('.', 'index.html')

# Helper function to connect to the database
def get_db_connection():
    conn = sqlite3.connect('tracker.db')
    conn.row_factory = sqlite3.Row  # Returns rows as dictionaries
    return conn

# Route 1: Receive data from the HTML form (POST)
@app.route('/submit', methods=['POST'])
def submit_log():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Extract data from the incoming request
    name = data.get('intern_name')
    date = data.get('date_logged')
    hours = data.get('hours_worked')
    tasks = data.get('tasks_completed')
    blockers = data.get('blockers', 'None')  # Default to 'None' if left blank

    # Simple validation
    if not name or not date or hours is None or not tasks:
        return jsonify({"error": "Missing required fields (intern_name, date_logged, hours_worked, tasks_completed)"}), 400

    try:
        hours = float(hours)
    except ValueError:
        return jsonify({"error": "Hours worked must be a number"}), 400

    # Insert into the SQL database
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO intern_logs (intern_name, date_logged, hours_worked, tasks_completed, blockers) VALUES (?, ?, ?, ?, ?)',
        (name, date, hours, tasks, blockers)
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Log submitted successfully!"}), 201

# Route 2: Send data to the manager's dashboard (GET)
@app.route('/logs', methods=['GET'])
def get_logs():
    conn = get_db_connection()
    logs = conn.execute('SELECT * FROM intern_logs ORDER BY date_logged DESC').fetchall()
    conn.close()

    # Convert the SQL rows into a list of dictionaries for the frontend
    logs_list = [dict(ix) for ix in logs]
    return jsonify(logs_list)

if __name__ == '__main__':
    # Running on port 5000 in debug mode
    app.run(debug=True, port=5000)
