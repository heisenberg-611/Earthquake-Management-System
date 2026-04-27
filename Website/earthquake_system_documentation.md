# Earthquake Management System Documentation

This document provides a comprehensive overview of the Earthquake Management System, detailing its architecture, components, database structure, and the purpose of every file within the codebase.

## System Architecture Overview

The application follows a standard **Model-View-Controller (MVC)** pattern, implemented using the Flask framework in Python. 

1. **Frontend (View)**: Built with HTML5, CSS3, and Vanilla JavaScript. It uses Jinja2 templating to dynamically render data passed from the backend.
2. **Backend (Controller)**: Built with Python and Flask. It handles routing, user authentication, role-based access control, session management, and processes incoming HTTP requests.
3. **Database (Model)**: A MySQL relational database managed via raw SQL queries through the `pymysql` library.

---

## 1. Backend Layer

The backend is responsible for the core logic, security, and data manipulation.

### `app.py`
This is the heart of the application. It initializes the Flask server and defines all the application's routes (endpoints).
- **Authentication & Security**: Handles `/login`, `/logout`, and `/signup`. It uses `werkzeug.security` to hash passwords and checks them securely. It uses Flask `session` to keep users logged in.
- **Role-Based Access Control (RBAC)**: Defines decorators (`@admin_required`, `@user_required`) to ensure that only authorized roles can access specific endpoints.
- **Dashboards**: Renders different views (`/admin/dashboard`, `/user/dashboard`) based on the user's role, fetching aggregate statistics for the admin dashboard.
- **CRUD Operations**: Contains all logic for **C**reating, **R**eading, **U**pdating, and **D**eleting Earthquake Events, Evacuation Routes, and Volunteers. It executes SQL queries directly to interact with the database.

### `db.py`
This file acts as the database connection factory.
- **Purpose**: Centralizes the database connection logic to avoid repetition in `app.py`.
- **How it works**: It uses the `pymysql` library to connect to the MySQL server. It securely reads database credentials (Host, Port, User, Password, DB Name) from environment variables, defaulting to local settings if none are found. It also enforces `DictCursor`, ensuring that database results are returned as easy-to-use Python dictionaries rather than raw tuples. It also handles SSL connections (referencing `ca.pem`).

### `seed_db.py`
A utility script used strictly for development and testing.
- **Purpose**: Populates the database with massive amounts of dummy data (60+ users, events, routes, and volunteers).
- **How it works**: It uses random string generators and coordinates logic to insert mock data into the database via `db.py`. This is essential for testing the UI, pagination (if any), sorting, and filtering logic without manually creating dozens of records.

---

## 2. Database Layer (MySQL)

The application relies on a highly structured relational database.

### `schema.sql`
This file defines the structural blueprint (schema) of the `earthquake_db`.
- **Purpose**: Used to initialize the database tables, relationships, constraints, and initial presentation data.
- **Structure**:
  - **Person Entity (Superclass)**: Stores common attributes like `PersonID`, `Name`, `Email`, and `Password`.
  - **Admin & User Entities (Subclasses)**: Inherit from `Person`. An Admin has elevated privileges, while a User belongs to a specific `Region`.
  - **Earthquake_Event**: Stores `Magnitude`, `Depth`, `Coordinates`, `AffectedArea`, and `Status`. Linked to the `Admin` who logged it.
  - **Evacuation_Route**: Stores `StartPoint`, `EndPoint`, `Distance`, `RoadType`, and `Status`. Linked to an `Admin`.
  - **Volunteer**: Linked to a `User` (1-to-1). Stores `Skills` and `AssignmentStatus` (Standby, Deployed, Returned). Managed by an `Admin`.
  - **Join Tables (M:N)**: `User_Searches_Event` and `User_Views_Route` track user interactions for potential analytics.

---

## 3. Frontend Layer

The frontend provides the interactive user interface, heavily styled with a "Vodafone-inspired" modern design system.

### `static/style.css`
The global stylesheet for the entire application.
- **Purpose**: Ensures a consistent, premium, and responsive visual experience.
- **Features**:
  - **Design Tokens**: Uses CSS variables (`:root`) to define a standardized color palette, typography (Inter, EB Garamond, JetBrains Mono), borders, and shadows.
  - **Component Styling**: Styles buttons (`.btn`, `.pill`), cards (`.card`), navigation (`nav`), and data tables (`.data-table`).
  - **Vodafone Theme**: Specifically styles the welcome page (`.voda-hero`, `.voda-red-band`) with dramatic typography and vibrant accents.

### `static/script.js`
The client-side logic handler.
- **Purpose**: Adds dynamic interactivity to the UI without requiring page reloads from the server.
- **Features**:
  - **Table Sorting**: Listens for clicks on table headers (`th.sortable`) and alphabetically/numerically sorts the rows in ascending or descending order.
  - **Multi-column Filtering**: Listens to input and dropdown changes on the `/volunteers` and `/routes` pages. It dynamically hides or shows table rows based on whether the cell text matches the search criteria (e.g., searching for a specific skill or filtering by route status).

### `templates/` Directory
Contains all the HTML views using the Jinja2 templating engine.
- **Purpose**: Allows Flask to inject dynamic Python variables (like user names, database records, and flash messages) directly into the HTML before sending it to the browser.
- **Key Files**:
  - `base.html`: The master layout file. It contains the `<head>`, global `<nav>`, and flash message rendering. All other templates *extend* this file, keeping the code DRY (Don't Repeat Yourself).
  - `welcome.html` & `index.html`: Landing pages.
  - `login.html`, `signup.html`: Authentication interfaces.
  - `admin_dashboard.html`, `user_dashboard.html`: Post-login landing hubs.
  - `events.html`, `routes.html`, `volunteers.html`: Data tables displaying fetched records.
  - `event_form.html`, `route_form.html`, `volunteer_form.html`: Reusable forms used for both **Creating** and **Updating** records.

---

## 4. Configuration & Deployment Files

- **`requirements.txt`**: Lists all Python dependencies (e.g., `Flask`, `PyMySQL`, `Werkzeug`). Necessary for setting up the environment.
- **`Procfile`**: Used by cloud hosting platforms (like Render or Heroku) to know what command to run to start the web server in production (e.g., usually using `gunicorn`).
- **`ca.pem`**: An SSL certificate file required by platforms like Aiven to establish a secure, encrypted connection between the Flask app and the remote MySQL database.

## Summary of Data Flow

1. **User Action**: A user clicks a link to view Evacuation Routes.
2. **Frontend Request**: The browser sends an HTTP GET request to `/routes`.
3. **Backend Route**: `app.py` catches `/routes`.
4. **Database Query**: `app.py` calls `get_db_connection()` from `db.py`, connects to MySQL, and executes `SELECT * FROM Evacuation_Route`.
5. **Data Processing**: MySQL returns the rows. `app.py` formats them into dictionaries.
6. **Template Rendering**: `app.py` passes the data to `routes.html` via Jinja2. The HTML loop `{% for route in routes %}` creates a table row for each record.
7. **Frontend Display**: The browser receives the raw HTML/CSS/JS. The user sees the table. They can then use the search bar, which triggers `script.js` to filter the rows locally on their machine.
