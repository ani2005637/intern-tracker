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

# Create indexes for high-performance data retrieval
print("Ensuring database indexes exist for fast loading...")
try:
    db.session_logs.create_index([("username", pymongo.ASCENDING), ("login_time", pymongo.DESCENDING)])
    db.tasks.create_index([("intern_name", pymongo.ASCENDING)])
    db.tasks.create_index([("assigned_by", pymongo.ASCENDING)])
    db.intern_logs.create_index([("intern_name", pymongo.ASCENDING), ("date_logged", pymongo.DESCENDING)])
    db.skills_log.create_index([("intern_name", pymongo.ASCENDING)])
    db.mentor_feedback.create_index([("intern_name", pymongo.ASCENDING)])
    db.notifications.create_index([("username", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)])
    db.announcements.create_index([("created_at", pymongo.DESCENDING)])
    db.direct_messages.create_index([("sender", pymongo.ASCENDING), ("recipient", pymongo.ASCENDING), ("created_at", pymongo.ASCENDING)])
    db.direct_messages.create_index([("recipient", pymongo.ASCENDING), ("created_at", pymongo.ASCENDING)])
    print("Database indexes created/verified.")
except Exception as ie:
    print(f"Warning: Failed to ensure database indexes: {ie}")

# Startup migration to ensure all existing users have 'approved: True' and 'restricted: False'
try:
    print("Running startup migration to approve existing users and initialize restriction state...")
    db.users.update_many({"approved": {"$exists": False}}, {"$set": {"approved": True}})
    db.users.update_many({"restricted": {"$exists": False}}, {"$set": {"restricted": False}})
    print("Startup migration completed successfully.")
except Exception as me:
    print(f"Warning: Startup migration failed: {me}")

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

def validate_log_date(date_str):
    if not date_str:
        return "Log date is required"
    try:
        log_dt = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        today_dt = datetime.date.today()
        yesterday_dt = today_dt - datetime.timedelta(days=1)
        if log_dt < yesterday_dt or log_dt > today_dt:
            return "Daily log date must be yesterday or today."
    except ValueError:
        return "Invalid log date format. Expected YYYY-MM-DD"
    return None

def validate_future_or_today_date(date_str, field_name):
    if not date_str:
        return None
    try:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        today_dt = datetime.date.today()
        if dt < today_dt:
            return f"{field_name} cannot be in the past"
    except ValueError:
        return f"Invalid {field_name} format. Expected YYYY-MM-DD"
    return None

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

# Helper to find usernames of all subordinate users (strict hierarchical access)
def get_subordinate_usernames(user):
    role_weights = {"Intern": 1, "Employee": 2, "Manager": 3, "Admin": 4}
    user_weight = role_weights.get(user['role'], 0)
    
    if user['role'] in ['Admin', 'Guest']:
        return None
        
    # Find all roles with a weight strictly lower than user's weight
    sub_roles = [role for role, weight in role_weights.items() if weight < user_weight]
    
    # Query usernames of those roles
    sub_users = list(db.users.find({"role": {"$in": sub_roles}}, {"username": 1}))
    sub_usernames = [u['username'] for u in sub_users]
    
    # Always include the user's own username so they can see their own data
    sub_usernames.append(user['username'])
    return sub_usernames


@app.before_request
def restrict_guest_writes():
    if request.method in ['POST', 'PUT', 'DELETE']:
        if request.path in ['/login', '/logout', '/signup']:
            return None
        user = get_logged_in_user()
        if user and user.get('role') == 'Guest':
            return jsonify({"error": "Forbidden: Guest account is read-only"}), 403
    return None


# ----------------- FRONTEND ROUTE -----------------
@app.route('/')
def serve_frontend():
    response = send_from_directory('.', 'index.html')
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


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
    email = data.get('email', '').strip()
    title = data.get('title', '').strip()

    if not username or not password or not full_name or not role or not email or not title:
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
            "email": email,
            "title": title,
            "approved": False,
            "created_at": datetime.datetime.utcnow()
        })
        
        # Notify all Admin users about the new pending registration
        try:
            admins = list(db.users.find({"role": "Admin"}))
            for admin_user in admins:
                db.notifications.insert_one({
                    "username": admin_user['username'],
                    "message": f"New registration pending approval: {full_name} ({role})",
                    "type": "registration_pending",
                    "created_at": datetime.datetime.utcnow(),
                    "read": False
                })
        except Exception as ne:
            print(f"Failed to create admin notification on signup: {ne}")
            
    except Exception as e:
        return jsonify({"error": f"Signup failed: {str(e)}"}), 500

    return jsonify({"message": "Registration successful! Your account is pending administrator approval."}), 201

@app.route('/users/create', methods=['POST'])
def create_user_by_supervisor():
    user = get_logged_in_user()
    if not user or user['role'] not in ['Admin', 'Manager']:
        return jsonify({"error": "Unauthorized: Access denied"}), 401
        
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    username = data.get('username', '').strip().lower()
    password = data.get('password', '')
    full_name = data.get('full_name', '').strip()
    role = data.get('role', '').strip()
    email = data.get('email', '').strip()
    title = data.get('title', '').strip()

    if not username or not password or not full_name or not role or not email or not title:
        return jsonify({"error": "All fields are required"}), 400

    if role not in ['Admin', 'Manager', 'Employee', 'Intern', 'Guest']:
        return jsonify({"error": "Invalid role specified"}), 400

    # Hierarchical role check
    if user['role'] == 'Manager' and role not in ['Employee', 'Intern']:
        return jsonify({"error": "Forbidden: Managers can only create Employee or Intern accounts"}), 403

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
            "email": email,
            "title": title,
            "approved": True, # Pre-approved since created by supervisor
            "restricted": False,
            "created_at": datetime.datetime.utcnow()
        })
        return jsonify({"message": f"Successfully created user account for {full_name} ({role})!"}), 201
    except Exception as e:
        return jsonify({"error": f"Failed to create user: {str(e)}"}), 500


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

    # Check if user account is approved
    if not user.get('approved', False):
        return jsonify({"error": "Your account is pending administrator approval. Please contact an admin."}), 403

    # Check if user account is restricted
    if user.get('restricted', False):
        return jsonify({"error": "Your account has been temporarily restricted by an administrator or manager. Please contact support."}), 403

    # Store user identity details inside the session
    session['user_id'] = str(user['_id'])
    session['username'] = user['username']
    session['role'] = user['role']
    session['full_name'] = user['full_name']

    # Close any orphaned active sessions for this user
    try:
        db.session_logs.update_many(
            {"username": user['username'], "logout_time": None},
            {"$set": {"logout_time": datetime.datetime.utcnow()}}
        )
    except Exception as e:
        print(f"Failed to close orphaned sessions: {e}")

    # Record login activity log
    try:
        db.session_logs.insert_one({
            "username": user['username'],
            "full_name": user['full_name'],
            "role": user['role'],
            "login_time": datetime.datetime.utcnow(),
            "logout_time": None
        })
    except Exception as e:
        print(f"Failed to record login session: {e}")

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
    user = get_logged_in_user()
    if user:
        try:
            # Close all active open sessions for this user
            res = db.session_logs.update_many(
                {"username": user['username'], "logout_time": None},
                {"$set": {"logout_time": datetime.datetime.utcnow()}}
            )
            # If no sessions were modified, fallback to updating the latest session's logout time
            if res.modified_count == 0:
                latest_any = db.session_logs.find_one(
                    {"username": user['username']},
                    sort=[("login_time", pymongo.DESCENDING)]
                )
                if latest_any:
                    db.session_logs.update_one(
                        {"_id": latest_any["_id"]},
                        {"$set": {"logout_time": datetime.datetime.utcnow()}}
                    )
        except Exception as e:
            print(f"Failed to record logout session: {e}")

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
        "role": user['role'],
        "email": user.get('email', ''),
        "title": user.get('title', '')
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

    # Fetch users
    users = list(db.users.find(query).sort("full_name", 1))
    
    # Optimize N+1 query: Fetch the latest session for all users in a single aggregation query
    try:
        pipeline = [
            {"$sort": {"login_time": -1}},
            {"$group": {
                "_id": "$username",
                "login_time": {"$first": "$login_time"},
                "logout_time": {"$first": "$logout_time"}
            }}
        ]
        sessions = {s["_id"]: s for s in db.session_logs.aggregate(pipeline)}
    except Exception as ae:
        print(f"Warning: Session aggregation failed: {ae}")
        sessions = {}

    for u in users:
        latest_session = sessions.get(u['username'])
        if latest_session:
            u['last_login'] = latest_session.get('login_time')
            u['last_logout'] = latest_session.get('logout_time')
            if latest_session.get("logout_time") is None:
                u['status'] = "Available"
            else:
                u['status'] = "Logged Out"
        else:
            u['last_login'] = None
            u['last_logout'] = None
            u['status'] = "Logged Out"

    return jsonify(serialize(users))


@app.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    if user['role'] not in ['Admin', 'Manager']:
        return jsonify({"error": "Forbidden: Only Admins and Managers can remove users"}), 403

    try:
        target_user = db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return jsonify({"error": "Invalid user ID format"}), 400

    if not target_user:
        return jsonify({"error": "User not found"}), 404

    # Prevent self-deletion
    if str(target_user['_id']) == str(user['_id']):
        return jsonify({"error": "You cannot remove yourself from the portal"}), 400

    role_weights = {
        "Intern": 1,
        "Employee": 2,
        "Manager": 3,
        "Admin": 4
    }

    user_weight = role_weights.get(user['role'], 0)
    target_weight = role_weights.get(target_user['role'], 0)

    # Enforce hierarchical access control: Rank(A) > Rank(B) (Bypassed for Admin)
    if user['role'] != 'Admin' and user_weight <= target_weight:
        return jsonify({"error": "Forbidden: You can only remove users with a lower role rank than yours"}), 403

    try:
        # Delete user
        db.users.delete_one({"_id": ObjectId(user_id)})
        
        # Cascade delete target user's records
        db.intern_logs.delete_many({"intern_name": target_user['username']})
        db.tasks.delete_many({"intern_name": target_user['username']})
        db.skills_log.delete_many({"intern_name": target_user['username']})
        db.mentor_feedback.delete_many({"intern_name": target_user['username']})
        
    except Exception as e:
        return jsonify({"error": f"Failed to remove user: {str(e)}"}), 500

    return jsonify({"message": f"User {target_user['full_name']} removed successfully!"})


# ----------------- DAILY LOGS ROUTES (RBAC ENFORCED) -----------------
@app.route('/logs', methods=['GET'])
def get_logs():
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    subs = get_subordinate_usernames(user)
    if subs is None:
        # Admins see everyone's logs
        logs = list(db.intern_logs.find({}).sort("date_logged", -1))
    else:
        # Others see own logs + logs of subordinates
        logs = list(db.intern_logs.find({"intern_name": {"$in": subs}}).sort("date_logged", -1))
    
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

    date_err = validate_log_date(date)
    if date_err:
        return jsonify({"error": date_err}), 400

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


@app.route('/logs/<log_id>', methods=['PUT'])
def update_log(log_id):
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        log = db.intern_logs.find_one({"_id": ObjectId(log_id)})
    except Exception:
        return jsonify({"error": "Invalid log ID format"}), 400

    if not log:
        return jsonify({"error": "Daily log not found"}), 404

    # Interns/Employees can only update their own logs. Managers/Admins can update any log.
    if user['role'] in ['Intern', 'Employee'] and log['intern_name'] != user['username']:
        return jsonify({"error": "Forbidden: You cannot modify this log"}), 403

    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    date = data.get('date_logged')
    check_in = data.get('check_in', '')
    check_out = data.get('check_out', '')
    hours = data.get('hours_worked')
    task_category = data.get('task_category', '')
    tasks = data.get('tasks_completed')
    deliverable = data.get('deliverable_completed', 'No')
    blockers = data.get('blockers', 'None')
    skills_used = data.get('skills_used', '')
    mood = data.get('mood')
    notes = data.get('notes', '')

    if not date or hours is None or not tasks:
        return jsonify({"error": "Missing required fields (date_logged, hours_worked, tasks_completed)"}), 400

    date_err = validate_log_date(date)
    if date_err:
        return jsonify({"error": date_err}), 400

    try:
        hours = float(hours)
        mood = int(mood) if mood is not None else 5
    except ValueError:
        return jsonify({"error": "Invalid numeric format"}), 400

    update_fields = {
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
    }

    # If Admin/Manager is editing, they can also update the intern_name if it was supplied
    if user['role'] not in ['Intern', 'Employee'] and 'intern_name' in data:
        update_fields["intern_name"] = data.get('intern_name')

    db.intern_logs.update_one({"_id": ObjectId(log_id)}, {"$set": update_fields})
    return jsonify({"message": "Daily log updated successfully!"})


@app.route('/logs/<log_id>', methods=['DELETE'])
def delete_log(log_id):
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        log = db.intern_logs.find_one({"_id": ObjectId(log_id)})
    except Exception:
        return jsonify({"error": "Invalid log ID format"}), 400

    if not log:
        return jsonify({"error": "Daily log not found"}), 404

    # Interns/Employees can only delete their own logs. Managers/Admins can delete any log.
    if user['role'] in ['Intern', 'Employee'] and log['intern_name'] != user['username']:
        return jsonify({"error": "Forbidden: You cannot delete this log"}), 403

    db.intern_logs.delete_one({"_id": ObjectId(log_id)})
    return jsonify({"message": "Daily log deleted successfully!"})


# ----------------- TASKS ROUTES (RBAC ENFORCED) -----------------
@app.route('/tasks', methods=['GET'])
def get_tasks():
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    subs = get_subordinate_usernames(user)
    if subs is None:
        # Admins see everyone's tasks
        tasks = list(db.tasks.find({}).sort("due_date", 1))
    else:
        # Others see own tasks + tasks of subordinates
        tasks = list(db.tasks.find({"intern_name": {"$in": subs}}).sort("due_date", 1))
        
    return jsonify(serialize(tasks))


@app.route('/tasks', methods=['POST'])
def add_task():
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    # Validation of target user and role permissions
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

    due_date_err = validate_future_or_today_date(due_date, "Due date")
    if due_date_err:
        return jsonify({"error": due_date_err}), 400

    target_user = db.users.find_one({"username": target_username})
    if not target_user:
        return jsonify({"error": "Target user not found"}), 404
        
    target_role = target_user['role']
    
    # Enforce role rules:
    # 1. Intern can only assign tasks to themselves
    if user['role'] == 'Intern' and target_username != user['username']:
        return jsonify({"error": "Forbidden: Interns can only assign tasks to themselves"}), 403

    # 2. Employee can only assign tasks to themselves or Interns
    if user['role'] == 'Employee' and target_username != user['username'] and target_role != 'Intern':
        return jsonify({"error": "Forbidden: Employees can only assign tasks to themselves or Interns"}), 403

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
            "notes": notes,
            "started_at": None,
            "completed_at": None
        })
        
        # Create notification for target user (suppressed if self-assigned)
        if target_username != user['username']:
            try:
                db.notifications.insert_one({
                    "username": target_username,
                    "message": f"New task assigned by {user['full_name']}: '{task_name}'",
                    "type": "task_assignment",
                    "created_at": datetime.datetime.utcnow(),
                    "read": False
                })
            except Exception as ne:
                print(f"Failed to create notification: {ne}")
            
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
        
        # Track start time when moved to In Progress
        if status == 'In Progress' and not task.get('started_at'):
            update_fields["started_at"] = datetime.datetime.utcnow().isoformat() + 'Z'
            
        # Track completion time when moved to Completed
        if status == 'Completed':
            if not task.get('completed_at'):
                update_fields["completed_at"] = datetime.datetime.utcnow().isoformat() + 'Z'
            if not task.get('completed_date'):
                update_fields["completed_date"] = datetime.date.today().isoformat()
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

    subs = get_subordinate_usernames(user)
    if subs is None:
        # Admins see everyone's skills
        skills = list(db.skills_log.find({}).sort("date_logged", -1))
    else:
        # Others see own skills + skills of subordinates
        skills = list(db.skills_log.find({"intern_name": {"$in": subs}}).sort("date_logged", -1))
        
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

    subs = get_subordinate_usernames(user)
    if subs is None:
        # Admins see everyone's feedback reviews
        feedback = list(db.mentor_feedback.find({}).sort("date_logged", -1))
    else:
        # Others see reviews written for/by them, or written for subordinates
        feedback = list(db.mentor_feedback.find({
            "$or": [
                {"intern_name": {"$in": subs}},
                {"feedback_from": user['username']}
            ]
        }).sort("date_logged", -1))
        
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

    follow_up_err = validate_future_or_today_date(follow_up_date, "Follow-up date")
    if follow_up_err:
        return jsonify({"error": follow_up_err}), 400

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


# ----------------- NOTIFICATIONS API ENDPOINTS -----------------
@app.route('/notifications', methods=['GET'])
def get_notifications():
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    notifications = list(db.notifications.find({"username": user['username']}).sort("created_at", -1).limit(20))
    return jsonify(serialize(notifications))


@app.route('/notifications/read', methods=['POST'])
def mark_all_notifications_read():
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    db.notifications.update_many(
        {"username": user['username'], "read": False},
        {"$set": {"read": True}}
    )
    return jsonify({"message": "All notifications marked as read"})


@app.route('/notifications/<notif_id>/read', methods=['POST'])
def mark_notification_read(notif_id):
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        db.notifications.update_one(
            {"_id": ObjectId(notif_id), "username": user['username']},
            {"$set": {"read": True}}
        )
    except Exception:
        return jsonify({"error": "Invalid notification ID"}), 400
        
    return jsonify({"message": "Notification marked as read"})


# ----------------- USER MANAGEMENT: UPDATE ROLE (Admin Only) -----------------
@app.route('/users/<user_id>/role', methods=['PUT'])
def update_user_role(user_id):
    user = get_logged_in_user()
    if not user or user['role'] != 'Admin':
        return jsonify({"error": "Unauthorized: Only Admins can modify roles"}), 401
    
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    new_role = data.get('role')
    if new_role not in ['Admin', 'Manager', 'Employee', 'Intern']:
        return jsonify({"error": "Invalid role"}), 400
        
    try:
        target_user = db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return jsonify({"error": "Invalid user ID format"}), 400
        
    if not target_user:
        return jsonify({"error": "User not found"}), 404
        
    # Prevent changing the role of oneself (prevents admin locking themselves out)
    if str(target_user['_id']) == str(user['_id']):
        return jsonify({"error": "You cannot change your own role to prevent lockout"}), 400
        
    # Prevent changing the role of the primary admin
    if target_user['username'] == 'admin':
        return jsonify({"error": "You cannot change the role of the primary administrator"}), 400
        
    db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"role": new_role}})
    return jsonify({"message": f"User {target_user['full_name']} role updated to {new_role}!"})


# ----------------- USER MANAGEMENT: APPROVE USER (Admin Only) -----------------
@app.route('/users/<user_id>/approve', methods=['PUT'])
def approve_user(user_id):
    user = get_logged_in_user()
    if not user or user['role'] != 'Admin':
        return jsonify({"error": "Unauthorized: Only Admins can approve users"}), 401
        
    try:
        target_user = db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return jsonify({"error": "Invalid user ID format"}), 400
        
    if not target_user:
        return jsonify({"error": "User not found"}), 404
        
    db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"approved": True}})
    
    # Create notification for target user
    try:
        db.notifications.insert_one({
            "username": target_user['username'],
            "message": "Your account has been approved by the Admin! You can now log in.",
            "type": "account_approved",
            "created_at": datetime.datetime.utcnow(),
            "read": False
        })
    except Exception as ne:
        print(f"Failed to create approval notification: {ne}")
        
    return jsonify({"message": f"User {target_user['full_name']} has been approved successfully!"})


# ----------------- USER MANAGEMENT: RESTRICT USER (Admin & Manager) -----------------
@app.route('/users/<user_id>/restrict', methods=['PUT'])
def restrict_user(user_id):
    user = get_logged_in_user()
    if not user or user['role'] not in ['Admin', 'Manager']:
        return jsonify({"error": "Unauthorized: Access denied"}), 401
        
    try:
        target_user = db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return jsonify({"error": "Invalid user ID format"}), 400
        
    if not target_user:
        return jsonify({"error": "User not found"}), 404
        
    # Prevent self-restriction
    if str(target_user['_id']) == str(user['_id']):
        return jsonify({"error": "You cannot restrict yourself"}), 400
        
    role_weights = {"Intern": 1, "Employee": 2, "Manager": 3, "Admin": 4}
    user_weight = role_weights.get(user['role'], 0)
    target_weight = role_weights.get(target_user['role'], 0)
    
    # Enforce hierarchical access control: Rank(A) > Rank(B) (Bypassed for Admin)
    if user['role'] != 'Admin' and user_weight <= target_weight:
        return jsonify({"error": "Forbidden: You can only restrict users with a lower rank than yours"}), 403
        
    db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"restricted": True}})
    
    # Create notification for target user
    try:
        db.notifications.insert_one({
            "username": target_user['username'],
            "message": "Your account has been temporarily restricted by an administrator or manager. Please contact support.",
            "type": "account_restricted",
            "created_at": datetime.datetime.utcnow(),
            "read": False
        })
    except Exception as ne:
        print(f"Failed to create restriction notification: {ne}")
        
    return jsonify({"message": f"User {target_user['full_name']} has been restricted successfully!"})


# ----------------- USER MANAGEMENT: UNRESTRICT USER (Admin & Manager) -----------------
@app.route('/users/<user_id>/unrestrict', methods=['PUT'])
def unrestrict_user(user_id):
    user = get_logged_in_user()
    if not user or user['role'] not in ['Admin', 'Manager']:
        return jsonify({"error": "Unauthorized: Access denied"}), 401
        
    try:
        target_user = db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return jsonify({"error": "Invalid user ID format"}), 400
        
    if not target_user:
        return jsonify({"error": "User not found"}), 404
        
    role_weights = {"Intern": 1, "Employee": 2, "Manager": 3, "Admin": 4}
    user_weight = role_weights.get(user['role'], 0)
    target_weight = role_weights.get(target_user['role'], 0)
    
    # Enforce hierarchical access control: Rank(A) > Rank(B) (Bypassed for Admin)
    if user['role'] != 'Admin' and user_weight <= target_weight:
        return jsonify({"error": "Forbidden: You can only unrestrict users with a lower rank than yours"}), 403
        
    db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"restricted": False}})
    
    # Create notification for target user
    try:
        db.notifications.insert_one({
            "username": target_user['username'],
            "message": "Your restriction has been lifted! You can now log in and log hours again.",
            "type": "account_unrestricted",
            "created_at": datetime.datetime.utcnow(),
            "read": False
        })
    except Exception as ne:
        print(f"Failed to create unrestriction notification: {ne}")
        
    return jsonify({"message": f"User {target_user['full_name']} restriction lifted successfully!"})


# ----------------- SESSION LOGS API ENDPOINT (Admin & Manager Only) -----------------
@app.route('/session_logs', methods=['GET'])
def get_session_logs():
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    if user['role'] not in ['Admin', 'Manager', 'Guest']:
        return jsonify({"error": "Forbidden: Access restricted"}), 403

    try:
        # Enforce hierarchical access control:
        # Admin can view all login/logout session logs
        if user['role'] in ['Admin', 'Guest']:
            logs = list(db.session_logs.find({}).sort("login_time", -1))
        # Manager can view Employee and Intern logs, plus their own
        else:
            sub_users = list(db.users.find({"role": {"$in": ["Employee", "Intern"]}}, {"username": 1}))
            sub_usernames = [u['username'] for u in sub_users]
            sub_usernames.append(user['username'])
            
            logs = list(db.session_logs.find({"username": {"$in": sub_usernames}}).sort("login_time", -1))
            
        return jsonify(serialize(logs))
    except Exception as e:
        return jsonify({"error": f"Failed to fetch session logs: {str(e)}"}), 500


# ----------------- COLLABORATION: MEDIA UPLOAD -----------------
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/uploads/<filename>')
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/upload', methods=['POST'])
def upload_file():
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected for uploading"}), 400

    if file:
        import uuid
        from werkzeug.utils import secure_filename
        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        filename = f"{uuid.uuid4()}.{ext}" if ext else str(uuid.uuid4())
        filename = secure_filename(filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        file_url = f"/uploads/{filename}"
        return jsonify({"url": file_url}), 200
    
    return jsonify({"error": "Upload failed"}), 400


# ----------------- COLLABORATION: PUBLIC KEYS FOR E2EE -----------------
@app.route('/users/public_key', methods=['PUT'])
def update_public_key():
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    if not data or 'public_key' not in data:
        return jsonify({"error": "Missing public_key in request"}), 400

    db.users.update_one({"username": user["username"]}, {"$set": {"public_key": data["public_key"]}})
    return jsonify({"message": "Public key updated successfully!"}), 200

@app.route('/users/<username>/public_key', methods=['GET'])
def get_user_public_key(username):
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    target = db.users.find_one({"username": username}, {"public_key": 1, "full_name": 1})
    if not target:
        return jsonify({"error": "User not found"}), 404

    if 'public_key' not in target:
        return jsonify({"error": f"User {target.get('full_name')} has not activated secure messaging yet (no public key)"}), 404

    return jsonify({"public_key": target["public_key"]}), 200


# ----------------- COLLABORATION: ANNOUNCEMENTS -----------------
@app.route('/announcements', methods=['GET'])
def get_announcements():
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        announcements = list(db.announcements.find({}).sort("created_at", -1).limit(50))
        announcements.reverse()
        return jsonify(serialize(announcements))
    except Exception as e:
        return jsonify({"error": f"Failed to fetch announcements: {str(e)}"}), 500

@app.route('/announcements', methods=['POST'])
def add_announcement():
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    if not data or 'content' not in data:
        return jsonify({"error": "Missing content in request"}), 400

    content = data.get('content')
    media_url = data.get('media_url', '')
    media_type = data.get('media_type', '')

    try:
        db.announcements.insert_one({
            "sender": user["username"],
            "sender_fullname": user["full_name"],
            "sender_role": user["role"],
            "content": content,
            "media_url": media_url,
            "media_type": media_type,
            "created_at": datetime.datetime.utcnow()
        })

        # Create notifications for all other approved active users
        other_users = db.users.find({"username": {"$ne": user["username"]}, "approved": True})
        for u in other_users:
            try:
                snippet = content[:40] + "..." if len(content) > 40 else content
                db.notifications.insert_one({
                    "username": u["username"],
                    "message": f"New announcement from {user['full_name']}: '{snippet}'",
                    "type": "announcement",
                    "created_at": datetime.datetime.utcnow(),
                    "read": False
                })
            except Exception as ne:
                print(f"Failed to create announcement notification: {ne}")

        return jsonify({"message": "Announcement posted successfully!"}), 201
    except Exception as e:
        return jsonify({"error": f"Failed to post announcement: {str(e)}"}), 500


# ----------------- COLLABORATION: SECURE ONE-TO-ONE MESSAGING (E2EE) -----------------
@app.route('/direct_messages', methods=['GET'])
def get_direct_messages():
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    recipient = request.args.get('recipient')
    if not recipient:
        return jsonify({"error": "Missing recipient parameter"}), 400

    try:
        # Mark incoming messages from recipient to current user as seen
        db.direct_messages.update_many(
            {"sender": recipient, "recipient": user["username"], "seen": {"$ne": True}},
            {"$set": {"seen": True}}
        )

        query = {
            "$or": [
                {"sender": user["username"], "recipient": recipient},
                {"sender": recipient, "recipient": user["username"]}
            ]
        }
        messages = list(db.direct_messages.find(query).sort("created_at", 1))
        return jsonify(serialize(messages))
    except Exception as e:
        return jsonify({"error": f"Failed to fetch messages: {str(e)}"}), 500

@app.route('/direct_messages', methods=['POST'])
def add_direct_message():
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    if not data or not all(k in data for k in ['recipient', 'ciphertext', 'iv', 'sender_key_enc', 'recipient_key_enc']):
        return jsonify({"error": "Missing required encrypted payload fields"}), 400

    recipient = data.get('recipient')
    ciphertext = data.get('ciphertext')
    iv = data.get('iv')
    sender_key_enc = data.get('sender_key_enc')
    recipient_key_enc = data.get('recipient_key_enc')

    target_user = db.users.find_one({"username": recipient})
    if not target_user:
        return jsonify({"error": "Recipient not found"}), 404

    try:
        db.direct_messages.insert_one({
            "sender": user["username"],
            "recipient": recipient,
            "ciphertext": ciphertext,
            "iv": iv,
            "sender_key_enc": sender_key_enc,
            "recipient_key_enc": recipient_key_enc,
            "created_at": datetime.datetime.utcnow(),
            "seen": False
        })

        # Create message notification for target user
        try:
            db.notifications.insert_one({
                "username": recipient,
                "message": f"New secure message from {user['full_name']}",
                "type": "direct_message",
                "created_at": datetime.datetime.utcnow(),
                "read": False
            })
        except Exception as ne:
            print(f"Failed to create message notification: {ne}")

        return jsonify({"message": "Message sent successfully!"}), 201
    except Exception as e:
        return jsonify({"error": f"Failed to send message: {str(e)}"}), 500


# ----------------- COLLABORATION: CONVERSATIONS LIST (E2EE) -----------------
@app.route('/direct_messages/conversations', methods=['GET'])
def get_conversations():
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        # Find all DMs involving the current user
        query = {"$or": [{"sender": user["username"]}, {"recipient": user["username"]}]}
        messages = list(db.direct_messages.find(query, {"sender": 1, "recipient": 1, "created_at": 1, "seen": 1}))
        
        conversations = {}
        for m in messages:
            other = m["recipient"] if m["sender"] == user["username"] else m["sender"]
            if other not in conversations:
                conversations[other] = {
                    "count": 0,
                    "unread_count": 0,
                    "received_count": 0,
                    "last_message_time": m["created_at"]
                }
            
            # Total messages in the conversation
            conversations[other]["count"] += 1
            
            # Messages sent BY THE OTHER USER
            if m["sender"] == other:
                conversations[other]["received_count"] += 1
                if not m.get("seen", False):
                    conversations[other]["unread_count"] += 1

            if m["created_at"] > conversations[other]["last_message_time"]:
                conversations[other]["last_message_time"] = m["created_at"]
        
        return jsonify(conversations)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch conversation stats: {str(e)}"}), 500


# ----------------- DELETE MESSAGE & ANNOUNCEMENT ENDPOINTS -----------------
@app.route('/announcements/<announcement_id>', methods=['DELETE'])
def delete_announcement(announcement_id):
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        ann = db.announcements.find_one({"_id": ObjectId(announcement_id)})
        if not ann:
            return jsonify({"error": "Announcement not found"}), 404
        
        # Sender, Admin, or Manager can delete
        if ann["sender"] == user["username"] or user["role"] in ["Admin", "Manager"]:
            db.announcements.delete_one({"_id": ObjectId(announcement_id)})
            
            # Clean up notifications related to this announcement
            db.notifications.delete_many({
                "type": "announcement",
                "message": {"$regex": f"New announcement from {ann['sender_fullname']}"}
            })
            
            return jsonify({"message": "Announcement deleted successfully!"}), 200
        else:
            return jsonify({"error": "Permission denied. You can only delete your own posts."}), 403
    except Exception as e:
        return jsonify({"error": f"Failed to delete announcement: {str(e)}"}), 500

@app.route('/direct_messages/<message_id>', methods=['DELETE'])
def delete_direct_message(message_id):
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        msg = db.direct_messages.find_one({"_id": ObjectId(message_id)})
        if not msg:
            return jsonify({"error": "Message not found"}), 404
        
        # Only the sender can delete their own message (unsend)
        if msg["sender"] == user["username"]:
            db.direct_messages.delete_one({"_id": ObjectId(message_id)})
            
            # Clean up unread notifications related to this DM from sender to recipient
            db.notifications.delete_many({
                "username": msg["recipient"],
                "type": "direct_message",
                "message": f"New secure message from {user['full_name']}",
                "read": False
            })
            
            return jsonify({"message": "Message deleted successfully!"}), 200
        else:
            return jsonify({"error": "Permission denied. You can only delete messages you sent."}), 403
    except Exception as e:
        return jsonify({"error": f"Failed to delete message: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
