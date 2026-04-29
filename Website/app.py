import os
from functools import wraps
from flask import Flask, render_template, request, flash, redirect, url_for, session
from db import get_db_connection
# init_db_if_not_exists
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
    volunteer_status = None
    volunteer_skills = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT AssignmentStatus, Skills FROM Volunteer WHERE UserID=%s", (session['user_id'],))
            vol = cursor.fetchone()
            if vol:
                volunteer_status = vol['AssignmentStatus']
                volunteer_skills = vol['Skills']
        conn.close()
    except Exception as e:
        flash(f"Error fetching volunteer status: {e}", "error")
        
    return render_template('user_dashboard.html', volunteer_status=volunteer_status, volunteer_skills=volunteer_skills)

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
                    flash("User registered successfully! Please login to access the system.", "success")
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
    statuses = []

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM Earthquake_Event ORDER BY Timestamp DESC")
            events_data = cursor.fetchall()
            
            cursor.execute("SELECT DISTINCT Status FROM Earthquake_Event")
            statuses = [row['Status'] for row in cursor.fetchall() if row['Status']]
            
        conn.close()
    except Exception as e:
        flash(f"Error fetching events: {e}", "error")
    return render_template('events.html', events=events_data, statuses=statuses)

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
@admin_required
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

# --- ENTITY ENDPOINTS: EVENT ---

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

# --- ENTITY ENDPOINTS: ROUTE ---

# FEATURE: Evacuation Route Tracker - CREATE
# -> Admin can add evacuation routes (start point, end point, distance, road type).
@app.route('/admin/route/add', methods=['GET', 'POST'])
@admin_required
def add_route():
    if request.method == 'POST':
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO Evacuation_Route (StartPoint, EndPoint, Distance, RoadType, Status, AdminID) VALUES (%s, %s, %s, %s, %s, %s)",
                    (request.form['start_point'], request.form['end_point'], request.form['distance'], request.form['road_type'], request.form['status'], session['user_id'])
                )
                conn.commit()
            conn.close()
            flash("Route added successfully.", "success")
            return redirect(url_for('routes'))
        except Exception as e:
            flash(f"Error: {e}", "error")
    return render_template('route_form.html', route=None)

# FEATURE: Evacuation Route Tracker - UPDATE
# -> Admin can update route status (Open, Blocked, Damaged, Under Repair).
@app.route('/admin/route/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_route(id):
    try:
        conn = get_db_connection()
        if request.method == 'POST':
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE Evacuation_Route SET StartPoint=%s, EndPoint=%s, Distance=%s, RoadType=%s, Status=%s WHERE RouteID=%s",
                    (request.form['start_point'], request.form['end_point'], request.form['distance'], request.form['road_type'], request.form['status'], id)
                )
                conn.commit()
            conn.close()
            flash("Route updated.", "success")
            return redirect(url_for('routes'))
            
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM Evacuation_Route WHERE RouteID=%s", (id,))
            route = cursor.fetchone()
        conn.close()
        return render_template('route_form.html', route=route)
    except Exception as e:
        flash(f"Error: {e}", "error")
        return redirect(url_for('routes'))

# FEATURE: Evacuation Route Tracker - DELETE
# -> Admin can remove routes that are permanently damaged or no longer needed.
@app.route('/admin/route/delete/<int:id>', methods=['POST'])
@admin_required
def delete_route(id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM Evacuation_Route WHERE RouteID=%s", (id,))
            conn.commit()
        conn.close()
        flash("Route deleted.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for('routes'))

# --- ENTITY ENDPOINTS: VOLUNTEER ---
@app.route('/admin/volunteer/add', methods=['GET', 'POST'])
@admin_required
def admin_add_volunteer():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        skills = request.form['skills']
        region = request.form.get('region', 'Unassigned')
        hashed_pw = generate_password_hash("volunteer123", method='pbkdf2:sha256')
        
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM Person WHERE Email=%s", (email,))
                existing_person = cursor.fetchone()
                
                if not existing_person:
                    cursor.execute("INSERT INTO Person (Name, Email, Password) VALUES (%s, %s, %s)", (name, email, hashed_pw))
                    user_id = cursor.lastrowid
                    cursor.execute("INSERT INTO User (UserID, Region) VALUES (%s, %s)", (user_id, region))
                else:
                    user_id = existing_person['PersonID']
                    cursor.execute("SELECT * FROM User WHERE UserID=%s", (user_id,))
                    if not cursor.fetchone():
                        cursor.execute("INSERT INTO User (UserID, Region) VALUES (%s, %s)", (user_id, region))
                
                cursor.execute("SELECT * FROM Volunteer WHERE UserID=%s", (user_id,))
                if cursor.fetchone():
                    flash("User is already a registered volunteer.", "error")
                else:
                    cursor.execute("INSERT INTO Volunteer (Skills, AssignmentStatus, UserID, AdminID) VALUES (%s, 'Standby', %s, %s)", (skills, user_id, session['user_id']))
                    conn.commit()
                    flash(f"Volunteer field profile initiated! Non-existing users received temporary default password: 'volunteer123'", "success")
            conn.close()
            return redirect(url_for('volunteers'))
        except Exception as e:
            flash(f"Error: {e}", "error")
    return render_template('admin_add_volunteer.html')

# FEATURE: Volunteer Registration - CREATE/UPDATE
# -> Users can register as a volunteer by submitting their details and skills.
@app.route('/user/volunteer/register', methods=['GET', 'POST'])
@user_required
def register_volunteer():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM Volunteer WHERE UserID=%s", (session['user_id'],))
            existing = cursor.fetchone()
            
        if request.method == 'POST':
            with conn.cursor() as cursor:
                if existing:
                    cursor.execute("UPDATE Volunteer SET Skills=%s WHERE UserID=%s", (request.form['skills'], session['user_id']))
                else:
                    cursor.execute("INSERT INTO Volunteer (Skills, AssignmentStatus, UserID) VALUES (%s, 'Standby', %s)", (request.form['skills'], session['user_id']))
                conn.commit()
            conn.close()
            flash("Volunteer registration processed!", "success")
            return redirect(url_for('user_dashboard'))
            
        conn.close()
        return render_template('volunteer_form.html', volunteer=existing, is_admin=False)
    except Exception as e:
        flash(f"Error: {e}", "error")
        return redirect(url_for('user_dashboard'))

# FEATURE: Volunteer Registration - UPDATE
# -> Admin can update volunteer assignment status (Standby, Deployed, Returned).
@app.route('/admin/volunteer/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_volunteer(id):
    try:
        conn = get_db_connection()
        if request.method == 'POST':
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE Volunteer SET Skills=%s, AssignmentStatus=%s, AdminID=%s WHERE VolunteerID=%s",
                    (request.form['skills'], request.form['status'], session['user_id'], id)
                )
                conn.commit()
            conn.close()
            flash("Volunteer status updated.", "success")
            return redirect(url_for('volunteers'))
            
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM Volunteer WHERE VolunteerID=%s", (id,))
            vol = cursor.fetchone()
        conn.close()
        return render_template('volunteer_form.html', volunteer=vol, is_admin=True)
    except Exception as e:
        flash(f"Error: {e}", "error")
        return redirect(url_for('volunteers'))

# FEATURE: Volunteer Registration - DELETE
# -> Admin can remove inactive or unavailable volunteers from the system.
@app.route('/admin/volunteer/delete/<int:id>', methods=['POST'])
@admin_required
def delete_volunteer(id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM Volunteer WHERE VolunteerID=%s", (id,))
            conn.commit()
        conn.close()
        flash("Volunteer removed from active system.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for('volunteers'))

if __name__ == '__main__':
    # init_db_if_not_exists()
    app.run(debug=True, port=5001)
