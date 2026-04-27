import pymysql
import os

def get_db_connection():
    return pymysql.connect(
        host=os.environ.get('DB_HOST', 'localhost'), 
        port=int(os.environ.get('DB_PORT', 3306)), 
        user=os.environ.get('DB_USER', 'root'), 
        password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ.get('DB_NAME', 'earthquake_db'), 
        cursorclass=pymysql.cursors.DictCursor,
        ssl={"ca": "ca.pem"}  
    )

# def init_db_if_not_exists():
#     db_name = os.environ.get('DB_NAME', 'earthquake_db')
#     needs_init = False
#     try:
#         conn = get_db_connection()
#         with conn.cursor() as cursor:
#             cursor.execute("SHOW TABLES")
#             tables = cursor.fetchall()
#             if not tables:
#                 needs_init = True
#         conn.close()
#     except pymysql.err.OperationalError as e:
#         if e.args[0] == 1049: # Unknown database
#             needs_init = True
#         else:
#             print(f"Database connection failed: {e}")
#             return
#     except Exception as e:
#         print(f"Error checking database: {e}")
#         return

#     if needs_init:
#         print(f"Database '{db_name}' or tables not found. Initializing...")
#         try:
#             # Connect without specifying a database to create it
#             conn = pymysql.connect(
#                 host=os.environ.get('DB_HOST', 'localhost'), 
#                 port=int(os.environ.get('DB_PORT', 3306)), 
#                 user=os.environ.get('DB_USER', 'root'), 
#                 password=os.environ.get('DB_PASSWORD', ''),
#                 cursorclass=pymysql.cursors.DictCursor
#             )
#             with conn.cursor() as cursor:
#                 # Read schema.sql
#                 schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
#                 with open(schema_path, 'r') as f:
#                     sql_script = f.read()
                
#                 # Execute each statement
#                 for statement in sql_script.split(';'):
#                     if statement.strip():
#                         cursor.execute(statement)
#             conn.commit()
#             conn.close()
#             print("Schema executed successfully.")
            
#             # Now run the seed script
#             from seed_db import seed_database
#             seed_database()
#         except Exception as ex:
#             print(f"Error initializing DB: {ex}")
