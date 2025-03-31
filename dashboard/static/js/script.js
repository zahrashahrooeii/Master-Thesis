// 📌 Global variables for chart data
let timestamps = [];
let temperatures = [];
let humidities = [];
const maxDataPoints = 50; // Limit data points for better performance
let alertSound = new Audio("/static/audio/alert.mp3"); // 🔊 Sound alert

// ✅ Function to fetch latest sensor data and update the left card
function fetchLatestSensorData() {
    fetch("/api/latest-readings")
    .then(response => response.json())
    .then(data => {
        if (data.status === "error") {
            document.getElementById("sensor-id").innerText = "⚠️ No data found";
            return;
        }

        document.getElementById("sensor-id").innerText = `Sensor: ${data.sensor_id}`;
        document.getElementById("timestamp").innerText = `Timestamp: ${data.timestamp}`;
        document.getElementById("temperature").innerText = `Temperature: ${data.temperature}°C`;
        document.getElementById("humidity").innerText = `Humidity: ${data.humidity}%`;
        document.getElementById("motion").innerText = `Motion: ${data.motion}`;
        document.getElementById("fan-state").innerHTML = data.fan === "ON" ? "✅ ON" : "❌ OFF";
        document.getElementById("light-state").innerHTML = data.light === "ON" ? "✅ ON" : "❌ OFF";
    })
    .catch(error => console.error("Error fetching latest sensor data:", error));
}

// ✅ Auto-refresh latest sensor data every 5 seconds
fetchLatestSensorData();
setInterval(fetchLatestSensorData, 5000);


// ✅ Function to fetch historical sensor data and update the chart
function fetchHistoricalData(timeframe = "day") {
    fetch(`/api/historical-readings?timeframe=${timeframe}`)
        .then(response => response.json())
        .then(data => {
            if (!Array.isArray(data) || data.length === 0) {
                console.warn("⚠️ No historical data available.");
                alert("No historical data found!");
                return;
            }

            // Extract timestamps, temperatures, humidity
            const timestamps = data.map(entry => entry.timestamp);
            const temperatures = data.map(entry => entry.temperature);
            const humidity = data.map(entry => entry.humidity);

            // ✅ Update the chart with new data
            updateChart(timestamps, temperatures, humidity);
        })
        .catch(error => console.error("❌ Error fetching historical data:", error));
}


// ✅ Auto-refresh latest data every 5 seconds
setInterval(fetchLatestSensorData, 5000);
fetchLatestSensorData();

// ✅ Load historical data on page load (default: last 24 hours)
document.addEventListener("DOMContentLoaded", function () {
    fetchHistoricalData("day");
});

// 📌 Function to handle Signup
function signupUser() {
    let name = document.getElementById("name").value;
    let email = document.getElementById("email").value;
    let password = document.getElementById("password").value;

    fetch("/api/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        if (data.status === "success") {
            window.location.href = data.redirect;  // Redirect to OTP verification page
        }
    })
    .catch(error => console.error("❌ Error signing up:", error));
}

function loginUser() {
    let email = document.getElementById("login_email").value;
    let password = document.getElementById("login_password").value;

    fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        if (data.status === "success") {
            window.location.href = data.redirect;  // ✅ Redirect to dashboard
        }
    })
    .catch(error => console.error("Error:", error));
}

// 📌 Function to download the PDF
function downloadPDF() {
    fetch("/api/download_pdf")
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "sensor_report.pdf";
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        })
        .catch(err => console.error("❌ Error exporting PDF:", err));
}


// 📌 OTP Verification
function verifyOTP() {
    let email = document.getElementById("email").value;
    let otp = document.getElementById("otp").value;

    fetch("/api/verify_otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, otp })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        if (data.status === "success") {
            window.location.href = "/login_page"; // Redirect to login after successful verification
        }
    })
    .catch(error => console.error("❌ Error verifying OTP:", error));
}

// 📌 Resend OTP with countdown
let countdown = 60;
let interval;
function startResendTimer() {
    document.getElementById("resendBtn").disabled = true;
    interval = setInterval(() => {
        countdown--;
        document.getElementById("resendBtn").innerText = `Resend OTP (${countdown}s)`;
        if (countdown <= 0) {
            clearInterval(interval);
            document.getElementById("resendBtn").disabled = false;
            document.getElementById("resendBtn").innerText = "🔄 Resend OTP";
        }
    }, 1000);
}

function resendOTP() {
    fetch("/api/resend_otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: document.getElementById("email").value })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        if (data.status === "success") {
            countdown = 60;
            startResendTimer();
        }
    })
    .catch(error => console.error("❌ Error resending OTP:", error));
}
function updateChart(labels, tempData, humidityData) {
    const ctx = document.getElementById("sensorChart").getContext("2d");

    // ✅ FIX: Check if sensorChart exists before destroying
    if (window.sensorChart && typeof window.sensorChart.destroy === "function") {
        window.sensorChart.destroy();
    }

    window.sensorChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Temperature (°C)",
                    borderColor: "red",
                    data: tempData,
                    fill: false
                },
                {
                    label: "Humidity (%)",
                    borderColor: "blue",
                    data: humidityData,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}



// 📌 Toggle Dark Mode
document.getElementById("darkModeToggle").addEventListener("click", function() {
    document.body.classList.toggle("dark-mode");
    localStorage.setItem("darkMode", document.body.classList.contains("dark-mode") ? "enabled" : "disabled");
});
// 📌 Toggle Fan or Light
function toggleDevice(device) {
    fetch(`/api/control/${device}`, { method: "POST" })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                showAlert(`${device.toUpperCase()} state changed to ${data.new_state}!`, "success");
                updateDeviceUI(device, data.new_state);
            } else {
                showAlert("Failed to change device state.", "danger");
            }
        })
        .catch(err => console.error(`❌ Error toggling ${device}:`, err));
}

// 📌 Update UI Immediately
function updateDeviceUI(device, state) {
    document.getElementById(`${device}-state`).innerText = state === "ON" ? "✅ ON" : "❌ OFF";
}



// 📌 Function to show alert messages
function showAlert(message, type) {
    const alertBox = document.createElement("div");
    alertBox.className = `alert alert-${type} alert-dismissible fade show`;
    alertBox.innerHTML = `${message} <button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
    
    document.body.appendChild(alertBox);
    setTimeout(() => alertBox.remove(), 3000);
}
function checkFanAlert() {
    fetch("http://127.0.0.1:5000/api/fan_alert")
        .then(response => response.json())
        .then(data => {
            if (data.status === "warning") {
                showAlert(data.alert, "danger"); // 🔥 Show alert if warning exists
            }
        })
        .catch(error => console.error("⚠️ Error fetching fan alert:", error));
}

// ✅ Call the function every 10 seconds to check for alerts
setInterval(checkFanAlert, 10000);

// ✅ Function to Show Alert in UI
function showAlert(message, type) {
    let alertBox = document.createElement("div");
    alertBox.className = `alert alert-${type} fixed-alert`;
    alertBox.innerHTML = `<strong>${message}</strong>`;
    
    document.body.appendChild(alertBox);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        alertBox.remove();
    }, 5000);
}


// ✅ Run the check every 5 seconds
setInterval(checkFanAlert, 5000);

function showAlert(message, type) {
    let alertBox = document.createElement("div");
    alertBox.className = `alert alert-${type} fade show position-fixed top-0 end-0 m-3`;
    alertBox.innerHTML = `
        <strong>${message}</strong>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertBox);

    // ✅ Auto-hide after 5 seconds
    setTimeout(() => alertBox.remove(), 5000);
}

// ✅ Load Dark Mode Preference
window.onload = () => {
    if (localStorage.getItem("darkMode") === "enabled") {
        document.body.classList.add("dark-mode");
    }
    fetchLatestSensorData();
    fetchHistoricalData("day");
};
