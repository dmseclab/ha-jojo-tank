/***********************************************************
 * JoJo Water Tank Raw Sensor Monitor - Revision 6
 * Hardware : Arduino UNO R4 WiFi + DFRobot SEN0262
 * Protocol : MQTT -> Home Assistant Auto-Discovery
 *
 * Revision 6 design:
 * - Arduino publishes raw measurements only.
 * - Home Assistant calculates level, depth and volume.
 * - Measurements publish every 5 minutes.
 * - No Arduino-side tank calibration is required.
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
#define FIRMWARE_VERSION         "6.0.0"
#define MQTT_CLIENT_ID           "arduino_jojo_tank"
#define ANALOG_PIN               A2
#define VREF_MV                  5000.0f
#define SENSE_RESISTOR_OHM       120.0f
#define ADC_MAX_VALUE            1023.0f
#define ADC_SAMPLES              20
#define ADC_SAMPLE_DELAY_MS      10
#define SEND_INTERVAL            300000UL
#define WIFI_RETRY_INTERVAL      10000UL
#define MQTT_RETRY_INTERVAL      10000UL

#define MQTT_STATE_TOPIC         "homeassistant/sensor/jojo_tank/state"
#define MQTT_DISC_RAW_ADC        "homeassistant/sensor/jojo_tank_raw_adc/config"
#define MQTT_DISC_VOLTAGE        "homeassistant/sensor/jojo_tank_voltage_mv/config"
#define MQTT_DISC_CURRENT        "homeassistant/sensor/jojo_tank_current_raw_ma/config"
#define MQTT_DISC_RSSI           "homeassistant/sensor/jojo_tank_wifi_rssi/config"
#define MQTT_DISC_UPTIME         "homeassistant/sensor/jojo_tank_uptime/config"
#define MQTT_DISC_FIRMWARE       "homeassistant/sensor/jojo_tank_firmware/config"
#define MQTT_OLD_DISC_PCT          "homeassistant/sensor/jojo_tank_level_pct/config"
#define MQTT_OLD_DISC_DEPTH        "homeassistant/sensor/jojo_tank_depth_mm/config"
#define MQTT_OLD_DISC_VOL          "homeassistant/sensor/jojo_tank_volume_l/config"
#define MQTT_OLD_DISC_CURRENT_USED "homeassistant/sensor/jojo_tank_current_used_ma/config"

WiFiClient wifiClient;
MqttClient mqttClient(wifiClient);
unsigned long lastSend = 0;
unsigned long lastWiFiAttempt = 0;
unsigned long lastMQTTAttempt = 0;
bool discoveryPublished = false;

void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;
  unsigned long now = millis();
  if (lastWiFiAttempt != 0 && now - lastWiFiAttempt < WIFI_RETRY_INTERVAL) return;
  lastWiFiAttempt = now;
  Serial.print("Connecting to WiFi");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500); Serial.print("."); attempts++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("\nWiFi OK - IP: "); Serial.println(WiFi.localIP());
    Serial.print("WiFi RSSI: "); Serial.print(WiFi.RSSI()); Serial.println(" dBm");
  } else Serial.println("\nWiFi FAILED");
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
    Serial.println(" MQTT OK"); discoveryPublished = false; return true;
  }
  Serial.print(" MQTT FAILED, error: "); Serial.println(mqttClient.connectError()); return false;
}

void removeOldDiscoveryEntity(const char* topic) {
  mqttClient.beginMessage(topic, 0, true); mqttClient.endMessage(); delay(100);
}

void addDeviceInfo(JsonObject device) {
  device["identifiers"][0] = "jojo_tank";
  device["name"] = "JoJo Tank";
  device["manufacturer"] = "DIY";
  device["model"] = "Arduino UNO R4 WiFi + SEN0262";
  device["sw_version"] = FIRMWARE_VERSION;
}

void publishNumericSensor(const char* topic, const char* name, const char* uniqueId,
 const char* valueTemplate, const char* unit, const char* icon, int precision,
 const char* deviceClass = nullptr, const char* stateClass = "measurement") {
  StaticJsonDocument<640> doc;
  doc["name"] = name; doc["unique_id"] = uniqueId; doc["state_topic"] = MQTT_STATE_TOPIC;
  doc["value_template"] = valueTemplate; doc["unit_of_measurement"] = unit; doc["icon"] = icon;
  doc["suggested_display_precision"] = precision; doc["force_update"] = false;
  if (deviceClass != nullptr) doc["device_class"] = deviceClass;
  if (stateClass != nullptr) doc["state_class"] = stateClass;
  JsonObject device = doc.createNestedObject("device"); addDeviceInfo(device);
  char payload[640]; size_t length = serializeJson(doc, payload, sizeof(payload));
  mqttClient.beginMessage(topic, length, true); mqttClient.write((const uint8_t*)payload, length); mqttClient.endMessage();
  Serial.print("  Discovery: "); Serial.println(name); delay(150);
}

void publishTextSensor(const char* topic, const char* name, const char* uniqueId,
 const char* valueTemplate, const char* icon) {
  StaticJsonDocument<512> doc;
  doc["name"] = name; doc["unique_id"] = uniqueId; doc["state_topic"] = MQTT_STATE_TOPIC;
  doc["value_template"] = valueTemplate; doc["icon"] = icon;
  JsonObject device = doc.createNestedObject("device"); addDeviceInfo(device);
  char payload[512]; size_t length = serializeJson(doc, payload, sizeof(payload));
  mqttClient.beginMessage(topic, length, true); mqttClient.write((const uint8_t*)payload, length); mqttClient.endMessage();
  Serial.print("  Discovery: "); Serial.println(name); delay(150);
}

void publishDiscovery() {
  if (!mqttClient.connected()) return;
  Serial.println("Removing obsolete Rev 5a discovery entities...");
  removeOldDiscoveryEntity(MQTT_OLD_DISC_PCT); removeOldDiscoveryEntity(MQTT_OLD_DISC_DEPTH);
  removeOldDiscoveryEntity(MQTT_OLD_DISC_VOL); removeOldDiscoveryEntity(MQTT_OLD_DISC_CURRENT_USED);
  Serial.println("Publishing Rev 6 Home Assistant discovery...");
  publishNumericSensor(MQTT_DISC_RAW_ADC,"Raw ADC","jojo_tank_raw_adc","{{ value_json.raw_adc }}","","mdi:counter",0,nullptr,"measurement");
  publishNumericSensor(MQTT_DISC_VOLTAGE,"Sensor Voltage","jojo_tank_voltage_mv","{{ value_json.voltage_mv }}","mV","mdi:sine-wave",0,"voltage","measurement");
  publishNumericSensor(MQTT_DISC_CURRENT,"Sensor Current","jojo_tank_current_raw_ma","{{ value_json.current_raw_ma }}","mA","mdi:current-dc",2,"current","measurement");
  publishNumericSensor(MQTT_DISC_RSSI,"WiFi Signal","jojo_tank_wifi_rssi","{{ value_json.wifi_rssi }}","dBm","mdi:wifi",0,"signal_strength","measurement");
  publishNumericSensor(MQTT_DISC_UPTIME,"Uptime","jojo_tank_uptime_seconds","{{ value_json.uptime_seconds }}","s","mdi:timer-outline",0,"duration","total_increasing");
  publishTextSensor(MQTT_DISC_FIRMWARE,"Firmware","jojo_tank_firmware","{{ value_json.firmware }}","mdi:chip");
  discoveryPublished = true; Serial.println("Discovery complete.");
}

int readAveragedADC() {
  unsigned long total = 0;
  for (int i = 0; i < ADC_SAMPLES; i++) { total += analogRead(ANALOG_PIN); delay(ADC_SAMPLE_DELAY_MS); }
  return (int)(total / ADC_SAMPLES);
}

void readAndPublish() {
  if (!mqttClient.connected()) return;
  int raw = readAveragedADC();
  float voltageMv = (raw / ADC_MAX_VALUE) * VREF_MV;
  float currentRawMa = voltageMv / SENSE_RESISTOR_OHM;
  long wifiRssi = WiFi.RSSI(); unsigned long uptimeSeconds = millis() / 1000UL;
  Serial.print("Raw ADC: "); Serial.print(raw); Serial.print(" | Voltage: "); Serial.print(voltageMv, 0);
  Serial.print(" mV | Current: "); Serial.print(currentRawMa, 2); Serial.print(" mA | RSSI: ");
  Serial.print(wifiRssi); Serial.println(" dBm");
  StaticJsonDocument<320> doc;
  doc["raw_adc"] = raw; doc["voltage_mv"] = round(voltageMv);
  doc["current_raw_ma"] = round(currentRawMa * 100.0f) / 100.0f;
  doc["wifi_rssi"] = wifiRssi; doc["uptime_seconds"] = uptimeSeconds; doc["firmware"] = FIRMWARE_VERSION;
  char payload[320]; size_t length = serializeJson(doc, payload, sizeof(payload));
  mqttClient.beginMessage(MQTT_STATE_TOPIC, length, true); mqttClient.write((const uint8_t*)payload, length); mqttClient.endMessage();
  Serial.println("MQTT state published.");
}

void setup() {
  Serial.begin(9600); delay(1500); pinMode(ANALOG_PIN, INPUT);
  Serial.println("========================================"); Serial.println("JoJo Tank Raw Monitor - Revision 6");
  Serial.print("Firmware: "); Serial.println(FIRMWARE_VERSION); Serial.println("Publish interval: 5 minutes");
  Serial.println("Calibration is handled by Home Assistant"); Serial.println("========================================");
  connectWiFi();
  if (connectMQTT()) { publishDiscovery(); readAndPublish(); lastSend = millis(); }
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) { discoveryPublished = false; connectWiFi(); }
  if (WiFi.status() == WL_CONNECTED && !mqttClient.connected()) connectMQTT();
  if (mqttClient.connected()) {
    mqttClient.poll();
    if (!discoveryPublished) { publishDiscovery(); readAndPublish(); lastSend = millis(); }
    unsigned long now = millis();
    if (now - lastSend >= SEND_INTERVAL) { lastSend = now; readAndPublish(); }
  }
}
