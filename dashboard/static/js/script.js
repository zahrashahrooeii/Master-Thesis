// 📌 Global variables to store chart data
let timestamps = [];
let temperatures = [];
let humidities = [];

// 📌 Initialize Chart.js
const ctx = document.getElementById("sensorChart").getContext("2d");
const sensorChart = new Chart(ctx, {
    type: "line",
    data: {
        labels: timestamps,
        datasets: [
            {
                label: "Temperature (°C)",
                data: temperatures,
                borderColor: "red",
                borderWidth: 2,
                fill: false,
            },
            {
                label: "Humidity (%)",
                data: humidities,
                borderColor: "blue",
                borderWidth: 2,
                fill: false,
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: { title: { display: true, text: "Timestamp" } },
            y: { title: { display: true, text: "Value" } }
        }
    }
});

// 📌 Function to show alerts
function showAlert(message, type) {
    const alertBox = document.getElementById("alertBox");
    alertBox.innerHTML = `<div class="alert alert-${type} alert-dismissible fade show" role="alert">
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>`;
}

// 📌 Function to fetch and update sensor data every 3 seconds
function fetchSensorData() {
    fetch("/api/latest-readings")
        .then(response => response.json())
        .then(data => {
            console.log("📡 API Response:", data);

            if (!data || Object.keys(data).length === 0) {
                console.error("❌ No sensor data received.");
                return;
            }

            // ✅ Extract values safely
            const timestamp = data.timestamp || new Date().toISOString();
            const temperature = data.temperature !== undefined ? data.temperature : "N/A";
            const humidity = data.humidity !== undefined ? data.humidity : "N/A";
            const motion = data.motion !== "N/A" ? "🚨 Motion Detected" : "No Motion";
            
            let fanState = data.fan === "ON" ? "✅ ON" : "❌ OFF";
            let lightState = data.light === "ON" ? "✅ ON" : "❌ OFF";

            // ✅ Update UI with latest sensor data
            document.getElementById("sensorDataContainer").innerHTML = `
                <h3>Sensor: ${data.sensor_id || "Unknown"}</h3>
                <p><b>Timestamp:</b> ${new Date(timestamp).toLocaleString()}</p>
                <p><b>Temperature:</b> ${temperature !== "N/A" ? temperature + " °C" : "No Data"}</p>
                <p><b>Humidity:</b> ${humidity !== "N/A" ? humidity + " %" : "No Data"}</p>
                <p><b>Motion:</b> ${motion}</p>
                <p><b>Fan State:</b> ${fanState}</p>
                <p><b>Light State:</b> ${lightState}</p>
            `;

            // ✅ Alert Logic
            if (temperature !== "N/A" && temperature > 25) {
                showAlert("🔥 High Temperature! Turning Fan ON!", "danger");
            }
            if (humidity !== "N/A" && humidity > 70) {
                showAlert("💧 High Humidity Levels Detected!", "warning");
            }
            if (data.motion !== "N/A") {
                showAlert("🚨 Motion Detected in the Area!", "info");
            }

            // ✅ Update Chart
            updateChart(timestamp, temperature, humidity);
        })
        .catch(err => console.error("❌ Fetch API Error:", err));
}

// ✅ Load historical data when page opens
window.onload = () => {
    fetchHistoricalData();
};

// ✅ Fetch new data every 3 seconds
setInterval(fetchSensorData, 3000);
fetchSensorData();
