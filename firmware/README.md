# Arduino Firmware

This folder contains the Arduino firmware used by the JoJo Tank Monitor reference installation.

The prepared firmware is **6.1.0**, intended for the next hardware reflash. The reference installation was still on 6.0.0 when these changes were prepared. The sketch is located at:

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

The CI build pins `ArduinoMqttClient` 0.1.8, `ArduinoJson` 6.21.5 and the Arduino Renesas UNO board core 1.6.0. Select those versions to reproduce the verified build.

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

Firmware 6.1.0 keeps the 20-sample ADC average as a float rather than truncating it to an integer. `raw_adc` can now contain decimals, voltage is published to two decimal places in mV and current to four in mA. ADC resolution is explicitly kept at 10 bits (maximum 1023) for the first comparison reflash. This preserves the voltage scale; higher resolution requires a separate change to both resolution and maximum count, followed by measurement validation. More decimal places do not establish corresponding sensor accuracy.

`ENABLE_MQTT_DISCOVERY` defaults to `true` to preserve existing discovery-based dashboards. Set it to `false` for a new custom-integration-only installation. This does not remove old retained discovery configurations. Export/check entity dependencies before removing legacy discovery data manually.

See the [Saturday reflash checklist](../docs/validation-0.6.1.md). Retain your local Wi-Fi and broker settings when preparing the upload. No broker or Home Assistant IP change is required.

## Upload and initial test

After a successful upload, open **Serial Monitor** at **9600 baud**. A normal startup should show Wi-Fi connection, MQTT connection, Home Assistant discovery publication and a raw sensor reading.

Example sequence:

```text
JoJo Tank Raw Monitor - Revision 6
Firmware: 6.1.0
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
