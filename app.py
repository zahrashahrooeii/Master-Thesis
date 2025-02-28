import sqlite3
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

app = Flask(__name__, template_folder="dashboard/templates", static_folder="dashboard/static")
DB_FILE = "sensor_data.db"

def fetch_latest_data(limit=10):
    """Retrieve the latest `limit` rows from the sensor_log table."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sensor_log ORDER BY id DESC LIMIT ?;", (int(limit),))
            rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "sensor_id": row[1],
                "timestamp": row[2],
                "temperature": row[3],
                "humidity": row[4],
                "motion": row[5],
                "fan": row[6],
                "light": row[7],
            }
            for row in rows
        ]
    except Exception as e:
        print(f"⚠️ Database Error: {e}")
        return []

@app.route("/")
def index():
    """Main dashboard page"""
    return render_template("index.html")

@app.route("/api/latest-readings")
def api_latest_readings():
    """Returns the latest sensor data from SQLite."""
    latest_weather = fetch_latest_data(1)  # Fetch only 1 latest entry
    if not latest_weather:
        return jsonify({"status": "error", "message": "No sensor data found"}), 500

    return jsonify(latest_weather[0])  # Return the first (latest) entry

@app.route("/api/historical-readings")
def api_historical_readings():
    """Returns historical sensor data for data analysis."""
    limit = request.args.get("limit", default=50, type=int)  # Default to last 50 readings
    data = fetch_latest_data(limit)
    
    if not data:
        return jsonify({"status": "error", "message": "No historical data found"}), 500
    
    return jsonify(data)

if __name__ == "__main__":
    CORS(app)
    app.run(host="127.0.0.1", port=5000, debug=True)
