# app.py
import os
import time
from flask import Flask, render_template, request, jsonify
from sensor_simulator import SensorSimulator
from control_logic import decide_actuator_states
from data_logger import CSVDataLogger

# If you want encryption, import from encryption_utils
# from encryption_utils import load_key, encrypt_data, decrypt_data

app = Flask(__name__, template_folder="dashboard/templates", static_folder="dashboard/static")

# Global variables for storing the latest sensor readings and actuator states
latest_readings = {}    # {sensor_id: {"timestamp":..., "temperature":..., ...}}
actuator_states = {}    # {sensor_id: {"fan":..., "light":...}}

# Instantiate the logger for CSV
logger = CSVDataLogger(csv_file="sensor_log.csv", 
                       fieldnames=["sensor_id", "timestamp", "temperature", "humidity", "motion", "fan", "light"])

# Start multiple simulators
simulators = []
def start_sensors():
    # Example: create 2 sensors
    sensor1 = SensorSimulator(sensor_id="sensor1", interval=2)
    sensor2 = SensorSimulator(sensor_id="sensor2", interval=3)
    simulators.extend([sensor1, sensor2])

    # Callback function when new data is generated
    def on_new_reading(sensor_id, reading):
        # 1) Update latest readings
        latest_readings[sensor_id] = reading

        # 2) Decide actuator states
        decision = decide_actuator_states(
            temperature=reading["temperature"],
            humidity=reading["humidity"],
            motion=reading["motion"],
            temp_threshold=30,
            hum_threshold=70
        )

        # Store the actuator state
        actuator_states[sensor_id] = decision

        # 3) Merge sensor reading + decision for logging
        row = {
            "sensor_id": sensor_id,
            "timestamp": reading["timestamp"],
            "temperature": reading["temperature"],
            "humidity": reading["humidity"],
            "motion": reading["motion"],
            "fan": decision["fan"],
            "light": decision["light"]
        }
        logger.log(row)

    # Start them
    sensor1.start(callback=on_new_reading)
    sensor2.start(callback=on_new_reading)

@app.route("/")
def index():
    """
    Main dashboard page.
    """
    return render_template("index.html")

@app.route("/api/latest-readings")
def api_latest_readings():
    """
    Returns the latest readings + actuator states for each sensor, in JSON.
    The frontend can poll this endpoint to update the dashboard.
    """
    combined = {}
    for sid, reading in latest_readings.items():
        combined[sid] = {
            **reading,
            **actuator_states.get(sid, {})
        }
    return jsonify(combined)

@app.route("/api/set-actuator", methods=["POST"])
def api_set_actuator():
    """
    Allows manual override. For example:
    POST /api/set-actuator
    {
      "sensor_id": "sensor1",
      "fan": "ON",
      "light": "OFF"
    }
    This might override the decision logic for demonstration.
    """
    data = request.json
    sensor_id = data.get("sensor_id")
    if sensor_id and sensor_id in actuator_states:
        # Update the stored actuator state
        fan_state = data.get("fan", actuator_states[sensor_id]["fan"])
        light_state = data.get("light", actuator_states[sensor_id]["light"])
        actuator_states[sensor_id] = {"fan": fan_state, "light": light_state}

        # Optionally log that override happened
        # ...
        return jsonify({"status": "ok", "message": "Actuator override set."})
    return jsonify({"status": "error", "message": "Invalid sensor_id"}), 400

if __name__ == "__main__":
    # Start sensors in background threads
    start_sensors()
    
    # Run Flask app
    app.run(host="127.0.0.1", port=5000, debug=True)
