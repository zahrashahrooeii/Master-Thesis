# sensor_simulator.py
import time
import random
import threading

class SensorSimulator:
    """
    Simulates one or more sensors generating data periodically.
    You can spawn multiple threads for multiple 'virtual sensors'.
    """

    def __init__(self, sensor_id, interval=2):
        """
        :param sensor_id: a unique ID or name for the sensor
        :param interval: time in seconds between data readings
        """
        self.sensor_id = sensor_id
        self.interval = interval
        self._running = False

    def start(self, callback):
        """
        Start the simulation in a separate thread.
        :param callback: a function that takes (sensor_id, reading_dict) as args
                         to handle each new sensor reading.
        """
        self._running = True

        def run():
            while self._running:
                reading = self.generate_reading()
                callback(self.sensor_id, reading)
                time.sleep(self.interval)

        thread = threading.Thread(target=run, daemon=True)
        thread.start()

    def stop(self):
        """Stop the simulator."""
        self._running = False

    def generate_reading(self):
        """
        Generate a simulated sensor reading. Adjust to match your needs:
        e.g., temperature, humidity, motion.
        """
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        temperature = round(random.uniform(20, 35), 2)
        humidity = round(random.uniform(30, 80), 2)
        motion = random.choice([True, False])
        return {
            "timestamp": timestamp,
            "temperature": temperature,
            "humidity": humidity,
            "motion": motion
        }
