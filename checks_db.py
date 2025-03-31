import sqlite3

DB_FILE = "users.db"

def check_users_table():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        # Get table schema
        cursor.execute("PRAGMA table_info(users);")
        columns = cursor.fetchall()

    print("\n✅ Users Table Schema:")
    for col in columns:
        print(col)

if __name__ == "__main__":
    check_users_table()
