#include <WiFi.h>
#include <WebServer.h>

// Motor control pins
const int PIN_DIR1 = 26;      // Motor 1 Direction
const int PIN_PWM1 = 25;      // Motor 1 PWM
const int PIN_BRAKE1 = 13;    // Motor 1 Brake
const int PIN_DIR2 = 14;      // Motor 2 Direction
const int PIN_PWM2 = 27;      // Motor 2 PWM
const int PIN_BRAKE2 = 17;    // Motor 2 Brake
const int PIN_SPEED = 12;     // Speed Pulse Output from Motor Controller


// LED Pins for modes and signal
#define USB_LED_PIN 2          // USB mode LED
#define WIFI_LED_PIN 4         // Wi-Fi mode LED
#define SIGNAL_LED_PIN 16      // Signal LED for random blinking

// Wi-Fi credentials
const char* ssid = "ESP32-Robot";
const char* password = "12345678";

WebServer server(80);

const unsigned long USB_TIMEOUT = 5000; // Timeout for USB inactivity (5 seconds)
unsigned long lastSerialTime = 0;
bool usbActive = false;
bool wifiActive = false;
int speed = 30; // Initial speed for USB mode (30 out of 255)

// Variables for speed measurement
double _kph = 0;
bool signalLedOn = false; // For random blinking of the signal LED

void setup() {
    Serial.begin(115200);

    // Set up motor control pins
    pinMode(PIN_DIR1, OUTPUT);
    pinMode(PIN_BRAKE1, OUTPUT);
    pinMode(PIN_PWM1, OUTPUT);
    pinMode(PIN_DIR2, OUTPUT);
    pinMode(PIN_BRAKE2, OUTPUT);
    pinMode(PIN_PWM2, OUTPUT);

    // Set up LEDs for modes
    pinMode(USB_LED_PIN, OUTPUT);
    pinMode(WIFI_LED_PIN, OUTPUT);
    pinMode(SIGNAL_LED_PIN, OUTPUT);

    // Initially turn off both mode LEDs
    digitalWrite(USB_LED_PIN, LOW);
    digitalWrite(WIFI_LED_PIN, LOW);
    digitalWrite(SIGNAL_LED_PIN, LOW);

    // Start Wi-Fi Access Point
    startWiFi();

    // Define routes
    server.on("/", handleRoot);
    server.on("/control", handleControl);
    server.on("/speed", handleSpeed); // Endpoint to get real-time speed
    server.begin();
    Serial.println("HTTP server started");
}

void loop() {
    // Handle Wi-Fi or USB Serial mode
    if (Serial.available()) {
        usbActive = true;
        lastSerialTime = millis();
        stopWiFi(); // Stop Wi-Fi when USB serial is active
        controlUSB();
    } else if (usbActive && millis() - lastSerialTime > USB_TIMEOUT) {
        usbActive = false;
        startWiFi(); // Re-enable Wi-Fi after USB inactivity
    }

    if (!usbActive) {
        server.handleClient(); // Only handle web clients in Wi-Fi mode
    }

    // Randomly blink the signal LED when the robot is on
    randomBlinkSignalLED();
}

// Control for USB commands
void controlUSB() {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "FORWARD") {
        forward();
    } else if (command == "BACKWARD") {
        backward();
    } else if (command == "LEFT") {
        left();
    } else if (command == "RIGHT") {
        right();
    } else if (command == "STOP") {
        applyBrakes();
    } else if (command.startsWith("SPEED")) {
        speed = command.substring(6).toInt();
        Serial.print("Speed set to: ");
        Serial.println(speed);
        adjustSpeed(speed);
    }
}

void startWiFi() {
    WiFi.softAP(ssid, password);
    IPAddress IP = WiFi.softAPIP();
    Serial.print("AP IP address: ");
    Serial.println(IP);
    wifiActive = true;
    digitalWrite(WIFI_LED_PIN, HIGH); // Wi-Fi LED ON
    digitalWrite(USB_LED_PIN, LOW);   // USB LED OFF
}

void stopWiFi() {
    WiFi.softAPdisconnect(true);
    wifiActive = false;
    digitalWrite(WIFI_LED_PIN, LOW);  // Wi-Fi LED OFF
    digitalWrite(USB_LED_PIN, HIGH);  // USB LED ON
}

// Handle root for web interface
void handleRoot() {
    server.send(200, "text/html", R"=====(<!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Robot Control</title>
    <style>body { font-family: Arial, sans-serif; text-align: center; }
           button { font-size: 20px; padding: 15px; margin: 5px; }
           .controls { margin-top: 20px; }
    </style></head>
    <body><h1>Robot Control</h1><div class="controls">
    <button onclick="sendCommand('dir', 'up')">Forward</button><br>
    <button onclick="sendCommand('dir', 'left')">Left</button>
    <button onclick="sendCommand('dir', 'stop')">Stop</button>
    <button onclick="sendCommand('dir', 'right')">Right</button><br>
    <button onclick="sendCommand('dir', 'down')">Backward</button></div>
    <div class="controls"><input type="range" min="0" max="255" value="0" id="speed" onchange="sendSpeed(this.value)">
    <label for="speed">Speed</label><p>Current Speed: <span id="currentSpeed">0</span> KPH</p></div>
    <script>function sendCommand(param, value) { fetch(`/control?${param}=${value}`); }
            function sendSpeed(value) { fetch(`/control?speed=${value}`); }
            function updateSpeed() { fetch('/speed').then(response => response.json())
            .then(data => { document.getElementById('currentSpeed').innerText = data.kph; }); }
            setInterval(updateSpeed, 500);</script></body></html>)=====");
}

void handleControl() {
    String dir = server.arg("dir");
    String speedStr = server.arg("speed");

    if (dir.length() > 0) {
        controlDirection(dir);
    }

    if (speedStr.length() > 0) {
        speed = speedStr.toInt();
        adjustSpeed(speed);
    }

    server.send(200, "text/plain", "OK");
}

void handleSpeed() {
    String json = "{\"kph\": " + String(_kph) + "}";
    server.send(200, "application/json", json);
}

// Direction control
void controlDirection(String dir) {
    if (dir == "up") forward();
    else if (dir == "down") backward();
    else if (dir == "left") left();
    else if (dir == "right") right();
    else if (dir == "stop") applyBrakes();
}

void forward() {
    digitalWrite(PIN_DIR1, LOW);  // Set motor 1 direction forward
    digitalWrite(PIN_DIR2, HIGH);  // Set motor 2 direction forward
    analogWrite(PIN_PWM1, speed);  // Set PWM for motor 1
    analogWrite(PIN_PWM2, speed);  // Set PWM for motor 2
    digitalWrite(PIN_BRAKE1, LOW); // Release brake for motor 1
    digitalWrite(PIN_BRAKE2, LOW); // Release brake for motor 2
}

void backward() {
    digitalWrite(PIN_DIR1, HIGH);   // Set motor 1 direction backward
    digitalWrite(PIN_DIR2, LOW);   // Set motor 2 direction backward
    analogWrite(PIN_PWM1, speed);  // Set PWM for motor 1
    analogWrite(PIN_PWM2, speed);  // Set PWM for motor 2
    digitalWrite(PIN_BRAKE1, LOW); // Release brake for motor 1
    digitalWrite(PIN_BRAKE2, LOW); // Release brake for motor 2
}

void left() {
    digitalWrite(PIN_DIR1, LOW);   // Set motor 1 backward
    digitalWrite(PIN_DIR2, LOW);  // Set motor 2 forward
    analogWrite(PIN_PWM1, speed);  // Set PWM for motor 1
    analogWrite(PIN_PWM2, speed);  // Set PWM for motor 2
    digitalWrite(PIN_BRAKE1, LOW); // Release brake for motor 1
    digitalWrite(PIN_BRAKE2, LOW); // Release brake for motor 2
}

void right() {
    digitalWrite(PIN_DIR1, HIGH);  // Set motor 1 forward
    digitalWrite(PIN_DIR2, HIGH);   // Set motor 2 backward
    analogWrite(PIN_PWM1, speed);  // Set PWM for motor 1
    analogWrite(PIN_PWM2, speed);  // Set PWM for motor 2
    digitalWrite(PIN_BRAKE1, LOW); // Release brake for motor 1
    digitalWrite(PIN_BRAKE2, LOW); // Release brake for motor 2
}

void applyBrakes() {
    digitalWrite(PIN_BRAKE1, HIGH); // Apply brake for motor 1
    digitalWrite(PIN_BRAKE2, HIGH); // Apply brake for motor 2
    analogWrite(PIN_PWM1, 0);       // Stop PWM for motor 1
    analogWrite(PIN_PWM2, 0);       // Stop PWM for motor 2
}

// Adjust speed for both motors
void adjustSpeed(int spd) {
    analogWrite(PIN_PWM1, spd);
    analogWrite(PIN_PWM2, spd);
}

// Blink signal LED randomly
void randomBlinkSignalLED() {
    if (random(0, 10) > 7) {
        signalLedOn = !signalLedOn;
        digitalWrite(SIGNAL_LED_PIN, signalLedOn ? HIGH : LOW);
    }
}
