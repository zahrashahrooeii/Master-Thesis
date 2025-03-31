import sqlite3

DB_FILE = "users.db"

def create_users_table():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
  # ✅ Create users table with OTP expiry time
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            otp TEXT,
            otp_expires_at DATETIME,  -- Added this column for expiry time
            is_verified INTEGER DEFAULT 0
        );
    """)
    
    conn.commit()

print("✅ Users table updated successfully with OTP expiry time!")
if __name__ == "__main__":
    create_users_table()
