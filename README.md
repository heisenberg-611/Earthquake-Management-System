# Earthquake Management System (TaTuBo)

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8+-green.svg)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-lightgrey.svg)
![MySQL](https://img.shields.io/badge/Database-MySQL%20(Aiven)-orange.svg)

**TaTuBo** is a comprehensive, full-stack disaster response web application built with Python and Flask. Designed to be deployed rapidly in the critical hours following a severe seismic event, the platform facilitates immediate crisis assistance, safe evacuation routing, and coordinated volunteer deployment.

![TaTuBo](https://earthquake-management-system.onrender.com/)

---

## 🌟 Key Features

The system features robust Role-Based Access Control (RBAC), dividing permissions between **Administrators** (who manage the data) and **Users/Citizens** (who consume the data and volunteer).

### 1. Seismic Event Tracker
- **Administrators** can log new earthquake events, providing critical data such as Magnitude (Mw), Depth (km), Coordinates, Affected Area, and Verification Status.
- **Administrators** have full CRUD (Create, Read, Update, Delete) capabilities to manage false alarms or update event severities.
- **Citizens** can view a real-time, sorted registry of all verified seismic events to stay informed about danger zones.

### 2. Evacuation Route Intelligence
- **Administrators** can map out evacuation paths, specifying Start Points, End Points, Distances, Road Types, and current Status (Open, Blocked, Damaged, Under Repair).
- **Citizens** can securely access the database to view open and safe evacuation routes out of their immediate area, ensuring safe passage away from blocked sectors.
- Real-time dynamic filtering allows users to sort routes by specific Road Types and Statuses.

### 3. Volunteer Taskforce Registry
- **Citizens** can register themselves as active field volunteers, submitting their contact details and specialized skills (e.g., First Aid, Search and Rescue, Heavy Machinery).
- **Administrators** manage the entire volunteer taskforce from a high-level dashboard, updating assignment statuses (Standby, Deployed, Returned) as the crisis evolves.
- Features dynamic client-side filtering for immediate skill-matching and deployment.

---

## 🛠️ Technology Stack

- **Backend:** Python, Flask, PyMySQL, Werkzeug (Security/Hashing)
- **Frontend:** HTML5, CSS3, Vanilla JavaScript (Client-side sorting/filtering)
- **Database:** MySQL hosted securely on [Aiven.io](https://aiven.io/)
- **Deployment:** Ready for deployment on [Render](https://render.com/) via Gunicorn WSGI.

---

## 🚀 Local Installation & Setup

### Prerequisites
- Python 3.8+
- An active MySQL Database (Aiven.io recommended)
- `ca.pem` SSL Certificate (if connecting securely to a cloud database)

### 1. Clone & Install
```bash
git clone https://github.com/heisenberg-611/Earthquake-Management-System.git
cd Earthquake-Management-System
pip install -r requirements.txt
```

### 2. Configure Environment Variables
You must provide your database credentials to the application. Export the following variables in your terminal:

```bash
export SECRET_KEY="your-super-secret-key"
export DB_HOST="your-aiven-host-url.aivencloud.com"
export DB_PORT="26422"
export DB_USER="avnadmin"
export DB_PASSWORD="your-secure-password"
export DB_NAME="earthquake_db"
```

### 3. Seed the Database (Optional)
If you want to populate your database with massive amounts of realistic dummy data (60+ events, 60+ routes, 50+ volunteers) for presentation or testing purposes, run the seeder script:
```bash
python3 seed_db.py
```

### 4. Run the Server
Start the Flask development server:
```bash
python3 app.py
```
Visit `http://localhost:5001` in your browser to access the system.

---

## ☁️ Deployment (Render)

This application is configured for immediate deployment on Render.
1. Connect your GitHub repository to Render as a **Web Service**.
2. Set the Build Command: `pip install -r requirements.txt`
3. Set the Start Command: `gunicorn app:app` (as defined in the `Procfile`)
4. Add all the Environment Variables listed in Step 2 to the Render Environment tab.

---
*Stay Safe. Stay Connected.*
