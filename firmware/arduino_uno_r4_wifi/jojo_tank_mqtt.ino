/***********************************************************
 * JoJo Water Tank Raw Sensor Monitor - Revision 6.2
 * Hardware : Arduino UNO R4 WiFi + DFRobot SEN0262
 * Protocol : MQTT raw telemetry
 *
 * Revision 6 design:
 * - Arduino publishes raw measurements only.
 * - Home Assistant calculations/entities belong to the JoJo Tank Monitor integration.
 * - Measurements publish every 5 minutes.
 * - No Arduino-side tank calibration or HA MQTT Discovery is required.
 ***********************************************************/

#include <WiFiS3.h>
#include <ArduinoMqttClient.h>
#include <ArduinoJson.h>

// =============================================
// USER CONFIG - CHANGE THESE VALUES
// =============================================
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* MQTT_BROKER   = "192.168.1.100";
const int   MQTT_PORT     = 1883;
const char* MQTT_USER     = "YOUR_MQTT_USERNAME";
const char* MQTT_PASS     = "YOUR_MQTT_PASSWORD";

// =============================================
// DEVICE CONFIG
// =============================================
#define FIRMWARE_VERSION         "6.2.0"
#define MQTT_CLIENT_ID           "arduino_jojo_tank"
#define ANALOG_PIN               A2
#define VREF_MV                  5000.0f
#define SENSE_RESISTOR_OHM       120.0f
#define ADC_MAX_VALUE            1023.0f
#define ADC_RESOLUTION_BITS      10
#define ADC_SAMPLES              20
#define ADC_SAMPLE_DELAY_MS      10
#define SEND_INTERVAL            300000UL
#define WIFI_RETRY_INTERVAL      10000UL
#define MQTT_RETRY_INTERVAL      10000UL

#define MQTT_STATE_TOPIC         "homeassistant/sensor/jojo_tank/state"

WiFiClient wifiClient;
MqttClient mqttClient(wifiClient);
unsigned long lastSend = 0;
unsigned long lastWiFiAttempt = 0;
unsigned long lastMQTTAttempt = 0;

void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;
  unsigned long now = millis();
  if (lastWiFiAttempt != 0 && now - lastWiFiAttempt < WIFI_RETRY_INTERVAL) return;
  lastWiFiAttempt = now;
  Serial.print("Connecting to WiFi");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("\nWiFi OK - IP: ");
    Serial.println(WiFi.localIP());
    Serial.print("WiFi RSSI: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
  } else {
    Serial.println("\nWiFi FAILED");
  }
}

bool connectMQTT() {
  if (mqttClient.connected()) return true;
  if (WiFi.status() != WL_CONNECTED) return false;
  unsigned long now = millis();
  if (lastMQTTAttempt != 0 && now - lastMQTTAttempt < MQTT_RETRY_INTERVAL) return false;
  lastMQTTAttempt = now;
  mqttClient.setUsernamePassword(MQTT_USER, MQTT_PASS);
  mqttClient.setId(MQTT_CLIENT_ID);
  Serial.print("Connecting to MQTT...");
  if (mqttClient.connect(MQTT_BROKER, MQTT_PORT)) {
    Serial.println(" MQTT OK");
    return true;
  }
  Serial.print(" MQTT FAILED, error: ");
  Serial.println(mqttClient.connectError());
  return false;
}

float readAveragedADC() {
  unsigned long total = 0;
  for (int i = 0; i < ADC_SAMPLES; i++) {
    total += analogRead(ANALOG_PIN);
    delay(ADC_SAMPLE_DELAY_MS);
  }
  return (float)total / ADC_SAMPLES;
}

void readAndPublish() {
  if (!mqttClient.connected()) return;
  float raw = readAveragedADC();
  float voltageMv = (raw / ADC_MAX_VALUE) * VREF_MV;
  float currentRawMa = voltageMv / SENSE_RESISTOR_OHM;
  long wifiRssi = WiFi.RSSI();
  unsigned long uptimeSeconds = millis() / 1000UL;

  Serial.print("Raw ADC: ");
  Serial.print(raw, 2);
  Serial.print(" | Voltage: ");
  Serial.print(voltageMv, 2);
  Serial.print(" mV | Current: ");
  Serial.print(currentRawMa, 2);
  Serial.print(" mA | RSSI: ");
  Serial.print(wifiRssi);
  Serial.println(" dBm");

  StaticJsonDocument<320> doc;
  doc["raw_adc"] = raw;
  doc["voltage_mv"] = round(voltageMv * 100.0f) / 100.0f;
  doc["current_raw_ma"] = round(currentRawMa * 10000.0f) / 10000.0f;
  doc["wifi_rssi"] = wifiRssi;
  doc["uptime_seconds"] = uptimeSeconds;
  doc["firmware"] = FIRMWARE_VERSION;

  char payload[320];
  size_t length = serializeJson(doc, payload, sizeof(payload));
  mqttClient.beginMessage(MQTT_STATE_TOPIC, length, true);
  mqttClient.write((const uint8_t*)payload, length);
  mqttClient.endMessage();
  Serial.println("MQTT state published.");
}

void setup() {
  Serial.begin(9600);
  delay(1500);
  pinMode(ANALOG_PIN, INPUT);
  analogReadResolution(ADC_RESOLUTION_BITS);
  Serial.println("========================================");
  Serial.println("JoJo Tank Raw Monitor - Revision 6.2");
  Serial.print("Firmware: ");
  Serial.println(FIRMWARE_VERSION);
  Serial.println("Publish interval: 5 minutes");
  Serial.println("Calibration and Home Assistant entities are handled by the JoJo Tank Monitor integration");
  Serial.println("========================================");
  connectWiFi();
  if (connectMQTT()) {
    readAndPublish();
    lastSend = millis();
  }
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) connectWiFi();
  if (WiFi.status() == WL_CONNECTED && !mqttClient.connected()) {
    if (connectMQTT()) {
      readAndPublish();
      lastSend = millis();
    }
  }
  if (mqttClient.connected()) {
    mqttClient.poll();
    unsigned long now = millis();
    if (now - lastSend >= SEND_INTERVAL) {
      lastSend = now;
      readAndPublish();
    }
  }
}
