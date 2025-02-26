import psycopg2

def connect_db():
    """Establish a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            dbname="travel_chatbot",  # Change this if your database name is different
            user="postgres",  # Change to your PostgreSQL username
            password="kingroy975",  # Change to your PostgreSQL password
            host="127.0.0.1",  # Keep this as localhost unless using a remote server
            port=3001  # Ensure this is the correct PostgreSQL port
        )
        return conn
    except Exception as e:
        print("❌ Database connection error:", e)
        return None
