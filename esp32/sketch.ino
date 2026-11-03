/*
 * AquaSense AI - ESP32 Water Quality Sensor Node
 * Atomberg atomQUEST 2026 - Track 2: Water Purifier Hackathon
 * 
 * Hardware & Pin Mapping:
 * - ESP32 DevKit V1
 * - TDS Potentiometer:       GPIO 34 (ADC1_CH6) -> 0 - 1000 ppm
 * - pH Potentiometer:        GPIO 35 (ADC1_CH7) -> 0.0 - 14.0 pH
 * - Turbidity Potentiometer: GPIO 32 (ADC1_CH4) -> 0.0 - 100.0 (Simulated Scale)
 * - Status LED:              GPIO 2  (Blinks during HTTP transmission)
 * 
 * Networking:
 * - Wokwi-GUEST WiFi (automatic NAT in Wokwi simulator)
 * - Sends HTTP POST JSON payload to: http://<SERVER_HOST>:8000/api/sensor-data
 */

#include <WiFi.h>
#include <HTTPClient.h>

// ======================== CONFIGURATION ========================
// In Wokwi simulator, use "Wokwi-GUEST" with empty password
const char* ssid = "Wokwi-GUEST";
const char* password = "";

// Backend Server URL:
// - If using Wokwi IoT Gateway / local tunnel (ngrok / localtunnel):
//   Set this to your public tunnel URL, e.g. "https://xxxx.ngrok-free.app/api/sensor-data"
// - If running ESP32 on same local network as backend:
//   Set this to your machine's LAN IP, e.g. "http://192.168.1.50:8000/api/sensor-data"
// - Default local host address:
const char* serverUrl = "http://host.wokwi.internal:8000/api/sensor-data";

// Pin Definitions
const int PIN_TDS = 34;
const int PIN_PH = 35;
const int PIN_TURBIDITY = 32;
const int PIN_LED = 2;

// Transmission Timers
unsigned long lastSendTime = 0;
const unsigned long sendInterval = 2500; // Send heartbeat every 2.5 seconds
const float changeThresholdPct = 2.0;    // Or send immediately if changed > 2%

// Previous readings for change detection
float prevTDS = -1.0;
float prevPH = -1.0;
float prevTurbidity = -1.0;

// ======================== HELPER FUNCTIONS ========================
float readSmoothAnalog(int pin, int samples = 10) {
  long sum = 0;
  for (int i = 0; i < samples; i++) {
    sum += analogRead(pin);
    delayMicroseconds(200);
  }
  return (float)sum / (float)samples;
}

void setup() {
  Serial.begin(115200);
  delay(500);

  pinMode(PIN_TDS, INPUT);
  pinMode(PIN_PH, INPUT);
  pinMode(PIN_TURBIDITY, INPUT);
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, LOW);

  Serial.println("\n==========================================");
  Serial.println("  AquaSense AI - ESP32 Sensor Transmitter ");
  Serial.println("  Atomberg atomQUEST 2026 Purifier Monitor");
  Serial.println("==========================================");

  // Set ADC attenuation for full 0 - 3.3V range (12-bit: 0 - 4095)
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);

  // Connect to WiFi
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WiFi] Connected successfully!");
    Serial.print("[WiFi] IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n[WiFi] Note: WiFi pending. Will continue reading sensors locally.");
  }
}

void loop() {
  // Read analog inputs
  float rawTDS = readSmoothAnalog(PIN_TDS);
  float rawPH = readSmoothAnalog(PIN_PH);
  float rawTurb = readSmoothAnalog(PIN_TURBIDITY);

  // Convert raw 12-bit ADC (0 - 4095) to physical & simulated parameters:
  // 1. TDS: 0 - 1000 ppm
  float tds = (rawTDS / 4095.0) * 1000.0;
  tds = round(tds * 10.0) / 10.0;

  // 2. pH: 0.0 - 14.0 pH
  float ph = (rawPH / 4095.0) * 14.0;
  ph = round(ph * 100.0) / 100.0;

  // 3. Turbidity: 0.0 - 100.0 (Simulated scale based on Wokwi potentiometer)
  // IMPORTANT: Illustrative conversion formula for hackathon simulation, not calibrated NTU
  float turbidity = (rawTurb / 4095.0) * 100.0;
  turbidity = round(turbidity * 10.0) / 10.0;

  // Check if value changed significantly
  bool valueChanged = false;
  if (prevTDS < 0 || abs(tds - prevTDS) > 10.0 || abs(ph - prevPH) > 0.25 || abs(turbidity - prevTurbidity) > 2.0) {
    valueChanged = true;
  }

  unsigned long currentMillis = millis();

  // Send if interval passed OR if user adjusted potentiometer
  if (valueChanged || (currentMillis - lastSendTime >= sendInterval)) {
    lastSendTime = currentMillis;
    prevTDS = tds;
    prevPH = ph;
    prevTurbidity = turbidity;

    // Format JSON payload
    char jsonBuffer[200];
    snprintf(
      jsonBuffer,
      sizeof(jsonBuffer),
      "{\"tds\":%.1f,\"ph\":%.2f,\"turbidity\":%.1f,\"device_id\":\"AquaSense-ESP32\"}",
      tds, ph, turbidity
    );

    // Print to Serial Monitor
    Serial.print("[Sensor JSON]: ");
    Serial.println(jsonBuffer);

    // Send HTTP POST to Backend if WiFi is connected
    if (WiFi.status() == WL_CONNECTED) {
      digitalWrite(PIN_LED, HIGH); // Blink LED
      HTTPClient http;
      http.begin(serverUrl);
      http.addHeader("Content-Type", "application/json");
      http.setTimeout(2500);

      int httpResponseCode = http.POST(jsonBuffer);

      if (httpResponseCode > 0) {
        Serial.print("[HTTP] Success (Status ");
        Serial.print(httpResponseCode);
        Serial.println(")");
      } else {
        Serial.print("[HTTP] POST failed, error: ");
        Serial.println(http.errorToString(httpResponseCode).c_str());
        Serial.println("[HTTP Tip] Ensure backend is running and reachable at serverUrl.");
      }
      http.end();
      digitalWrite(PIN_LED, LOW);
    }
  }

  delay(150);
}

