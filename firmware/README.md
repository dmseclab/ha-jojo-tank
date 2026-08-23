# Arduino Firmware

This folder contains the Arduino firmware used by the JoJo Tank Monitor reference installation.

The current reference firmware is located at:

```text
arduino_uno_r4_wifi/jojo_tank_mqtt.ino
```

## Reference hardware

- Arduino UNO R4 WiFi-compatible board
- DFRobot SEN0262-family submersible liquid-level / pressure sensor
- Sensor interface/converter
- 120 ohm sense resistor
- Sensor connected to analog input `A2`

## Arduino IDE requirements

Before compiling the firmware, install/select the Arduino UNO R4 WiFi board support package in Arduino IDE.

The sketch uses these libraries:

| Library | Source | Notes |
| --- | --- | --- |
| `WiFiS3` | Arduino UNO R4 WiFi board package | Normally installed with the board support package |
| `ArduinoMqttClient` | Arduino | Install using Arduino IDE Library Manager |
| `ArduinoJson` | Benoit Blanchon | Install using Arduino IDE Library Manager |

### Installing the required libraries

In Arduino IDE:

1. Open **Tools -> Manage Libraries...** or open **Library Manager** from the sidebar.
2. Search for `ArduinoMqttClient`.
3. Install **ArduinoMqttClient by Arduino**.
4. Search for `ArduinoJson`.
5. Install **ArduinoJson by Benoit Blanchon**.
6. Select the correct Arduino UNO R4 WiFi board and COM/serial port.
7. Open `jojo_tank_mqtt.ino` and click **Verify** before uploading.

If compilation reports:

```text
fatal error: ArduinoMqttClient.h: No such file or directory
```

install `ArduinoMqttClient` from Library Manager and compile again.

If compilation reports that `ArduinoJson.h` cannot be found, install `ArduinoJson` from Library Manager.

## Configure Wi-Fi and MQTT

Before uploading, edit only the installation-specific values in the `USER CONFIG` section of the sketch:

```cpp
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* MQTT_BROKER   = "192.168.1.100";
const int   MQTT_PORT     = 1883;
const char* MQTT_USER     = "YOUR_MQTT_USERNAME";
const char* MQTT_PASS     = "YOUR_MQTT_PASSWORD";
```

Do not commit real Wi-Fi passwords, MQTT passwords, tokens, or other credentials to the public repository.

## Firmware behaviour

Revision 6 is intentionally a raw sensor publisher. The Arduino publishes raw measurement and diagnostic data over MQTT; tank-specific calculations are performed by the JoJo Tank Monitor Home Assistant integration.

Current raw/diagnostic data includes:

- Raw ADC
- Sensor voltage
- Sensor current
- Wi-Fi signal strength
- Uptime
- Firmware version

Tank capacity, tank height, empty/full calibration, calculated percentage, available litres, water depth and refill detection belong to the Home Assistant integration rather than the Arduino firmware.

The reference firmware publishes measurements every five minutes.

## Upload and initial test

After a successful upload, open **Serial Monitor** at **9600 baud**. A normal startup should show Wi-Fi connection, MQTT connection, Home Assistant discovery publication and a raw sensor reading.

Example sequence:

```text
JoJo Tank Raw Monitor - Revision 6
Firmware: 6.0.0
Publish interval: 5 minutes
Connecting to WiFi...
WiFi OK - IP: ...
Connecting to MQTT... MQTT OK
Removing obsolete Rev 5a discovery entities...
Publishing Rev 6 Home Assistant discovery...
Discovery complete.
Raw ADC: ... | Voltage: ... mV | Current: ... mA | RSSI: ... dBm
MQTT state published.
```

After installing the Arduino at the tank, confirm that the JoJo Tank Monitor integration in Home Assistant continues to receive fresh readings before removing any legacy MQTT or Home Assistant entities.
