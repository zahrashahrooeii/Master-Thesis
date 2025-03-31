# control_logic.py

def run_sensor_simulation():
    """Fetches weather data, checks manual actuator states, and applies control logic."""
    global fan_state, light_state  # Allow Flask API to modify these variables
    init_db()  # Ensure database is initialized

    try:
        while True:
            # 🔹 Step 1: Fetch real-time temperature & humidity
            temperature, humidity = fetch_weather()
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

            # 🔹 Step 2: Fetch latest actuator states (manual overrides)
            fan_manual, light_manual = fetch_device_state()  # ✅ Get latest user-set state

            if temperature is not None and humidity is not None:
                motion = "NO"

                # ✅ Overheat Alert
                if temperature > 25:
                    print("🔥 WARNING: Overheat detected! Temperature exceeds 30°C!")

                # ✅ Humidity-Based Motion Detection
                if humidity > 80:
                    motion = "YES"

                # ✅ Apply logic while respecting manual changes
                new_states = decide_actuator_states(temperature, humidity, motion, fan_manual, light_manual)

                fan_state = new_states["fan"]
                light_state = new_states["light"]

                # ✅ Store updated states in the database
                store_sensor_data("weather_api", timestamp, temperature, humidity, motion, fan_state, light_state)

                print(f"📡 Data Logged: {timestamp}, Temp: {temperature}°C, Humidity: {humidity}%, Motion: {motion}, Fan: {fan_state}, Light: {light_state}")

            time.sleep(10)  # Fetch every 10 seconds
    except KeyboardInterrupt:
        print("🛑 Sensor simulation stopped.")

