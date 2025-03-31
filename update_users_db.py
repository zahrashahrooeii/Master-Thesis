import sqlite3

DB_FILE = "users.db"

def add_otp_expires_column():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()

        # ✅ Check if otp_expires_at column exists
        cursor.execute("PRAGMA table_info(users);")
        columns = [col[1] for col in cursor.fetchall()]

        if "otp_expires_at" not in columns:
            print("🛠 Adding 'otp_expires_at' column...")
            cursor.execute("ALTER TABLE users ADD COLUMN otp_expires_at DATETIME;")
            conn.commit()
            print("✅ Column 'otp_expires_at' added successfully!")
        else:
            print("⚡ 'otp_expires_at' column already exists!")

if __name__ == "__main__":
    add_otp_expires_column()
