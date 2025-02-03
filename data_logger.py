# data_logger.py
import os
import csv
import threading

class CSVDataLogger:
    """
    Thread-safe CSV logger that appends sensor readings.
    """

    def __init__(self, csv_file="sensor_log.csv", fieldnames=None):
        """
        :param csv_file: path to your CSV log file
        :param fieldnames: list of column names, e.g. ["timestamp", "temperature", "humidity", "motion", "fan", "light"]
        """
        self.csv_file = csv_file
        self.fieldnames = fieldnames if fieldnames else ["timestamp", "temperature", "humidity", "motion", "fan", "light"]
        self._lock = threading.Lock()

        # If file doesn't exist, create and write header
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, mode="w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writeheader()

    def log(self, data):
        """
        data is a dict matching the fieldnames. e.g.:
        {
          "timestamp": "2025-01-26 12:00:00",
          "temperature": 25.6,
          "humidity": 60.1,
          "motion": False,
          "fan": "OFF",
          "light": "OFF"
        }
        """
        with self._lock, open(self.csv_file, mode="a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writerow(data)
