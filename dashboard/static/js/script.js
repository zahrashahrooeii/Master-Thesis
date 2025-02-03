function fetchSensorData() {
    fetch("/api/latest-readings")
      .then(response => response.json())
      .then(data => {
        const container = document.getElementById("sensorDataContainer");
        container.innerHTML = "";
  
        // data is something like: { sensor1: {...}, sensor2: {...} }
        for (let sensorId in data) {
          const reading = data[sensorId];
          const div = document.createElement("div");
          div.classList.add("sensor-block");
  
          div.innerHTML = `
            <h3>Sensor: ${sensorId}</h3>
            <p>Timestamp: ${reading.timestamp}</p>
            <p>Temperature: ${reading.temperature} °C</p>
            <p>Humidity: ${reading.humidity} %</p>
            <p>Motion: ${reading.motion}</p>
            <p>Fan State: ${reading.fan}</p>
            <p>Light State: ${reading.light}</p>
          `;
  
          container.appendChild(div);
        }
      })
      .catch(err => console.error(err));
  }
  
  setInterval(fetchSensorData, 3000);
  fetchSensorData();  // initial load
  