import os
from functools import wraps
from flask import Flask, render_template, request, flash, redirect, url_for, session
from db import get_db_connection, init_db_if_not_exists
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# Use a static SECRET_KEY in production to prevent sessions from resetting!
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# --- Role Decorators ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'Admin':
            flash("Access Denied: Administrator permissions required.", "error")
            return redirect(url_for('welcome'))
        return f(*args, **kwargs)
    return decorated_function

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'User':
            flash("Access Denied: You must be signed in as a User.", "error")
            return redirect(url_for('welcome'))
        return f(*args, **kwargs)
    return decorated_function

# --- Dashboards ---
@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("You must be logged in to view your dashboard.", "error")
        return redirect(url_for('login'))
    if session.get('role') == 'Admin':
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('user_dashboard'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as cnt FROM Earthquake_Event")
            total_events = cursor.fetchone()['cnt']
            
            cursor.execute("SELECT COUNT(*) as cnt FROM Earthquake_Event WHERE Status = 'Verified'")
            verified_events = cursor.fetchone()['cnt']
            
            cursor.execute("SELECT COUNT(*) as cnt FROM Volunteer")
            total_volunteers = cursor.fetchone()['cnt']
            
            cursor.execute("SELECT COUNT(*) as cnt FROM Evacuation_Route WHERE Status != 'Open'")
            disrupted_routes = cursor.fetchone()['cnt']
        conn.close()
        return render_template('admin_dashboard.html', 
            total_events=total_events, verified_events=verified_events,
            total_volunteers=total_volunteers, disrupted_routes=disrupted_routes)
    except Exception as e:
        flash(f"DB error: {e}", "error")
        return render_template('admin_dashboard.html', total_events=0, verified_events=0, total_volunteers=0, disrupted_routes=0)

@app.route('/user/dashboard')
@user_required
def user_dashboard():
    return render_template('user_dashboard.html')

# --- AUTH ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM Person WHERE Email = %s", (email,))
                person = cursor.fetchone()
                
                if person and check_password_hash(person['Password'], password):
                    session['user_id'] = person['PersonID']
                    session['name'] = person['Name']
                    
                    cursor.execute("SELECT * FROM Admin WHERE AdminID = %s", (person['PersonID'],))
                    if cursor.fetchone():
                        session['role'] = 'Admin'
                        flash("Logged in successfully as Administrator!", "success")
                        return redirect(url_for('admin_dashboard'))
                    else:
                        session['role'] = 'User'
                        flash("Welcome back!", "success")
                        return redirect(url_for('user_dashboard'))
                else:
                    flash("Invalid email or password", "error")
            conn.close()
        except Exception as e:
            flash(f"Database error: {e}", "error")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))

@app.route('/signup/user', methods=['GET', 'POST'])
def signup_user():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        region = request.form.get('region', 'Unassigned')
        
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM Person WHERE Email = %s", (email,))
                if cursor.fetchone():
                    flash("Email already registered.", "error")
                else:
                    cursor.execute("INSERT INTO Person (Name, Email, Password) VALUES (%s, %s, %s)", (name, email, hashed_pw))
                    person_id = cursor.lastrowid
                    cursor.execute("INSERT INTO User (UserID, Region) VALUES (%s, %s)", (person_id, region))
                    conn.commit()
                    flash("User registered successfully! Please longin to access the system.", "success")
                    return redirect(url_for('login'))
            conn.close()
        except Exception as e:
            flash(f"Error: {e}", "error")
            
    return render_template('signup.html', role='User')

@app.route('/signup/admin', methods=['GET', 'POST'])
@admin_required
def signup_admin():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM Person WHERE Email = %s", (email,))
                if cursor.fetchone():
                    flash("Email already registered.", "error")
                else:
                    cursor.execute("INSERT INTO Person (Name, Email, Password) VALUES (%s, %s, %s)", (name, email, hashed_pw))
                    person_id = cursor.lastrowid
                    cursor.execute("INSERT INTO Admin (AdminID) VALUES (%s)", (person_id,))
                    conn.commit()
                    flash("Administrator registered successfully!", "success")
                    return redirect(url_for('admin_dashboard'))
            conn.close()
        except Exception as e:
            flash(f"Error: {e}", "error")
            
    return render_template('signup.html', role='Admin')

# --- CORE ROUTES (Events, Routes, Volunteers) ---

# FEATURE: Seismic Event Tracker - READ
# -> Admin can view all logged seismic events.
@app.route('/events')
def events():
    events_data = []
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM Earthquake_Event ORDER BY Timestamp DESC")
            events_data = cursor.fetchall()
        conn.close()
    except Exception as e:
        flash(f"Error fetching events: {e}", "error")
    return render_template('events.html', events=events_data)

# FEATURE: Evacuation Route Tracker - READ
# -> Users can view all evacuation routes for their zone.
@app.route('/routes')
def routes():
    routes_data = []
    road_types = []
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM Evacuation_Route")
            routes_data = cursor.fetchall()
            
            cursor.execute("SELECT DISTINCT RoadType FROM Evacuation_Route")
            road_types = [row['RoadType'] for row in cursor.fetchall() if row['RoadType']]
        conn.close()
    except Exception as e:
        flash(f"Error fetching routes: {e}", "error")
    return render_template('routes.html', routes=routes_data, road_types=road_types)

# FEATURE: Volunteer Registration - READ
# -> Admin can view all registered volunteers.
@app.route('/volunteers')
def volunteers():
    volunteers_data = []
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            query = """
                SELECT v.VolunteerID, p.Name, p.Email, v.Skills, v.AssignmentStatus
                FROM Volunteer v
                JOIN User u ON v.UserID = u.UserID
                JOIN Person p ON u.UserID = p.PersonID
            """
            cursor.execute(query)
            volunteers_data = cursor.fetchall()
        conn.close()
    except Exception as e:
        flash(f"Error fetching volunteers: {e}", "error")
    return render_template('volunteers.html', volunteers=volunteers_data)

# FEATURE: Seismic Event Tracker - CREATE
# -> Admin can add new earthquake event records to the system.
@app.route('/admin/event/add', methods=['GET', 'POST'])
@admin_required
def add_event():
    if request.method == 'POST':
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO Earthquake_Event (Magnitude, Depth, Coordinates, AffectedArea, Status, AdminID) VALUES (%s, %s, %s, %s, %s, %s)",
                    (request.form['magnitude'], request.form['depth'], request.form['coordinates'], request.form['affected_area'], request.form['status'], session['user_id'])
                )
                conn.commit()
            conn.close()
            flash("Event added successfully.", "success")
            return redirect(url_for('events'))
        except Exception as e:
            flash(f"Error: {e}", "error")
    return render_template('event_form.html', event=None)

# FEATURE: Seismic Event Tracker - UPDATE
# -> Admin can update event details (magnitude, depth, coordinates, affected area, etc.).
@app.route('/admin/event/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_event(id):
    try:
        conn = get_db_connection()
        if request.method == 'POST':
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE Earthquake_Event SET Magnitude=%s, Depth=%s, Coordinates=%s, AffectedArea=%s, Status=%s WHERE EventID=%s",
                    (request.form['magnitude'], request.form['depth'], request.form['coordinates'], request.form['affected_area'], request.form['status'], id)
                )
                conn.commit()
            conn.close()
            flash("Event updated.", "success")
            return redirect(url_for('events'))
            
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM Earthquake_Event WHERE EventID=%s", (id,))
            event = cursor.fetchone()
        conn.close()
        return render_template('event_form.html', event=event)
    except Exception as e:
        flash(f"Error: {e}", "error")
        return redirect(url_for('events'))

# FEATURE: Seismic Event Tracker - DELETE
# -> Admin can remove duplicate or false alarm event records.
@app.route('/admin/event/delete/<int:id>', methods=['POST'])
@admin_required
def delete_event(id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM Earthquake_Event WHERE EventID=%s", (id,))
            conn.commit()
        conn.close()
        flash("Event deleted.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for('events'))

if __name__ == '__main__':
    # init_db_if_not_exists()
    app.run(debug=True, port=5001)