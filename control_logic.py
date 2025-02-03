# control_logic.py

def decide_actuator_states(temperature, humidity, motion, temp_threshold=30, hum_threshold=70):
    """
    Simple example logic:
      - Fan ON if temperature > temp_threshold or humidity > hum_threshold
      - Light ON if motion == True
    Returns a dict with the new actuator states.
    """
    fan_on = (temperature > temp_threshold) or (humidity > hum_threshold)
    light_on = motion  # If motion is True, turn light on

    return {
        "fan": "ON" if fan_on else "OFF",
        "light": "ON" if light_on else "OFF"
    }
