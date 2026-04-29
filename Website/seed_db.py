import random
import string
from werkzeug.security import generate_password_hash
from db import get_db_connection

def generate_random_string(length=8):
    return ''.join(random.choices(string.ascii_letters, k=length))

def generate_random_coords():
    lat = round(random.uniform(-90, 90), 4)
    lon = round(random.uniform(-180, 180), 4)
    return f"{lat},{lon}"

def seed_database():
    try:
        print("Connecting to database...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        password_hash = generate_password_hash("password123")
        
        print("Inserting 200 Persons (for Users and Admins)...")
        first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa", "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"]
        
        person_ids = []
        for i in range(200):
            fname = random.choice(first_names)
            lname = random.choice(last_names)
            name = f"{fname} {lname} {i}"
            email = f"user{i}_{generate_random_string(4)}@example.com"
            
            cursor.execute("INSERT INTO Person (Name, Email, Password) VALUES (%s, %s, %s)", (name, email, password_hash))
            person_ids.append(cursor.lastrowid)
        
        print("Assigning Roles (5 Admins, 195 Users)...")
        admin_ids = []
        for i in range(5):
            cursor.execute("INSERT IGNORE INTO Admin (AdminID) VALUES (%s)", (person_ids[i],))
            admin_ids.append(person_ids[i])
            
        user_ids = []
        regions = ['North Zone', 'South Zone', 'East Zone', 'West Zone', 'Central', 'Pacific', 'Atlantic']
        for i in range(5, len(person_ids)):
            cursor.execute("INSERT IGNORE INTO User (UserID, Region) VALUES (%s, %s)", (person_ids[i], random.choice(regions)))
            user_ids.append(person_ids[i])
            
        print("Generating 200 Earthquake Events...")
        cities = ["Los Angeles", "San Francisco", "Tokyo", "Manila", "Jakarta", "Mexico City", "Santiago", "Lima", "Tehran", "Istanbul", "Athens", "Wellington"]
        statuses_event = ['Verified', 'Unverified']
        
        for _ in range(200):
            mag = round(random.uniform(2.5, 8.5), 1)
            depth = round(random.uniform(5.0, 300.0), 1)
            coords = generate_random_coords()
            area = f"{random.choice(cities)} Region"
            status = random.choice(statuses_event)
            admin_id = random.choice(admin_ids)
            
            cursor.execute("""
                INSERT INTO Earthquake_Event (Magnitude, Depth, Coordinates, AffectedArea, Status, AdminID) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (mag, depth, coords, area, status, admin_id))
            
        print("Generating 150 Volunteers...")
        skills_list = ['First Aid', 'Search and Rescue', 'Medical Doctor', 'Heavy Machinery Operator', 'Logistics', 'Communications', 'Paramedic', 'Firefighter', 'Translator', 'Structural Engineer']
        statuses_vol = ['Standby', 'Deployed', 'Returned']
        
        # We need a unique UserID for each volunteer
        for uid in user_ids[:150]: 
            cursor.execute("SELECT * FROM Volunteer WHERE UserID = %s", (uid,))
            if not cursor.fetchone():
                skills = f"{random.choice(skills_list)}, {random.choice(skills_list)}"
                cursor.execute("""
                    INSERT INTO Volunteer (Skills, AssignmentStatus, UserID, AdminID) 
                    VALUES (%s, %s, %s, %s)
                """, (skills, random.choice(statuses_vol), uid, random.choice(admin_ids)))
                
        print("Generating 200 Evacuation Routes...")
        places = ["City Hospital", "North Hills Shelter", "Central Station", "Eastside Camp", "Westside Mall", "South Bridge", "River Valley", "Highland Park", "Old Town", "New City Stadium", "Safe Zone Alpha", "Camp Bravo"]
        road_types = ["Highway", "Local Road", "Expressway", "Mountain Road", "Dirt Path", "Bridge"]
        statuses_route = ['Open', 'Blocked', 'Damaged', 'Under Repair']
        
        for i in range(200):
            start = f"{random.choice(places)} {i}"
            end = f"{random.choice(places)} {i+100}"
            dist = round(random.uniform(2.0, 50.0), 1)
            rtype = random.choice(road_types)
            status = random.choice(statuses_route)
            admin_id = random.choice(admin_ids)
            
            cursor.execute("""
                INSERT INTO Evacuation_Route (StartPoint, EndPoint, Distance, RoadType, Status, AdminID) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (start, end, dist, rtype, status, admin_id))
            
        conn.commit()
        print("Massive mock data inserted successfully!")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    seed_database()
