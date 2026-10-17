# Troubleshooting

Use this guide from the physical signal path toward Home Assistant: **sensor -> SEN0262/interface -> Arduino -> Wi-Fi -> MQTT broker -> JoJo Tank Monitor integration**. Avoid changing calibration merely to hide a connectivity or wiring problem.

## Arduino Online is offline

`Arduino Online` means Home Assistant has received a recent valid live MQTT measurement. Offline can therefore mean Arduino power loss, Wi-Fi loss, MQTT/broker failure, routing failure or simply no valid telemetry within the configured timeout.

Check Arduino power and Serial Monitor first, then Wi-Fi connectivity and MQTT broker reachability. Confirm the configured MQTT topic matches the firmware state topic. Last-known tank measurements intentionally remain visible during an outage and are marked stale; this is expected behaviour, not proof that the Arduino is still online.

## Values are visible but stale

This is expected after telemetry expires. The integration preserves the last valid measurement rather than replacing the tank with `unavailable`. `Last Reading` remains the time the last valid live payload was received. Fix the telemetry path; do not clear storage or recalibrate the tank merely because data is stale.

## No entities or no readings after installation

Confirm the Home Assistant MQTT integration is configured and connected. Confirm JoJo Tank Monitor was added under **Settings -> Devices & services**, and verify its configured MQTT topic. The v1 firmware does not use Home Assistant MQTT Discovery; entity creation belongs to the custom integration.

Use an MQTT client to inspect the configured state topic. A valid payload contains fields such as `raw_adc`, `voltage_mv`, `current_raw_ma`, `wifi_rssi`, `uptime_seconds` and `firmware`.

## Duplicate legacy MQTT entities

Firmware 6.1.0 and older could publish Home Assistant MQTT Discovery configuration. Firmware 6.2.0 removes discovery publication, but retained discovery `config` messages may still exist in the broker. Confirm the custom integration is working before deleting old retained discovery configuration/entities. Never delete the live raw state topic used by JoJo Tank Monitor.

## Tank percentage, depth or litres look wrong

Check in this order:

1. Raw ADC changes when the water level changes.
2. Sensor Voltage is plausible for the raw ADC.
3. Sensor Current is plausible for the voltage and configured 120 ohm sense resistance.
4. Empty/full current calibration matches the installation.
5. Tank height and capacity are correct.

The reference installation uses 4.00 mA empty, 11.50 mA full, 1900 mm usable full depth and 5250 L capacity. These are reference values, not universal values for every sensor/tank.

Physical calculated depth may exceed the configured full depth because of sensor tolerance/noise. Tank percentage and litres are intentionally capped at 100% and configured capacity.

## Raw ADC / voltage / current are implausible

Check the physical circuit before changing software. The reference installation follows DFRobot's standard 4–20 mA liquid-level arrangement closely and uses Arduino input A2. Verify sensor polarity, supply voltage, loop wiring, SEN0262/interface wiring, the 120 ohm sense resistance and common/reference connections against the actual hardware and DFRobot documentation:

https://wiki.dfrobot.com/kit0139/docs/18950

Do not apply a wiring diagram blindly to a transmitter with a different datasheet or pinout.

## Refill was not detected

Refill detection is deliberately filtered to reject noise. It uses the configured refill threshold, a median of recent readings and sustained confirmation. A brief top-up can therefore be too small or too short to qualify. Confirm that the actual sustained increase exceeded the configured threshold before lowering it.

The reference threshold is 75 L. Lower thresholds increase sensitivity to measurement recovery/noise.

## Refill looks duplicated or incorrect

Check the refill history start/end values and the raw level history around the event. A refill remains open while filtered readings continue rising and closes after the configured timeout. Do not count intermediate rises as separate physical refills. Device restarts or long telemetry gaps establish a new detection baseline rather than continuing an uncertain in-progress event.

## Low Water does not switch where expected

Check the configured Low Water Level. The binary sensor uses hysteresis to prevent rapid on/off switching near the threshold, so its recovery point is intentionally not identical to its trip point. Also check `Arduino Online`; stale last-known values should not be treated as proof of the current physical water level.

## Temperature compensation makes the reading worse

Disable it. Temperature correction is optional and disabled by default. The reference installation met its accuracy target without requiring compensation. Only enable correction after comparing simultaneous manual and electronic depths across a useful temperature range.

Invalid, unavailable or stale weather data falls back to raw depth for live measurements.

## Home Assistant restart/reload behaviour

The last valid measurement and completed refill history are persisted. After restart, stored values may reappear before a new live MQTT message arrives; this does not prove current connectivity. Arduino Online should only recover when valid live telemetry is received.

## HACS update appears not to take effect

Confirm HACS installed the expected version, restart Home Assistant when requested, and inspect the integration manifest/version if necessary. Browser/frontend caches can delay visible wording changes, but entity behaviour should follow the installed backend code after HA restart.

## Firmware upload problems

Use Arduino IDE with the UNO R4 WiFi board selected. Install `ArduinoMqttClient` and `ArduinoJson` if compilation reports missing headers. Preserve your local Wi-Fi/MQTT credentials when replacing the sketch and never commit those credentials to the public repository.

After upload, use Serial Monitor at 9600 baud and confirm Wi-Fi connection, MQTT connection and `MQTT state published.` before troubleshooting Home Assistant.

## Before reporting a defect

Capture the integration version, firmware version, relevant configured values, the raw MQTT payload (with credentials removed), Arduino Online/Last Reading status and the approximate time of the event. For calculation/refill issues, include a short Home Assistant history export around the event when possible.
