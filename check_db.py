import sqlite3

DB_FILE = "sensor_data.db"
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Fetch the latest 10 sensor readings
cursor.execute("SELECT * FROM sensor_log ORDER BY timestamp DESC LIMIT 10;")
rows = cursor.fetchall()

print("\n📊 Latest 10 Sensor Readings:")
for row in rows:
    print(row)

conn.close()
