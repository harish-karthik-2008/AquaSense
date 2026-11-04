/*
 * AquaSense AI - ESP32 Wokwi Simulation Node
 * Atomberg atomQUEST 2026 - Track 2: Water Purifier Monitoring
 *
 * Hardware & Pin Mapping:
 * - Microcontroller:         ESP32 DevKit V1
 * - TDS Potentiometer:       GPIO 34 (ADC1_CH6) -> 0 - 1000 ppm
 * - pH Potentiometer:        GPIO 35 (ADC1_CH7) -> 0.0 - 14.0 pH
 * - Turbidity Potentiometer: GPIO 32 (ADC1_CH4) -> 0.0 - 100.0 (Simulated Scale)
 * - Status LED:              GPIO 2  (Blinks during HTTP transmission)
 *
 * Networking:
 * - Wokwi-GUEST WiFi (automatic virtual NAT in Wokwi simulator)
 * - HTTP POST JSON payload to: /api/sensor-data
 */

#include <WiFi.h>
#include <HTTPClient.h>

// ======================== NETWORKING CONFIGURATION ========================
// In Wokwi simulator, always use "Wokwi-GUEST" with an empty password ("")
const char* ssid = "Wokwi-GUEST";
const char* password = "";

// --------------------------------------------------------------------------
// BACKEND / NGROK SERVER CONFIGURATION
// --------------------------------------------------------------------------
// In the Wokwi browser simulation, the ESP32 runs in a WebAssembly sandbox
// and cannot reach "localhost:8000" on your laptop directly.
//
// >>> DEVELOPER SETUP FOR ANOTHER LAPTOP: <<<
// 1. Start the AquaSense backend on your laptop:
//      cd backend
//      python -m uvicorn main:app --host 0.0.0.0 --port 8000
// 2. Start an ngrok tunnel on port 8000:
//      ngrok http 8000
// 3. Paste your public ngrok forwarding URL (or LAN IP) below:
//
// Examples:
//   - ngrok tunnel:    "https://your-tunnel-name.ngrok-free.app/api/sensor-data"
//   - ngrok http:      "http://your-tunnel-name.ngrok-free.dev/api/sensor-data"
//   - Local WiFi LAN:  "http://192.168.1.50:8000/api/sensor-data"
// --------------------------------------------------------------------------
const char* serverUrl = "https://YOUR-NGROK-SUBDOMAIN.ngrok-free.app/api/sensor-data";

// ======================== HARDWARE PIN DEFINITIONS ========================
const int PIN_TDS = 34;        // Potentiometer 1: TDS (0-1000 ppm)
const int PIN_PH = 35;         // Potentiometer 2: pH (0-14 pH)
const int PIN_TURBIDITY = 32;  // Potentiometer 3: Turbidity (0-100 index)
const int PIN_LED = 2;         // Onboard Status LED (Blinks on HTTP send)

// ======================== TIMING & THRESHOLDS =============================
unsigned long lastSendTime = 0;
const unsigned long sendInterval = 2500; // Heartbeat interval: every 2.5 seconds

// Previous readings for real-time slider change detection
float prevTDS = -1.0;
float prevPH = -1.0;
float prevTurbidity = -1.0;

// ======================== HELPER FUNCTIONS ================================
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
  Serial.println("  AquaSense AI - ESP32 Wokwi Sensor Node  ");
  Serial.println("  Atomberg atomQUEST 2026 Purifier Monitor");
  Serial.println("==========================================");

  // Set ADC resolution for full 0 - 3.3V range (12-bit: 0 - 4095)
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);

  // Connect to Wokwi virtual WiFi
  Serial.print("[WiFi] Connecting to: ");
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
    Serial.print("[WiFi] Virtual IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n[WiFi] Connection pending. Reading sensors locally...");
  }

  Serial.print("[HTTP] Target Endpoint: ");
  Serial.println(serverUrl);
  Serial.println("==========================================\n");
}

void loop() {
  // Read analog voltages (0 - 4095)
  float rawTDS = readSmoothAnalog(PIN_TDS);
  float rawPH = readSmoothAnalog(PIN_PH);
  float rawTurb = readSmoothAnalog(PIN_TURBIDITY);

  // Convert raw 12-bit ADC (0 - 4095) to physical & simulated parameters:
  // 1. TDS: 0.0 - 1000.0 ppm
  float tds = (rawTDS / 4095.0) * 1000.0;
  tds = round(tds * 10.0) / 10.0;

  // 2. pH: 0.00 - 14.00 pH
  float ph = (rawPH / 4095.0) * 14.0;
  ph = round(ph * 100.0) / 100.0;

  // 3. Turbidity: 0.0 - 100.0 (Simulated index based on Wokwi potentiometer)
  float turbidity = (rawTurb / 4095.0) * 100.0;
  turbidity = round(turbidity * 10.0) / 10.0;

  // Check if potentiometer was turned significantly (> 10 ppm TDS, > 0.25 pH, or > 2.0 Turbidity)
  bool valueChanged = false;
  if (prevTDS < 0 || abs(tds - prevTDS) > 10.0 || abs(ph - prevPH) > 0.25 || abs(turbidity - prevTurbidity) > 2.0) {
    valueChanged = true;
  }

  unsigned long currentMillis = millis();

  // Send if 2.5s elapsed OR immediately if user turned a potentiometer
  if (valueChanged || (currentMillis - lastSendTime >= sendInterval)) {
    lastSendTime = currentMillis;
    prevTDS = tds;
    prevPH = ph;
    prevTurbidity = turbidity;

    // Format JSON payload with simulated: true flag
    char jsonBuffer[256];
    snprintf(
      jsonBuffer,
      sizeof(jsonBuffer),
      "{\"tds\":%.1f,\"ph\":%.2f,\"turbidity\":%.1f,\"device_id\":\"AquaSense-ESP32\",\"simulated\":true}",
      tds, ph, turbidity
    );

    // Print to Serial Monitor
    Serial.print("[Sensor Telemetry]: ");
    Serial.println(jsonBuffer);

    // Send HTTP POST if WiFi is connected
    if (WiFi.status() == WL_CONNECTED) {
      digitalWrite(PIN_LED, HIGH); // Flash Status LED during transmission
      HTTPClient http;
      http.begin(serverUrl);
      http.addHeader("Content-Type", "application/json");
      // Bypass ngrok free tier browser warning interstitial
      http.addHeader("ngrok-skip-browser-warning", "true");
      http.setTimeout(3000);

      int httpResponseCode = http.POST(jsonBuffer);

      if (httpResponseCode > 0) {
        Serial.print("[HTTP] Success (Status ");
        Serial.print(httpResponseCode);
        Serial.println(")");
        if (httpResponseCode == 200 || httpResponseCode == 201) {
          String response = http.getString();
          Serial.println("[HTTP] Backend accepted reading.");
        }
      } else {
        Serial.print("[HTTP] POST failed, error: ");
        Serial.println(http.errorToString(httpResponseCode).c_str());
        Serial.println("[Tip] Verify backend is running and ngrok URL in sketch.ino is active.");
      }
      http.end();
      digitalWrite(PIN_LED, LOW);
    }
  }

  delay(150);
}

