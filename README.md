# JoJo Tank Monitor for Home Assistant

A reproducible DIY water-tank monitoring project using an Arduino-compatible controller, a submersible pressure level sensor, MQTT and Home Assistant.

> **Project status:** Reference Build / v0.1 development. The first goal is to preserve and document the known-working installation before packaging the Home Assistant side as a HACS custom integration.

## Overview
<img width="638" height="494" alt="JoJo1" src="https://github.com/user-attachments/assets/e072b129-69aa-4fcc-9ffc-0a8c6d0a755a" />
<img width="638" height="681" alt="JoJo2" src="https://github.com/user-attachments/assets/f832b154-4fa7-4778-8eff-c5c04bddf517" />
The reference system uses an Arduino to read raw sensor measurements and publish them to MQTT every five minutes. Home Assistant performs the tank-specific calibration and calculates water level, depth and volume.

This separation is intentional: the Arduino firmware does not need to know the tank capacity or height, so the same firmware can be reused with different tanks and calibration values.

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
     |- calibration
     |- level (%)
     |- volume (L)
     |- depth (mm)
     |- refill detection
     `- alarms/dashboard
```

## Reference Hardware

The original installation was developed around a 5,250 L JoJo water tank.

| Component | Reference hardware | Purpose |
| --- | --- | --- |
| Tank | JoJo 5,250 L water tank | Water storage |
| Level sensor | DFRobot Gravity Submersible Liquid Level / Tank Pressure Sensor (SEN0262 family) | Hydrostatic water-level measurement |
| Sensor interface | Interface/converter supplied with the sensor | Converts/conditions the sensor signal for the controller |
| Controller | Arduino UNO R4 WiFi-compatible board | Reads the sensor and publishes MQTT measurements |
| Home automation | Home Assistant | Calibration, calculations, history, refill detection and dashboard |
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

Tank capacity, tank height and empty/full calibration belong on the Home Assistant side. They are deliberately not hard-coded into Revision 6 of the Arduino firmware.

## Arduino Configuration

Before uploading the firmware, configure Wi-Fi and MQTT settings in the `USER CONFIG` section:

```cpp
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* MQTT_BROKER   = "192.168.1.100";
const int   MQTT_PORT     = 1883;
const char* MQTT_USER     = "YOUR_MQTT_USERNAME";
const char* MQTT_PASS     = "YOUR_MQTT_PASSWORD";
```

Never commit real Wi-Fi or MQTT credentials to a public repository.

## MQTT

The Revision 6 firmware publishes raw measurements to:

```text
homeassistant/sensor/jojo_tank/state
```

The Arduino publishes the raw ADC value, sensor voltage/current and diagnostic information. Tank-specific calculations remain in Home Assistant.

## Home Assistant Calculations

### Sensor current

```text
Current (mA) = Sensor voltage (mV) / 120 ohm
```

### Tank level

```text
Level (%) = (Current - Empty current) / (Full current - Empty current) x 100
```

The result should be constrained to 0-100%.

### Available volume

```text
Volume (L) = Level (%) / 100 x Tank capacity (L)
```

### Water depth

```text
Depth (mm) = Level (%) / 100 x Tank height (mm)
```

For the reference tank, capacity is 5,250 L and height is 1,850 mm.

## Calibration

Do not assume another sensor or installation will produce exactly the same full-scale current as the reference system.

For a new installation:

1. Confirm the electrical wiring and sense resistor.
2. Record the stable sensor current at the known empty/minimum reference point.
3. Fill the tank to the known full reference point.
4. Allow the sensor reading to stabilise.
5. Record Raw ADC, sensor voltage and calculated current.
6. Use the measured empty and full currents as the Home Assistant calibration limits.
7. Verify calculated percentage, depth and litres against known tank levels.

## Planned Repository Layout

```text
ha-jojo-tank/
|- README.md
|- hacs.json
|- LICENSE
|- firmware/
|  `- arduino_uno_r4_wifi/
|     `- jojo_tank_mqtt.ino
|- examples/
|  `- original-ha-config/
`- custom_components/
   `- jojo_tank/
```

The original Home Assistant configuration will be preserved as a known-working reference/fallback. The `custom_components/jojo_tank` directory will become the reusable HACS integration.

## Roadmap

- [x] Capture Revision 6 raw MQTT firmware
- [x] Document reference hardware and calibration values
- [ ] Add sanitized Arduino firmware
- [ ] Preserve original Home Assistant configuration
- [ ] Add wiring documentation/diagram
- [ ] Build HACS custom integration
- [ ] Add UI configuration for tank capacity, height and calibration
- [ ] Add refill detection
- [ ] Add daily/weekly/monthly consumption
- [ ] Add leak detection and estimated days remaining
- [ ] Add example dashboard
- [ ] Publish first stable release

## Security

Do not publish Wi-Fi passwords, MQTT passwords, Home Assistant tokens, API keys or other credentials. Example configuration in this repository uses placeholders only.

## License

A project license will be added before the first stable release.
