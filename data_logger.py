import os
import csv
import threading

class CSVDataLogger:
    def __init__(self, csv_file="sensor_log.csv", fieldnames=None):
        self.csv_file = csv_file
        self.fieldnames = fieldnames if fieldnames else [
            "sensor_id", "timestamp", "temperature", "humidity", "motion", "fan", "light"
        ]
        self._lock = threading.Lock()

        if not os.path.exists(self.csv_file):
            with open(self.csv_file, mode="w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writeheader()
                print(f"📂 Created new CSV log file: {self.csv_file}")

    def log(self, data):
        if "timestamp" not in data:
            data["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")

        with self._lock:
            try:
                print(f"📄 Writing to CSV: {data}")  # Debugging Line
                with open(self.csv_file, mode="a", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                    writer.writerow(data)
                print(f"✅ Logged: {data}")  # Debugging Line
            except Exception as e:
                print(f"❌ Error writing to CSV: {e}")
