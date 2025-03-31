import sqlite3
import requests
import time
import csv
import os
import random
from flask import Flask, request, jsonify
import threading  # To run the Flask server and sensor simulation in parallel

DEVICE_API = "http://127.0.0.1:5001/get_states"


# ✅ API Configuration
WEATHER_API_KEY = "9da02c565641491282d135042250702"
CITY = "Eindhoven"
WEATHER_URL = f"https://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={CITY}&aqi=no"

DB_FILE = "sensor_data.db"
CSV_FILE = "sensor_log.csv"

# ✅ Initialize Flask App
app = Flask(__name__)

# ✅ Global variables to store actuator states (initial default states)
fan_state = "OFF"
light_state = "OFF"


def fetch_device_state():
    """Fetches the latest fan and light states from the actuator control API and database."""
    global fan_state, light_state

    try:
        # ✅ Check the latest manual state from the database
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT fan, light FROM sensor_log ORDER BY id DESC LIMIT 1;")
            result = cursor.fetchone()

        if result:
            fan_state, light_state = result  # ✅ Fetch from DB
            print(f"🌍 Updated Actuator States from DB: Fan={fan_state}, Light={light_state}")

        # ✅ Double-check with the API if needed
        response = requests.get(DEVICE_API, timeout=5)
        if response.status_code == 200:
            data = response.json()
            fan_state = data.get("fan", fan_state)  # ✅ Keep latest known state
            light_state = data.get("light", light_state)
            print(f"🌍 Retrieved Actuator States from API: {data}")

        return fan_state, light_state

    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error fetching device state from API: {e}")
    except Exception as e:
        print(f"⚠️ Error fetching device state from database: {e}")

    return fan_state, light_state



def run_sensor_simulation():
    """Fetches weather data and logs it to SQLite every 10 seconds, updating states dynamically."""
    global fan_state, light_state  # Allow Flask API to modify these variables
    init_db()

    try:
        while True:
            temperature, humidity = fetch_weather()
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

            if temperature is not None and humidity is not None:
                motion = "NO"

                # ✅ Fetch latest fan/light state
                fan_state, light_state = fetch_device_state()

                # ✅ Store updated states in the database
                store_sensor_data("weather_api", timestamp, temperature, humidity, motion, fan_state, light_state)

                print(f"📡 Data Logged: {timestamp}, Temp: {temperature}°C, Humidity: {humidity}%, Motion: {motion}, Fan: {fan_state}, Light: {light_state}")

            time.sleep(10)  # Fetch every 10 seconds
    except KeyboardInterrupt:
        print("🛑 Sensor simulation stopped.")

def log_actuator_change(device, state):
    """Logs the manual actuator state change into the database."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # ✅ Save only fan or light change
        if device == "fan":
            cursor.execute("UPDATE sensor_log SET fan = ? WHERE sensor_id = 'manual_control' ORDER BY id DESC LIMIT 1", (state,))
        elif device == "light":
            cursor.execute("UPDATE sensor_log SET light = ? WHERE sensor_id = 'manual_control' ORDER BY id DESC LIMIT 1", (state,))

        conn.commit()
        conn.close()
        print(f"✅ DATABASE UPDATED: {device.upper()} set to {state} at {timestamp}")

    except Exception as e:
        print(f"❌ Database Logging Error: {e}")



# ✅ Create/update SQLite database
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

# ✅ Fetch real-time weather data
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

# ✅ Store sensor data in SQLite and CSV
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

@app.route("/update_device", methods=["POST"])
def update_device():
    """Updates fan or light state manually and logs changes in SQLite."""
    global fan_state, light_state

    data = request.json
    device = data.get("device")
    new_state = data.get("state")

    if device == "fan":
        fan_state = new_state
    elif device == "light":
        light_state = new_state
    else:
        return jsonify({"status": "error", "message": "Invalid device"}), 400

    # ✅ Print Debugging Output
    print(f"🔄 {device.upper()} manually updated to {new_state}")

    # ✅ Debugging Print Statements
    print(f"🔄 MANUAL UPDATE: {device.upper()} changed to {new_state}")
    print(f"🔥 Current States after update -> Fan: {fan_state}, Light: {light_state}")

    return jsonify({"status": "success", "message": f"{device} updated to {new_state}"}), 200

@app.route("/get_states", methods=["GET"])
def get_states():
    """Returns the current states of the fan and light."""
    print(f"🌍 Returning Actuator States: Fan={fan_state}, Light={light_state}")  # ✅ Debugging
    return jsonify({"fan": fan_state, "light": light_state}), 200



# ✅ Sensor Simulation Loop (Now considers manual actuator control)
def run_sensor_simulation():
    """Fetches weather data and logs it to SQLite every 10 seconds, updating states dynamically."""
    global fan_state, light_state  # Allow Flask API to modify these variables
    init_db()

    try:
        while True:
            temperature, humidity = fetch_weather()
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

            if temperature is not None and humidity is not None:
                motion = "NO"

                # ✅ Fetch the latest fan/light states (respects manual changes)
                latest_fan_state, latest_light_state = fetch_device_state()

                # ✅ If a manual change was made, don't override it
                if fan_state != latest_fan_state:
                    fan_state = latest_fan_state
                if light_state != latest_light_state:
                    light_state = latest_light_state

                # ✅ Overheat Alert
                if temperature > 25:
                    print("🔥 WARNING: Overheat detected! Temperature exceeds 25°C!")

                # ✅ Humidity-Based Motion Detection
                if humidity > 80:
                    motion = "YES"

                # ✅ Automatic Control Logic (ONLY apply if no manual override)
                if fan_state == "OFF" and temperature > 25:  
                    fan_state = "ON"  
                elif fan_state == "ON" and temperature <= 25:
                    fan_state = "OFF"  

                current_hour = int(timestamp.split(" ")[1].split(":")[0])

                if light_state == "OFF" and (18 <= current_hour or current_hour < 6):
                    light_state = "ON"
                elif light_state == "ON" and (18 <= current_hour < 6):
                    light_state = "OFF"

                # ✅ Store data with updated states
                store_sensor_data("weather_api", timestamp, temperature, humidity, motion, fan_state, light_state)
                print(f"📡 Data Logged: {timestamp}, Temp: {temperature}°C, Humidity: {humidity}%, Motion: {motion}, Fan: {fan_state}, Light: {light_state}")

            time.sleep(10)  # Fetch every 10 seconds
    except KeyboardInterrupt:
        print("🛑 Sensor simulation stopped.")

# ✅ Log Manual Actuator Changes
def log_actuator_change(device, state):
    """Logs the manual actuator state change into the database."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        if device == "fan":
            cursor.execute("UPDATE sensor_log SET fan = ? WHERE sensor_id = 'manual_control' ORDER BY id DESC LIMIT 1", (state,))
        elif device == "light":
            cursor.execute("UPDATE sensor_log SET light = ? WHERE sensor_id = 'manual_control' ORDER BY id DESC LIMIT 1", (state,))

        conn.commit()
        conn.close()
        print(f"✅ DATABASE UPDATED: {device.upper()} set to {state} at {timestamp}")

    except Exception as e:
        print(f"❌ Database Logging Error: {e}")

# ✅ Run Flask and Sensor Simulation in Parallel
def start_flask():
    """Start the Flask app."""
    app.run(host="127.0.0.1", port=5001, debug=False)

if __name__ == "__main__":
    # Run Flask API and Sensor Simulation in parallel threads
    flask_thread = threading.Thread(target=start_flask, daemon=True)  # ✅ Add daemon=True

    flask_thread.start()

    run_sensor_simulation()
