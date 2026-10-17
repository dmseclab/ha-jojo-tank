# Installation and calibration

This guide describes a new JoJo Tank Monitor installation. The reference build uses an Arduino UNO R4 WiFi, DFRobot SEN0262/interface, a 4–20 mA submersible level transmitter and MQTT.

## 1. Build and wire the sensor

Use DFRobot's official 4–20 mA liquid-level example as the reference circuit:

https://wiki.dfrobot.com/kit0139/docs/18950

The reference JoJo installation follows that arrangement closely and reads the signal on Arduino analog input A2. Verify your own transmitter supply voltage, polarity and pinout before applying power. See `firmware/README.md` for the reference hardware notes.

## 2. Prepare the Arduino firmware

Open `firmware/arduino_uno_r4_wifi/jojo_tank_mqtt.ino` in Arduino IDE. Select Arduino UNO R4 WiFi and install the required ArduinoMqttClient and ArduinoJson libraries. Configure only the Wi-Fi and MQTT values in the USER CONFIG section, then Verify and Upload.

Open Serial Monitor at 9600 baud. Confirm Wi-Fi connects, MQTT connects and a state payload is published. Firmware 6.2.0 publishes raw telemetry only; it does not create Home Assistant entities through MQTT Discovery.

## 3. Prepare Home Assistant and MQTT

Configure Home Assistant's MQTT integration and confirm it can reach the same broker used by the Arduino.

The reference firmware state topic is:

```text
homeassistant/sensor/jojo_tank/state
```

A different topic is supported when the integration and publisher are configured consistently.

## 4. Install with HACS

Until the project is included in HACS defaults, add the repository as a HACS custom repository of category **Integration**, install **JoJo Tank Monitor**, and restart Home Assistant if requested.

Then go to **Settings -> Devices & services -> Add Integration**, search for **JoJo Tank Monitor**, and complete the configuration flow.

## 5. Configure the tank

Reference installation values are:

| Setting | Reference value |
| --- | ---: |
| Tank capacity | 5250 L |
| Usable full depth | 1900 mm |
| Empty current | 4.00 mA |
| Full current | 11.50 mA |
| Sense resistor | 120 ohm |
| Refill threshold | 75 L |
| Publish interval | 5 minutes |
| Telemetry/offline timeout | 15 minutes |
| Estimation reserve | 10% |

These values describe the reference installation. Do not assume another transmitter/tank has identical calibration.

Temperature compensation should remain disabled initially. Enable it only if simultaneous manual/electronic measurements demonstrate a repeatable temperature-related error.

## 6. Calibrate and validate

With live telemetry present, compare Home Assistant Raw ADC, Sensor Voltage and Sensor Current with the expected electrical range. Confirm the calculated depth against a physical water-depth measurement at one or more known levels.

Set the full current/depth to match the real usable full-water condition rather than forcing the physical sensor to a nominal catalogue value. Percentage and available litres are capped at 100% and configured capacity even if sensor noise produces a physical depth slightly above the configured full reference.

For a new hardware combination, obtain at least an empty/low reference and a known high/full reference before treating the displayed litres as calibrated.

## 7. Operational validation

Confirm:

- Arduino Online is connected while live MQTT telemetry is arriving.
- Last Reading advances only on valid live measurements.
- Raw ADC, voltage and current are plausible.
- Water depth, percentage and available litres follow physical level changes.
- Low Water uses the intended threshold.
- A real refill above the configured threshold produces one completed refill-history event.
- Loss of telemetry preserves last-known values but marks them stale/offline.
- Telemetry recovery returns the device online automatically.

For a non-hardware acceptance test, follow `docs/CLEAN_INSTALL_VALIDATION.md` and use `tools/mqtt_simulator.py`.

## 8. Troubleshooting

See `docs/TROUBLESHOOTING.md` before changing calibration or firmware. Connectivity, stale telemetry and retained MQTT Discovery data can resemble measurement problems but require different fixes.
