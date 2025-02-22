import psycopg2

def connect_db():
    try:
        conn = psycopg2.connect(
            dbname="travel_chatbot",
            user="postgres",
            password="kingroy975",
            host="localhost",  # Use 'localhost' instead of '127.0.0.1'
            port="3001"  # PostgreSQL default port
        )
        return conn
    except Exception as e:
        print("Database connection failed:", e)
        return None

def fetch_locations():
    conn = connect_db()
    if not conn:
        return
    
    cur = conn.cursor()
    cur.execute("SELECT * FROM locations;")
    rows = cur.fetchall()
    
    for row in rows:
        print(row)

    cur.close()
    conn.close()

# Run the function
fetch_locations()
