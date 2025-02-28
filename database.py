import sqlite3

DB_FILE = "sensor_data.db"

def initialize_database():
    """Creates the database table if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sensor_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sensor_id TEXT,
        timestamp TEXT,
        temperature REAL,
        humidity REAL,
        motion TEXT,
        fan TEXT,
        light TEXT
    )
    """)

    conn.commit()
    conn.close()

def insert_sensor_data(sensor_id, timestamp, temperature, humidity, motion, fan, light):
    """Inserts sensor data into SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO sensor_log (sensor_id, timestamp, temperature, humidity, motion, fan, light)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (sensor_id, timestamp, temperature, humidity, motion, fan, light))

    conn.commit()
    conn.close()

# ✅ Ensure the database is set up when this file runs
initialize_database()
