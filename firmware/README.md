# Arduino Firmware

This folder contains the Arduino firmware used by the JoJo Tank Monitor reference installation.

The v1 release candidate firmware is **6.2.0**. The sketch is located at:

```text
arduino_uno_r4_wifi/jojo_tank_mqtt.ino
```

## Reference hardware and wiring

The reference installation uses:

- Arduino UNO R4 WiFi
- DFRobot SEN0262 current-to-voltage module / interface
- 4–20 mA submersible liquid-level sensor
- 120 ohm sense resistor
- 24 V sensor supply
- Sensor signal connected to Arduino analog input `A2`

The physical installation follows DFRobot's standard 4–20 mA liquid-level example closely. Use the official DFRobot diagram and instructions as the reference wiring source:

https://wiki.dfrobot.com/kit0139/docs/18950

The DFRobot page is a reference circuit, not a guarantee that every third-party 4–20 mA transmitter is wired identically. Verify the transmitter supply voltage, polarity, current-loop terminals, converter/module configuration and Arduino pinout against the hardware actually being installed before applying power. The reference JoJo installation uses A2; change `ANALOG_PIN` in the sketch if another analog input is used.

## Arduino IDE requirements

Install/select the Arduino UNO R4 WiFi board support package in Arduino IDE. The sketch uses `WiFiS3`, `ArduinoMqttClient` and `ArduinoJson`.

The CI build pins ArduinoMqttClient 0.1.8, ArduinoJson 6.21.5 and Arduino Renesas UNO board core 1.6.0. Select those versions to reproduce the verified build.

If compilation reports `ArduinoMqttClient.h: No such file or directory`, install ArduinoMqttClient from Library Manager. If `ArduinoJson.h` cannot be found, install ArduinoJson from Library Manager.

## Configure Wi-Fi and MQTT

Before uploading, edit only the installation-specific values in the `USER CONFIG` section:

```cpp
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* MQTT_BROKER   = "192.168.1.100";
const int   MQTT_PORT     = 1883;
const char* MQTT_USER     = "YOUR_MQTT_USERNAME";
const char* MQTT_PASS     = "YOUR_MQTT_PASSWORD";
```

Never commit real Wi-Fi passwords, MQTT passwords, Home Assistant tokens or other credentials to the public repository.

## Firmware behaviour

Revision 6.2 is intentionally a raw MQTT telemetry publisher. Home Assistant entity creation and all tank-specific calculations belong to the JoJo Tank Monitor custom integration. The firmware does **not** publish Home Assistant MQTT Discovery configuration.

Published data includes raw ADC, sensor voltage, sensor current, Wi-Fi signal strength, uptime and firmware version. The reference firmware publishes every five minutes to:

```text
homeassistant/sensor/jojo_tank/state
```

Example payload:

```json
{"raw_adc":281.0,"voltage_mv":1373.41,"current_raw_ma":11.4451,"wifi_rssi":-55,"uptime_seconds":3600,"firmware":"6.2.0"}
```

Tank capacity, tank height, empty/full calibration, percentage, available litres, water depth, low-water state, refill detection/history and optional temperature correction are handled by the Home Assistant integration.

The firmware keeps the 20-sample ADC average as a float and explicitly uses 10-bit ADC resolution (maximum 1023) to preserve the validated measurement scale. More decimal places do not imply corresponding sensor accuracy.

### Upgrading from firmware 6.1.0 or older

Firmware 6.2.0 removes legacy Home Assistant MQTT Discovery publication. Previously retained discovery `config` topics may remain in the MQTT broker after upgrading because retained messages survive firmware replacement. Remove obsolete discovery entities/configuration only after confirming that the JoJo Tank Monitor custom integration is receiving live telemetry. Do not delete the raw state topic used by the integration.

## Upload and initial test

After a successful upload, open Serial Monitor at **9600 baud**. A normal startup should resemble:

```text
JoJo Tank Raw Monitor - Revision 6.2
Firmware: 6.2.0
Publish interval: 5 minutes
Connecting to WiFi...
WiFi OK - IP: ...
Connecting to MQTT... MQTT OK
Raw ADC: ... | Voltage: ... mV | Current: ... mA | RSSI: ... dBm
MQTT state published.
```

Confirm in Home Assistant that `Arduino Online` becomes connected and that Raw ADC, Sensor Voltage, Sensor Current and Last Reading update before considering the upgrade complete.
