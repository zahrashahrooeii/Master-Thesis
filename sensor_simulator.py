import sqlite3
import requests
import time
import csv
import os

# ✅ API Configuration
WEATHER_API_KEY = "9da02c565641491282d135042250702"
CITY = "Eindhoven"
WEATHER_URL = f"https://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={CITY}&aqi=no"

DB_FILE = "sensor_data.db"
CSV_FILE = "sensor_log.csv"

def init_db():
    """Creates the database table if it does not exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS sensor_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sensor_id TEXT,
                        timestamp TEXT,
                        temperature REAL,
                        humidity REAL,
                        motion TEXT,
                        fan TEXT,
                        light TEXT
                      )''')
    conn.commit()
    conn.close()

    # ✅ Create CSV file if it doesn't exist
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["sensor_id", "timestamp", "temperature", "humidity", "motion", "fan", "light"])

def fetch_weather():
    """Fetches real-time weather data from WeatherAPI with retry logic."""
    try:
        response = requests.get(WEATHER_URL, timeout=5)
        if response.status_code != 200:
            print(f"⚠️ API Error: {response.status_code} - {response.text}")
            return None, None

        data = response.json()
        return data["current"]["temp_c"], data["current"]["humidity"]

    except requests.exceptions.RequestException as e:
        print(f"❌ API Request Failed: {e} - Retrying in 30s")
        time.sleep(30)  # Retry after 30 seconds
        return None, None

def store_sensor_data(sensor_id, timestamp, temperature, humidity, motion, fan, light):
    """Stores sensor data in SQLite database and CSV."""
    
    # ✅ Save to SQLite
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sensor_log (sensor_id, timestamp, temperature, humidity, motion, fan, light) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (sensor_id, timestamp, temperature, humidity, motion, fan, light))
    conn.commit()
    conn.close()

    # ✅ Save to CSV
    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([sensor_id, timestamp, temperature, humidity, motion, fan, light])

def run_sensor_simulation():
    """Fetches weather data and logs it to SQLite every 10 seconds."""
    init_db()
    
    try:
        while True:
            temperature, humidity = fetch_weather()
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

            if temperature is not None and humidity is not None:
                motion = "NO"
                fan = "OFF"
                light = "OFF"

                # ✅ Overheat Alert
                if temperature > 30:
                    print("🔥 WARNING: Overheat detected! Temperature exceeds 30°C!")

                # ✅ Humidity-Based Motion Detection
                if humidity > 80:
                    motion = "YES"

                # ✅ Logic to control fan and light
                if temperature > 25:
                    fan = "ON"
                current_hour = int(timestamp.split(" ")[1].split(":")[0])
                if 18 <= current_hour or current_hour < 6:
                    light = "ON"

                store_sensor_data("weather_api", timestamp, temperature, humidity, motion, fan, light)
                print(f"📡 Data Logged: {timestamp}, Temp: {temperature}°C, Humidity: {humidity}%, Motion: {motion}, Fan: {fan}, Light: {light}")

            time.sleep(10)  # Fetch every 10 seconds
    except KeyboardInterrupt:
        print("🛑 Sensor simulation stopped.")

if __name__ == "__main__":
    run_sensor_simulation()
