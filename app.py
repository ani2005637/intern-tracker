from flask import Flask, request, jsonify, send_from_directory, session
import pymongo
from bson import ObjectId
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import os
import datetime

app = Flask(__name__)

# Set secret key for sessions (secure default but customizable via environment)
app.secret_key = os.environ.get('SECRET_KEY', 'sanna_innovations_secret_key_129847')

# Enable CORS with credentials support so frontend can send/receive session cookies
CORS(app, supports_credentials=True)

# Connect to MongoDB
mongo_uri = os.environ.get('MONGO_URI')
if not mongo_uri:
    # Use default credentials provided by the user
    mongo_uri = 'mongodb+srv://srikakulaanirudh0506_db_user:e9gSM1PbSju6TYek@cluster0.3jbhs01.mongodb.net/?appName=Cluster0'

print("Connecting to MongoDB Atlas web service...")
client = pymongo.MongoClient(mongo_uri)
db = client['intern_tracker']

# Helper to serialize MongoDB documents (converting ObjectId to string 'id')
def serialize(doc):
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize(d) for d in doc]
    
    doc = dict(doc)
    if '_id' in doc:
        doc['id'] = str(doc['_id'])
        del doc['_id']
    return doc

# ----------------- AUTHENTICATION MIDDLEWARE HELPERS -----------------
def get_logged_in_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    try:
        user = db.users.find_one({"_id": ObjectId(user_id)})
        return user
    except Exception:
        return None


# ----------------- FRONTEND ROUTE -----------------
@app.route('/')
def serve_frontend():
    return send_from_directory('.', 'index.html')


# ----------------- AUTHENTICATION API ENDPOINTS -----------------
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    username = data.get('username', '').strip().lower()
    password = data.get('password', '')
    full_name = data.get('full_name', '').strip()
    role = data.get('role', 'Intern')  # 'Admin', 'Manager', 'Employee', 'Intern'

    if not username or not password or not full_name or not role:
        return jsonify({"error": "All fields are required"}), 400

    if role not in ['Admin', 'Manager', 'Employee', 'Intern']:
        return jsonify({"error": "Invalid role specified"}), 400

    # Check if username exists
    existing = db.users.find_one({"username": username})
    if existing:
        return jsonify({"error": "Username already taken"}), 400

    hashed_pw = generate_password_hash(password)
    try:
        db.users.insert_one({
            "username": username,
            "password_hash": hashed_pw,
            "full_name": full_name,
            "role": role,
            "created_at": datetime.datetime.utcnow()
        })
    except Exception as e:
        return jsonify({"error": f"Signup failed: {str(e)}"}), 500

    return jsonify({"message": "Registration successful!"}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    if not data:
        return jsonify({"error": "No credentials provided"}), 400

    username = data.get('username', '').strip().lower()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = db.users.find_one({"username": username})
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    if not check_password_hash(user['password_hash'], password):
        return jsonify({"error": "Invalid credentials"}), 401

    # Store user identity details inside the session
    session['user_id'] = str(user['_id'])
    session['username'] = user['username']
    session['role'] = user['role']
    session['full_name'] = user['full_name']

    return jsonify({
        "message": "Login successful!",
        "user": {
            "username": user['username'],
            "full_name": user['full_name'],
            "role": user['role']
        }
    })


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully!"})


@app.route('/current_user', methods=['GET'])
def current_user():
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({
        "username": user['username'],
        "full_name": user['full_name'],
        "role": user['role']
    })


# Fetch users list dynamically (useful for task assignment dropdowns)
@app.route('/users', methods=['GET'])
def get_users():
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    role_filter = request.args.get('role')
    query = {}
    if role_filter:
        query['role'] = role_filter

    users = list(db.users.find(query).sort("full_name", 1))
    return jsonify(serialize(users))


# ----------------- DAILY LOGS ROUTES (RBAC ENFORCED) -----------------
@app.route('/logs', methods=['GET'])
def get_logs():
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    # Interns and Employees can only see their own logs
    if user['role'] in ['Intern', 'Employee']:
        logs = list(db.intern_logs.find({"intern_name": user['username']}).sort("date_logged", -1))
    else:
        # Managers and Admins can see all logs
        logs = list(db.intern_logs.find({}).sort("date_logged", -1))
    
    return jsonify(serialize(logs))


@app.route('/submit', methods=['POST'])
def submit_log():
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Interns and Employees can only log for themselves. Admins/Managers can log on behalf of others.
    if user['role'] in ['Intern', 'Employee']:
        name = user['username']
    else:
        name = data.get('intern_name', user['username'])

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

    if not date or hours is None or not tasks:
        return jsonify({"error": "Missing required fields (date_logged, hours_worked, tasks_completed)"}), 400

    try:
        hours = float(hours)
        mood = int(mood)
    except ValueError:
        return jsonify({"error": "Invalid numeric format"}), 400

    try:
        db.intern_logs.insert_one({
            "intern_name": name,
            "date_logged": date,
            "check_in": check_in,
            "check_out": check_out,
            "hours_worked": hours,
            "task_category": task_category,
            "tasks_completed": tasks,
            "deliverable_completed": deliverable,
            "blockers": blockers,
            "skills_used": skills_used,
            "mood": mood,
            "notes": notes
        })
    except Exception as e:
        return jsonify({"error": f"Submission failed: {str(e)}"}), 500

    return jsonify({"message": "Daily log submitted successfully!"}), 201


# ----------------- TASKS ROUTES (RBAC ENFORCED) -----------------
@app.route('/tasks', methods=['GET'])
def get_tasks():
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    # Interns and Employees only see tasks assigned to them
    if user['role'] in ['Intern', 'Employee']:
        tasks = list(db.tasks.find({"intern_name": user['username']}).sort("due_date", 1))
    else:
        # Managers/Admins see all tasks
        tasks = list(db.tasks.find({}).sort("due_date", 1))
        
    return jsonify(serialize(tasks))


@app.route('/tasks', methods=['POST'])
def add_task():
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    # Interns cannot assign tasks
    if user['role'] == 'Intern':
        return jsonify({"error": "Interns cannot assign tasks"}), 403

    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    target_username = data.get('intern_name') # Target user to assign task
    task_name = data.get('task_name')
    category = data.get('category', '')
    assigned_date = data.get('assigned_date')
    due_date = data.get('due_date', '')
    priority = data.get('priority', 'Medium')
    status = data.get('status', 'Not Started')
    percent_done = data.get('percent_done', 0)
    notes = data.get('notes', '')

    if not target_username or not task_name or not assigned_date:
        return jsonify({"error": "Missing required fields (intern_name, task_name, assigned_date)"}), 400

    # Role check: Employees can ONLY assign tasks to Interns.
    target_user = db.users.find_one({"username": target_username})
    if not target_user:
        return jsonify({"error": "Target user not found"}), 404
        
    target_role = target_user['role']
    
    if user['role'] == 'Employee' and target_role != 'Intern':
        return jsonify({"error": "Employees can only assign tasks to Interns"}), 403

    try:
        db.tasks.insert_one({
            "intern_name": target_username,
            "task_name": task_name,
            "category": category,
            "assigned_date": assigned_date,
            "due_date": due_date,
            "priority": priority,
            "status": status,
            "percent_done": int(percent_done),
            "assigned_by": user['username'],
            "notes": notes
        })
    except Exception as e:
        return jsonify({"error": f"Task creation failed: {str(e)}"}), 500

    return jsonify({"message": "Task created successfully!"}), 201


@app.route('/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    status = data.get('status')
    percent_done = data.get('percent_done')
    completed_date = data.get('completed_date', '')
    notes = data.get('notes')

    try:
        task = db.tasks.find_one({"_id": ObjectId(task_id)})
    except Exception:
        return jsonify({"error": "Invalid task ID format"}), 400

    if not task:
        return jsonify({"error": "Task not found"}), 404
    
    # Access checks: Interns/Employees can only update tasks assigned to them
    if user['role'] in ['Intern', 'Employee'] and task['intern_name'] != user['username']:
        return jsonify({"error": "Forbidden: You cannot modify this task"}), 403

    update_fields = {}
    if status is not None:
        update_fields["status"] = status
        if status == 'Completed' and not completed_date:
            completed_date = datetime.date.today().isoformat()
            update_fields["completed_date"] = completed_date
    if percent_done is not None:
        try:
            update_fields["percent_done"] = int(percent_done)
        except ValueError:
            pass
    if completed_date is not None:
        update_fields["completed_date"] = completed_date
    if notes is not None:
        update_fields["notes"] = notes

    if update_fields:
        db.tasks.update_one({"_id": ObjectId(task_id)}, {"$set": update_fields})

    return jsonify({"message": "Task updated successfully!"})


@app.route('/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        task = db.tasks.find_one({"_id": ObjectId(task_id)})
    except Exception:
        return jsonify({"error": "Invalid task ID format"}), 400

    if not task:
        return jsonify({"error": "Task not found"}), 404
    
    # Interns cannot delete tasks.
    # Employees can only delete tasks if they created it.
    # Managers/Admins can delete any task.
    if user['role'] == 'Intern':
        return jsonify({"error": "Forbidden"}), 403
    elif user['role'] == 'Employee' and task['assigned_by'] != user['username']:
        return jsonify({"error": "Forbidden: You can only delete tasks you created"}), 403

    db.tasks.delete_one({"_id": ObjectId(task_id)})
    return jsonify({"message": "Task deleted successfully!"})


# ----------------- SKILLS ROUTES (RBAC ENFORCED) -----------------
@app.route('/skills', methods=['GET'])
def get_skills():
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    if user['role'] in ['Intern', 'Employee']:
        skills = list(db.skills_log.find({"intern_name": user['username']}).sort("date_logged", -1))
    else:
        skills = list(db.skills_log.find({}).sort("date_logged", -1))
        
    return jsonify(serialize(skills))


@app.route('/skills', methods=['POST'])
def add_skill():
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Interns/Employees log skills for themselves.
    if user['role'] in ['Intern', 'Employee']:
        name = user['username']
    else:
        name = data.get('intern_name', user['username'])

    date = data.get('date_logged')
    skill_tool = data.get('skill_tool')
    category = data.get('category', '')
    resource = data.get('resource_course', '')
    hours = data.get('hours_spent')
    prof_before = data.get('proficiency_before')
    prof_after = data.get('proficiency_after')
    certificate = data.get('certificate', 'No')
    notes = data.get('notes', '')

    if not date or not skill_tool or hours is None:
        return jsonify({"error": "Missing required fields (date_logged, skill_tool, hours_spent)"}), 400

    try:
        hours = float(hours)
        prof_before = int(prof_before) if prof_before is not None else None
        prof_after = int(prof_after) if prof_after is not None else None
    except ValueError:
        return jsonify({"error": "Invalid format"}), 400

    try:
        db.skills_log.insert_one({
            "intern_name": name,
            "date_logged": date,
            "skill_tool": skill_tool,
            "category": category,
            "resource_course": resource,
            "hours_spent": hours,
            "proficiency_before": prof_before,
            "proficiency_after": prof_after,
            "certificate": certificate,
            "notes": notes
        })
    except Exception as e:
        return jsonify({"error": f"Skill logging failed: {str(e)}"}), 500

    return jsonify({"message": "Skill logged successfully!"}), 201


# ----------------- MENTOR FEEDBACK ROUTES (RBAC ENFORCED) -----------------
@app.route('/feedback', methods=['GET'])
def get_feedback():
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    if user['role'] in ['Intern', 'Employee']:
        feedback = list(db.mentor_feedback.find({"intern_name": user['username']}).sort("date_logged", -1))
    else:
        feedback = list(db.mentor_feedback.find({}).sort("date_logged", -1))
        
    return jsonify(serialize(feedback))


@app.route('/feedback', methods=['POST'])
def add_feedback():
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    # Interns cannot log supervisor reviews.
    if user['role'] == 'Intern':
        return jsonify({"error": "Interns cannot log feedback reviews"}), 403

    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    target_username = data.get('intern_name') # Target user to receive feedback
    date = data.get('date_logged')
    feedback_type = data.get('type')
    summary = data.get('feedback_summary')
    area_improve = data.get('area_to_improve', '')
    strength = data.get('strength_noted', '')
    action = data.get('action_taken', '')
    follow_up = data.get('follow_up', 'No')
    follow_up_date = data.get('follow_up_date', '')

    if not target_username or not date or not feedback_type or not summary:
        return jsonify({"error": "Missing required fields (intern_name, date_logged, type, feedback_summary)"}), 400

    target_user = db.users.find_one({"username": target_username})
    if not target_user:
        return jsonify({"error": "Target user not found"}), 404
        
    target_role = target_user['role']

    # Employees can ONLY leave feedback for Interns
    if user['role'] == 'Employee' and target_role != 'Intern':
        return jsonify({"error": "Employees can only log feedback for Interns"}), 403

    try:
        db.mentor_feedback.insert_one({
            "intern_name": target_username,
            "date_logged": date,
            "feedback_from": user['username'],
            "type": feedback_type,
            "feedback_summary": summary,
            "area_to_improve": area_improve,
            "strength_noted": strength,
            "action_taken": action,
            "follow_up": follow_up,
            "follow_up_date": follow_up_date
        })
    except Exception as e:
        return jsonify({"error": f"Feedback submission failed: {str(e)}"}), 500

    return jsonify({"message": "Mentor feedback logged successfully!"}), 201


if __name__ == '__main__':
    app.run(debug=True, port=5000)
