import sqlite3
import random
import string
import pdfkit
import pandas as pd
from flask import Flask, render_template, jsonify, request, Response, session
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import requests
import time # ✅ Added for response time logging



# ✅ Initialize Flask App
app = Flask(__name__, template_folder="dashboard/templates", static_folder="dashboard/static")
app.secret_key = "supersecretkey"


SENSOR_SIMULATOR_URL = "http://127.0.0.1:5001/update_device"

# ✅ Initialize Bcrypt for password hashing
bcrypt = Bcrypt(app)

# ✅ Configure Flask-Mail for OTP Email
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "smarrt.iot@gmail.com"  # 🔹 Replace with your email
app.config["MAIL_PASSWORD"] = "fadc reec gnpp nlis"  # 🔹 Replace with your email app password
mail = Mail(app)

# ✅ Database Paths
SENSOR_DB = "sensor_data.db"
USERS_DB = "users.db"

# ✅ Manually set wkhtmltopdf path
PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf="C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe")

# ✅ Function to generate a 6-digit OTP
def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

# ✅ Function to send OTP email
def send_otp_email(email, otp):
    try:
        msg = Message("Your OTP Code", sender="smarrt.iot@gmail.com", recipients=[email])
        msg.body = f"Your OTP code is: {otp}. Please use this to verify your account."
        mail.send(msg)
        return True
    except Exception as e:
        print(f"⚠️ Error sending email: {e}")
        return False

@app.route("/api/control/<device>", methods=["POST"])
def control_device(device):
    """Toggle the fan or light state manually and update the sensor simulator."""
    try:
        with sqlite3.connect(SENSOR_DB) as conn:
            cursor = conn.cursor()

            # ✅ Get the current state from the database
            cursor.execute(f"SELECT {device} FROM sensor_log ORDER BY id DESC LIMIT 1;")
            current_state = cursor.fetchone()

            if current_state:
                new_state = "OFF" if current_state[0] == "ON" else "ON"

                # ✅ Insert a new log instead of updating (ensures persistence)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute(
                    "INSERT INTO sensor_log (sensor_id, timestamp, temperature, humidity, motion, fan, light) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    ("manual_control", timestamp, None, None, None, new_state if device == "fan" else current_state[0],
                     new_state if device == "light" else current_state[0])
                )
                conn.commit()

                # ✅ Notify the Sensor Simulator
                try:
                    response = requests.post(SENSOR_SIMULATOR_URL, json={"device": device, "state": new_state})
                    if response.status_code != 200:
                        print(f"⚠️ Failed to notify sensor simulator: {response.text}")
                except Exception as e:
                    print(f"⚠️ Error contacting sensor simulator: {e}")

                return jsonify({"status": "success", "message": f"{device.capitalize()} turned {new_state}", "new_state": new_state}), 200

        return jsonify({"status": "error", "message": "Failed to update state"}), 500
    except Exception as e:
        print(f"⚠️ Error: {e}")
        return jsonify({"status": "error", "message": "Database error"}), 500

# ✅ Route for User Signup
@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.json
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"status": "error", "message": "All fields are required"}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    otp = generate_otp()
    otp_expires_at = datetime.now() + timedelta(minutes=1)  # ✅ OTP expires in 1 minute

    try:
        with sqlite3.connect(USERS_DB) as conn:
            cursor = conn.cursor()

            # Check if user already exists
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                return jsonify({"status": "error", "message": "Email already registered"}), 400

            # Insert new user with OTP and expiry time
            cursor.execute(
                "INSERT INTO users (name, email, password, otp, otp_expires_at, is_verified) VALUES (?, ?, ?, ?, ?, 0)",
                (name, email, hashed_password, otp, otp_expires_at),
            )
            conn.commit()

        # Send OTP to email
        if send_otp_email(email, otp):
            return jsonify({
    "status": "success",
    "message": "Signup successful! OTP sent to email.",
    "redirect": f"/verify_otp_page?email={email}"  # ✅ Redirect URL added
}), 200

        else:
            return jsonify({"status": "error", "message": "Failed to send OTP. Try again."}), 500

    except Exception as e:
        print(f"⚠️ Database Error: {e}")
        return jsonify({"status": "error", "message": "Database error"}), 500

@app.before_request
def start_timer():
    g.start_time = time.time()

@app.after_request
def log_response_time(response):
    if hasattr(g, 'start_time'):
        response_time = (time.time() - g.start_time) * 1000  # Convert to milliseconds
        print(f"API Response Time: {response_time:.2f} ms")
    return response

@app.route('/sensor_data', methods=['GET'])
def get_sensor_data():
    return {"temperature": 23, "humidity": 60}

    
@app.route("/api/verify_otp", methods=["POST"])
def verify_otp():
    data = request.json
    email = data.get("email")
    entered_otp = data.get("otp")

    if not email or not entered_otp:
        return jsonify({"status": "error", "message": "Email and OTP are required"}), 400

    try:
        with sqlite3.connect(USERS_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT otp, otp_expires_at FROM users WHERE email = ?", (email,))
            result = cursor.fetchone()

            if result:
                stored_otp, otp_expires_at = result
                current_time = datetime.now()

                # ✅ Check if OTP is expired
                if otp_expires_at and datetime.strptime(otp_expires_at, "%Y-%m-%d %H:%M:%S.%f") < current_time:
                    return jsonify({"status": "error", "message": "OTP expired. Please request a new one."}), 400

                if stored_otp == entered_otp:
                    cursor.execute("UPDATE users SET is_verified = 1, otp = NULL, otp_expires_at = NULL WHERE email = ?", (email,))
                    conn.commit()
                    return jsonify({
                        "status": "success",
                        "message": "OTP verified! Redirecting to login.",
                        "redirect": "/login_page"  # ✅ FIXED: Redirect to /login_page
                    }), 200
                else:
                    return jsonify({"status": "error", "message": "Invalid OTP"}), 400
            else:
                return jsonify({"status": "error", "message": "User not found"}), 404

    except Exception as e:
        print(f"⚠️ Database Error: {e}")
        return jsonify({"status": "error", "message": "Database error"}), 500


@app.route("/api/resend_otp", methods=["POST"])
def resend_otp():
    data = request.json
    email = data.get("email")

    if not email:
        return jsonify({"status": "error", "message": "Email is required"}), 400

    try:
        new_otp = generate_otp()
        otp_expires_at = datetime.now() + timedelta(minutes=1)  # ✅ New expiry time

        with sqlite3.connect(USERS_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET otp = ?, otp_expires_at = ? WHERE email = ?", (new_otp, otp_expires_at, email))
            conn.commit()

        # ✅ Send the new OTP
        if send_otp_email(email, new_otp):
            return jsonify({"status": "success", "message": "New OTP sent to email."}), 200
        else:
            return jsonify({"status": "error", "message": "Failed to send new OTP. Try again."}), 500

    except Exception as e:
        print(f"⚠️ Database Error: {e}")
        return jsonify({"status": "error", "message": "Database error"}), 500
    


# 📌 Function to retrieve latest sensor data
def fetch_latest_data(limit=10):
    try:
        with sqlite3.connect(SENSOR_DB) as conn:  # ✅ FIXED
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

# 📌 Function to retrieve historical data based on timeframe
def fetch_historical_data(timeframe):
    try:
        with sqlite3.connect(SENSOR_DB) as conn:  # ✅ FIXED
            cursor = conn.cursor()

            
            if timeframe == "week":
                query = "SELECT * FROM sensor_log WHERE timestamp >= DATETIME('now', '-7 days') ORDER BY timestamp ASC;"
            elif timeframe == "month":
                query = "SELECT * FROM sensor_log WHERE timestamp >= DATETIME('now', '-30 days') ORDER BY timestamp ASC;"
            elif timeframe == "year":
                query = "SELECT * FROM sensor_log WHERE timestamp >= DATETIME('now', '-1 year') ORDER BY timestamp ASC;"
            else:  # Default to last 24 hours
                query = "SELECT * FROM sensor_log WHERE timestamp >= DATETIME('now', '-1 day') ORDER BY timestamp ASC;"
            
            cursor.execute(query)
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
def home_page():  # ✅ Rename the function to avoid conflict
    return render_template("home.html")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")  # ✅ Redirect to home if not logged in
    return render_template("index.html")  # ✅ Show dashboard after login
 # Now dashboard has a separate route


@app.route("/signup_page")
def signup_page():
    return render_template("signup.html")

@app.route("/login_page")
def login_page():
    return render_template("login.html")

@app.route("/verify_otp_page")
def verify_otp_page():
    email = request.args.get("email")
    if not email:
        return "Invalid request", 400
    return render_template("verify_otp.html", email=email)



@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"status": "error", "message": "Email and password required"}), 400

    try:
        with sqlite3.connect(USERS_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password, is_verified FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()

            if user:
                stored_password, is_verified = user
                if is_verified == 0:
                    return jsonify({"status": "error", "message": "Account not verified. Please check your email."}), 403

                if bcrypt.check_password_hash(stored_password, password):
                    session["user"] = email  # ✅ Store session
                    return jsonify({"status": "success", "message": "Login successful!", "redirect": "/dashboard"}), 200  # ✅ Send redirect URL
                else:
                    return jsonify({"status": "error", "message": "Invalid credentials"}), 401
            else:
                return jsonify({"status": "error", "message": "User not found"}), 404

    except Exception as e:
        print(f"⚠️ Database Error: {e}")
        return jsonify({"status": "error", "message": "Database error"}), 500


# ✅ Route for Logout
@app.route("/api/logout", methods=["GET"])
def logout():
    session.pop("user", None)
    return jsonify({"status": "success", "message": "Logged out successfully"}), 200


@app.route("/api/latest-readings")
def api_latest_readings():
    """Returns the latest sensor data from SQLite."""
    latest_weather = fetch_latest_data(1)  # Fetch only 1 latest entry
    if not latest_weather:
        return jsonify({"status": "error", "message": "No sensor data found"}), 500

    return jsonify(latest_weather[0])  # Return the first (latest) entry

@app.route("/api/historical-readings")
def api_historical_readings():
    """Returns historical sensor data based on selected timeframe."""
    timeframe = request.args.get("timeframe", default="day")  # Default to last 24 hours
    data = fetch_historical_data(timeframe)
    
    if not data:
        return jsonify({"status": "error", "message": "No historical data found"}), 500
    
    return jsonify(data)


# 📌 Route to download CSV
@app.route("/api/download_csv")
def download_csv():
    df = fetch_historical_data()
    if df is None or df.empty:
        return jsonify({"status": "error", "message": "No data available"}), 500

    csv_data = df.to_csv(index=False)
    return Response(csv_data, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=sensor_data.csv"})

import pdfkit

@app.route("/api/download_pdf")
def download_pdf():
    try:
        data = fetch_historical_data("day")  # Change timeframe if needed

        if not data:
            return jsonify({"status": "error", "message": "No data available"}), 500

        # ✅ Convert data to HTML
        html = "<h1>Sensor Data Report</h1>"
        html += "<table border='1'><tr><th>ID</th><th>Sensor</th><th>Timestamp</th><th>Temp (°C)</th><th>Humidity (%)</th></tr>"

        for row in data:
            html += f"<tr><td>{row['id']}</td><td>{row['sensor_id']}</td><td>{row['timestamp']}</td><td>{row['temperature']}</td><td>{row['humidity']}</td></tr>"

        html += "</table>"

        # ✅ Generate PDF (Make sure wkhtmltopdf is installed)
        pdf = pdfkit.from_string(html, False, configuration=pdfkit.configuration(wkhtmltopdf="C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe"))

        return Response(pdf, mimetype="application/pdf",
                        headers={"Content-Disposition": "attachment; filename=sensor_report.pdf"})

    except Exception as e:
        print(f"⚠️ Error generating PDF: {e}")
        return jsonify({"status": "error", "message": "Failed to generate PDF"}), 500

if __name__ == "__main__":
    CORS(app)
    app.run(host="127.0.0.1", port=5000, debug=True)
