# JoJo Tank Monitor for Home Assistant

A reproducible DIY water-tank monitoring project using an Arduino-compatible controller, a submersible pressure level sensor, MQTT and Home Assistant.

> **Project status:** v0.5.4 active development / pre-v1.0 validation. The HACS custom integration is the primary Home Assistant implementation and provides native tank calculations, configurable calibration, refill detection/history, a configurable low-water threshold with hysteresis, an independent estimation reserve level, diagnostics and local Home Assistant branding. The legacy YAML/template calculation layer has been removed from the reference installation.

## Overview
<img width="638" height="494" alt="JoJo1" src="https://github.com/user-attachments/assets/e072b129-69aa-4fcc-9ffc-0a8c6d0a755a" />
<img width="638" height="681" alt="JoJo2" src="https://github.com/user-attachments/assets/f832b154-4fa7-4778-8eff-c5c04bddf517" />

The reference system uses an Arduino to read raw sensor measurements and publish them to MQTT every five minutes. The JoJo Tank Monitor Home Assistant integration performs tank-specific calibration and calculates water level, depth and available volume.

This separation is intentional: the Arduino firmware does not need to know the tank capacity, height, warning threshold or estimation reserve, so the same firmware can be reused with different tanks and calibration values.

```text
Submersible pressure sensor
          |
          v
DFRobot interface/converter
          |
          v
Arduino UNO R4 WiFi-compatible board
          |
          | Wi-Fi / MQTT
          v
      MQTT Broker
          |
          v
   Home Assistant
          |
          v
 JoJo Tank Monitor
     |- calibration
     |- level (%)
     |- available water (L)
     |- depth (mm)
     |- low-water status
     |- refill detection
     |- refill history
     |- estimation reserve
     `- diagnostics
          |
          +--> notifications / automations
          `--> warning light
```

## Reference Hardware

The original installation was developed around a 5,250 L JoJo water tank.

| Component | Reference hardware | Purpose |
| --- | --- | --- |
| Tank | JoJo 5,250 L water tank | Water storage |
| Level sensor | DFRobot Gravity Submersible Liquid Level / Tank Pressure Sensor (SEN0262 family) | Hydrostatic water-level measurement |
| Sensor interface | Interface/converter supplied with the sensor | Converts/conditions the sensor signal for the controller |
| Controller | Arduino UNO R4 WiFi-compatible board | Reads the sensor and publishes MQTT measurements |
| Home automation | Home Assistant | Integration host, history, dashboards and automations |
| Transport | MQTT | Transfers measurements from the Arduino to Home Assistant |

### Hardware links

These links document hardware used by, or compatible with, the reference build. Equivalent components may also work.

- Sensor purchased from DIYElectronics: https://www.diyelectronics.co.za/store/liquid/4228-gravity-submersible-liquid-level-tank-pressure-sensor.html
- Example UNO R4 WiFi-compatible controller from Micro Robotics: https://www.robotics.org.za/UNO-R4-WIFI

The exact supplier of the controller used in the original installation is not known, so the controller link above is provided as a compatible example rather than a claim that it is the original board.

## Reference Installation Values

| Setting | Reference value |
| --- | ---: |
| Tank capacity | 5,250 L |
| Tank height | 1,850 mm |
| Empty calibration | 4.00 mA |
| Full calibration | 11.50 mA |
| Sense resistor | 120 ohm |
| Arduino analog input | A2 |
| ADC samples per reading | 20 |
| Publish interval | 5 minutes |
| Refill detection threshold | 75 L |
| Refill end timeout | 15 minutes |
| Low water level | 20% (user configurable) |
| Estimation reserve level | 10% (user configurable) |

Tank capacity, tank height, calibration, refill settings, low-water threshold and estimation reserve belong on the Home Assistant integration side. They are deliberately not hard-coded into the Arduino firmware.

**Low Water Level** and **Estimation Reserve Level** are independent. Low Water Level controls the warning binary sensor and associated automations. Estimation Reserve Level is reserved for the planned days-remaining calculation and can be set independently (for example, a 50% warning threshold with a 10% estimation reserve).

## Arduino Firmware

The reference firmware is Revision 6 / firmware `6.0.0` and publishes raw measurements rather than tank-specific calculated values.

Before compiling, install the required Arduino libraries for the UNO R4 WiFi firmware, including **ArduinoMqttClient**. Then configure Wi-Fi and MQTT settings in the firmware `USER CONFIG` section:

```cpp
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* MQTT_BROKER   = "192.168.1.100";
const int   MQTT_PORT     = 1883;
const char* MQTT_USER     = "YOUR_MQTT_USERNAME";
const char* MQTT_PASS     = "YOUR_MQTT_PASSWORD";
```

Never commit real Wi-Fi or MQTT credentials to a public repository. See the README/instructions in the firmware folder for firmware-specific setup notes.

## MQTT

The Revision 6 firmware publishes raw measurements to:

```text
homeassistant/sensor/jojo_tank/state
```

The physical Arduino/MQTT device can retain its raw diagnostic entities (for example Raw ADC, Sensor Voltage, Firmware, Uptime and Wi-Fi Signal). Tank calculations and operational status belong to the JoJo Tank Monitor integration.

## Home Assistant Calculations

### Sensor current

```text
Current (mA) = Sensor voltage (mV) / sense resistor (ohm)
```

### Tank level

```text
Level (%) = (Current - Empty current) / (Full current - Empty current) x 100
```

The integration constrains the result to 0-100%.

### Available volume

```text
Volume (L) = Level (%) / 100 x Tank capacity (L)
```

### Water depth

```text
Depth (mm) = Level (%) / 100 x Tank height (mm)
```

For the reference tank, capacity is 5,250 L and height is 1,850 mm.

### Low-water logic

The Low Water binary sensor uses the configured **Low Water Level**. It enters the low-water state at or below the threshold and uses a 2 percentage-point clear margin to prevent repeated toggling near the threshold.

Example: with Low Water Level set to 50%, the warning activates at 50% or below and clears only after the calculated level recovers above the hysteresis margin.

## Current Integration Entities

Entity IDs depend on the tank/device name and Home Assistant's entity registry. The IDs below are from the reference installation and should be treated as examples.

| Entity / example entity ID | Type | Purpose | Default state |
| --- | --- | --- | --- |
| `sensor.jojo_water_tank_tank_level` | Sensor | Calculated tank level | Enabled |
| `sensor.jojo_water_tank_available_water` | Sensor | Calculated available water in litres | Enabled |
| `sensor.jojo_water_tank_water_depth` | Sensor | Calculated water depth | Enabled |
| `sensor.jojo_water_tank_sensor_current` | Sensor | Sensor current calculated from voltage and sense resistor | Enabled |
| `sensor.jojo_water_tank_raw_adc` | Sensor | Raw ADC measurement received from MQTT | Enabled |
| `sensor.jojo_water_tank_sensor_voltage` | Sensor | Raw sensor voltage received from MQTT | Enabled |
| `sensor.jojo_water_tank_last_reading` | Sensor | Timestamp of the most recent integration reading | Enabled |
| `sensor.living_room_jojo_water_tank_minimum_water_level` | Diagnostic sensor | Configured **Low Water Level**; legacy entity ID is retained for upgrade compatibility | Enabled |
| `sensor.living_room_jojo_water_tank_estimation_reserve_level` | Diagnostic sensor | Independent reserve level for planned water-remaining estimation | Enabled |
| `binary_sensor.living_room_jojo_water_tank_low_water` | Binary sensor | Low-water problem state with 2% hysteresis | Enabled |
| `sensor.living_room_jojo_water_tank_refill_status` | Sensor | `Refilling` / `Not Refilling` | Enabled |
| `sensor.living_room_jojo_water_tank_last_refill_amount` | Sensor | Stored volume of the last detected refill | Enabled |
| `sensor.living_room_jojo_water_tank_last_refill_time` | Sensor | Timestamp of the last detected refill | Enabled |
| `sensor.living_room_jojo_water_tank_last_refill` | Sensor | Friendly last-refill display; shows `Never` until a refill is recorded | Enabled |
| Wi-Fi Signal | Diagnostic sensor | MQTT Wi-Fi RSSI exposed by integration | Disabled by default |
| Uptime | Diagnostic sensor | Arduino uptime exposed by integration | Disabled by default |
| Firmware | Diagnostic sensor | Arduino firmware version exposed by integration | Disabled by default |

The physical MQTT device in the reference installation also retains `sensor.jojo_tank_firmware`, `sensor.jojo_tank_raw_adc`, `sensor.jojo_tank_sensor_voltage`, `sensor.jojo_tank_uptime` and `sensor.jojo_tank_wifi_signal` for low-level hardware troubleshooting. These are source/diagnostic entities and are intentionally separate from the integration's calculated entities.

Legacy YAML/template entities such as `sensor.jojo_tank_level`, `sensor.jojo_tank_volume`, `sensor.jojo_tank_calculated_current`, `sensor.jojo_tank_current_display`, `sensor.jojo_tank_water_depth` and the old template refill entities are no longer required by the reference installation and have been removed.

## Configuration and Maintenance

Open **Settings -> Devices & services -> JoJo Tank Monitor -> Configure**.

The options menu currently provides:

- **Tank Settings** — tank dimensions, sensor calibration, refill settings, Low Water Level and Estimation Reserve Level.
- **Clear Refill Data** — deliberately clears stored refill amount/time without changing calibration, dimensions, MQTT readings or Home Assistant statistics.

Changing Low Water Level automatically changes the integration's Low Water binary sensor behaviour. Automations should therefore trigger from the Low Water binary sensor rather than hard-coding a percentage independently.

## Reference Automations

The reference Home Assistant installation currently uses the Low Water binary sensor for two functions:

1. A low-water/recovery notification.
2. A dedicated Living Room warning light. When Low Water is `on`, `light.living_room_light` is set to red at full brightness; when Low Water clears, the light is switched off.

The warning light is primarily dedicated to tank status in the reference installation. If a shared household light is used instead, consider preserving/restoring its previous state rather than always turning it off when the warning clears.

## Calibration

Do not assume another sensor or installation will produce exactly the same full-scale current as the reference system.

For a new installation:

1. Confirm the electrical wiring and sense resistor.
2. Record the stable sensor current at the known empty/minimum reference point.
3. Fill the tank to the known full reference point.
4. Allow the sensor reading to stabilise.
5. Record Raw ADC, sensor voltage and calculated current.
6. Enter the measured empty and full currents in the JoJo Tank Monitor integration configuration.
7. Verify calculated percentage, depth and litres against known tank levels.

## Repository Layout

```text
ha-jojo-tank/
|- README.md
|- hacs.json
|- LICENSE
|- firmware/
|  `- arduino_uno_r4_wifi/
|     |- README.md
|     `- jojo_tank_mqtt.ino
|- examples/
|  `- original-ha-config/
`- custom_components/
   `- jojo_tank/
      |- binary_sensor.py
      |- config_flow.py
      |- const.py
      |- sensor.py
      |- strings.json
      |- translations/
      `- brand/
```

The original Home Assistant configuration is retained in `examples/` as historical/reference material. The HACS integration is now the primary implementation and the reference Home Assistant instance no longer depends on the legacy JoJo template sensors/helpers.

## Roadmap

GitHub is the source of truth for the project roadmap.

### Completed

- [x] Capture Revision 6 raw MQTT firmware
- [x] Document reference hardware and calibration values
- [x] Add sanitized Arduino firmware and firmware setup notes
- [x] Preserve original Home Assistant configuration as reference/fallback
- [x] Build installable HACS custom integration
- [x] Create native Home Assistant device and sensor entities
- [x] Add UI configuration for tank capacity, height and calibration
- [x] Add configurable sense resistor
- [x] Add native level, available-water and water-depth calculations
- [x] Add raw ADC, voltage, current, Wi-Fi, uptime and firmware diagnostics
- [x] Add configurable refill detection
- [x] Add multi-reading refill accumulation and timeout
- [x] Add last refill amount/time and friendly `Never` state
- [x] Add persistent refill history across Home Assistant restarts
- [x] Add deliberate **Clear Refill Data** action
- [x] Add configurable **Low Water Level**
- [x] Add Low Water binary sensor with 2% hysteresis
- [x] Add independent **Estimation Reserve Level**
- [x] Add low-water notification/reference automation
- [x] Add low-water warning-light/reference automation
- [x] Remove obsolete legacy YAML/template entities from the reference installation
- [x] Add friendly configuration/menu labels and translations
- [x] Add local Home Assistant integration branding/icon
- [x] Add MIT open-source license and project disclaimer

### Current validation

- [ ] Validate native refill detection during a real tank refill
- [ ] Verify persisted refill amount/time after a Home Assistant restart following a real refill
- [ ] Continue real-world validation of Low Water threshold/hysteresis behaviour

### Before v1.0 stable

- [ ] Remove obsolete Arduino MQTT Discovery publications/warnings if any remain
- [ ] Add/complete wiring documentation and diagram
- [ ] Complete clean-install, calibration and troubleshooting documentation
- [ ] Perform a clean HACS installation test on a fresh Home Assistant setup
- [ ] Publish v1.0.0 stable release

### Future development

- [ ] Water Used Today
- [ ] Water Used Yesterday
- [ ] 7-day average daily water usage
- [ ] Estimated Days Remaining using the independent Estimation Reserve Level
- [ ] Daily/weekly/monthly water-consumption reporting
- [ ] Leak or abnormal-consumption detection
- [ ] Example Home Assistant dashboard
- [ ] Additional notifications/automation examples
- [ ] Multiple-tank support
- [ ] Re-enable/document InfluxDB and Grafana once integration behaviour and entity design are stable

## Security

Do not publish Wi-Fi passwords, MQTT passwords, Home Assistant tokens, API keys or other credentials. Example configuration in this repository uses placeholders only.

## Disclaimer

This project was developed for a specific private water-tank monitoring installation and is provided as a reference for others who may find it useful.

The software, firmware, wiring information, configuration examples and documentation are provided "as is", without warranty of any kind. Users are responsible for verifying the suitability, safety, calibration, electrical installation and operation of the system for their own environment.

Use of this project is entirely at your own risk and discretion.

## License

This project is licensed under the MIT License. See `LICENSE` for the full license text.

Copyright (c) 2026 dmseclab
