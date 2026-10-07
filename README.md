# JoJo Water Tank Monitor for Home Assistant

**JoJo Tank Monitor** is an open-source Home Assistant custom integration for monitoring **JoJo Tanks and other water storage tanks** using **MQTT**, an Arduino-compatible controller and a **4–20 mA water-level / pressure sensor**.

It converts raw tank-sensor telemetry into useful Home Assistant entities such as **water level percentage, water depth, volume in litres, low-water status, refill detection, refill history and diagnostics**. The reference build uses an Arduino UNO R4 WiFi with a submersible pressure sensor, but the Home Assistant integration is designed around MQTT data and configurable calibration values.

This project is useful for anyone looking for a **Home Assistant water tank monitor**, **JoJo tank level sensor**, **MQTT water tank monitoring**, or a DIY **4–20 mA tank level monitoring** solution.

## Features

- Home Assistant custom integration with Config Flow
- HACS-compatible repository structure
- MQTT-based local communication
- Tank level percentage
- Water depth in millimetres
- Calculated water volume in litres
- Configurable tank capacity and tank height
- Configurable empty/full current calibration
- Raw ADC, voltage and current diagnostics
- Wi-Fi, uptime and firmware diagnostics
- Configurable low-water threshold with hysteresis
- Independent estimation reserve level
- Refill detection and persistent refill history
- Home Assistant Recorder support without requiring Grafana or InfluxDB
- Local processing with no cloud service required
- MIT licensed

## Reference Hardware

The current reference installation uses:

- JoJo 5,250 L vertical water tank
- Arduino UNO R4 WiFi
- 4–20 mA submersible pressure / level sensor
- DFRobot SEN0262 current-to-voltage converter
- 120 ohm sense resistor
- 24 V sensor power supply
- MQTT broker accessible to Home Assistant

Other tank sizes and compatible MQTT sensor sources can be used by changing the integration calibration and tank settings.

## Installation with HACS

Until the project is submitted to the default HACS repository, install it as a **custom repository**:

1. Open **HACS** in Home Assistant.
2. Go to **Integrations**.
3. Open the HACS menu and choose **Custom repositories**.
4. Add:

   ```text
   https://github.com/dmseclab/ha-jojo-tank
   ```

5. Select **Integration** as the repository category.
6. Find **JoJo Tank Monitor** in HACS and install it.
7. Restart Home Assistant if prompted.
8. Go to **Settings → Devices & services → Add Integration**.
9. Search for **JoJo Tank Monitor** and complete the configuration flow.

You can also download or clone the repository directly:

```bash
git clone https://github.com/dmseclab/ha-jojo-tank.git
```

## Current Project Status

> **Current stable development version:** v0.5.4. The project is still undergoing real-world validation before v1.0.0.

The HACS custom integration is the primary Home Assistant implementation. It provides native tank calculations, configurable calibration, refill detection/history, configurable low-water threshold with hysteresis, independent estimation reserve level and diagnostics. The legacy YAML/template calculation layer has been removed from the reference installation.

## Reference Installation Values

| Setting | Reference value |
| --- | ---: |
| Tank capacity | 5,250 L |
| Tank height | 1,850 mm |
| Empty calibration | 4.00 mA |
| Full calibration | 11.50 mA |
| Sense resistor | 120 ohm |
| Publish interval | 5 minutes |
| Refill detection threshold | 75 L |
| Refill end timeout | 15 minutes |
| Low water level | 20% (user configurable) |
| Estimation reserve level | 10% (user configurable) |
| Refill history retention | 60 days / max 100 events |

## Refill Detection and History

Version 0.6.0 promotes the field-tested beta filter to `main`. Refill detection uses a median of five readings, a recent low-water baseline and three consecutive filtered confirmations. The effective detection threshold is the greater of your configured threshold and **4% of tank capacity** (210 L on the reference 5,250 L tank). A 75 L configured setting therefore does not imply that a 75 L top-up will be detected. Small top-ups can be missed by this conservative filter.

At the reference five-minute publish interval, the filter needs about 20 minutes after a sustained step before confirmation, once its baseline is established. Tank level, available water, depth and raw diagnostics remain unsmoothed. Only refill detection is filtered.

Once a refill is confirmed, its end volume follows the filtered high-water mark. Rising readings keep the close-out timer active while the median catches up, including slow refills. When readings stop rising for the configured timeout, the integration closes the event and records:

```text
Refill amount = final refill volume - volume before refill
```

Completed events persist across Home Assistant restarts and contain `time`, `start_l`, `end_l` and `amount_l`. History is automatically limited to the latest 60 days and a maximum of 100 events.

Device restarts, retained startup messages and telemetry gaps longer than the greater of 15 minutes or the refill timeout establish a new baseline. In-progress refill detection is discarded across these boundaries. Completed history is preserved. Last Reading is the receipt time of the latest valid MQTT measurement and is unchanged by history/timer updates.

**Clear Refill Data** clears stored events, the last refill amount/time, active timers and detection candidates. It leaves Home Assistant Recorder statistics in place.

For the 0.6.0 changes, validation findings and upgrade steps, see [CHANGELOG](CHANGELOG.md) and [field validation](docs/validation-0.6.0.md).

The reference installation exposes this through `sensor.living_room_jojo_water_tank_refill_history`. A native Home Assistant Markdown card can render the event attribute as a Date/Time, Before, After and Added table without InfluxDB or Grafana.

## Home Assistant History Strategy

The reference Home Assistant installation uses native Recorder with 60-day retention. Dedicated InfluxDB and Grafana containers have therefore been retired for now. External time-series storage can be reconsidered when additional higher-volume telemetry such as EM50 energy monitoring is introduced.

## Roadmap

### Completed

- [x] Capture Revision 6 raw MQTT firmware
- [x] Document reference hardware and calibration values
- [x] Add sanitized Arduino firmware and setup notes
- [x] Build installable HACS custom integration
- [x] Create native Home Assistant device and sensor entities
- [x] Add UI configuration for tank capacity, height and calibration
- [x] Add native level, available-water and water-depth calculations
- [x] Add raw ADC, voltage, current, Wi-Fi, uptime and firmware diagnostics
- [x] Add configurable refill detection and timeout
- [x] Add persistent last-refill information
- [x] Add 60-day structured refill-event history
- [x] Calculate refill from start-to-end volume instead of summing intermediate rises
- [x] Add refill-history sensor and dashboard table design
- [x] Promote beta refill filtering to main with regression coverage
- [x] Share validated calculations across sensors, alarms and refill detection
- [x] Fix refill clearing and Last Reading timestamps
- [x] Configure Home Assistant Recorder for 60-day history
- [x] Retire InfluxDB/Grafana from the current reference design
- [x] Add configurable Low Water Level and binary sensor with hysteresis
- [x] Add independent Estimation Reserve Level
- [x] Add low-water notification and warning-light automations
- [x] Remove obsolete legacy YAML/template entities
- [x] Add local integration branding/icon
- [x] Add MIT open-source license and project disclaimer
- [x] Protect the default GitHub branch against deletion
- [x] Protect the default GitHub branch against force pushes
- [x] Verify authorised repository updates still work after enabling branch rules

### Current validation

- [ ] Validate the new start/end/net refill calculation during the next real tank refill
- [ ] Confirm a completed refill creates one correct history row after the 15-minute timeout
- [ ] Verify refill history survives a Home Assistant restart after a real event is stored
- [ ] Continue real-world validation of Low Water threshold/hysteresis behaviour
- [x] Replay 4–7 October history through MQTT callbacks with zero detected refill events

### Before v1.0 stable

- [ ] Remove obsolete Arduino MQTT Discovery publications/warnings if any remain
- [ ] Add/complete wiring documentation and diagram
- [ ] Complete clean-install, calibration and troubleshooting documentation
- [ ] Perform a clean HACS installation test on a fresh Home Assistant setup
- [ ] Publish v1.0.0 stable release

### Future development

- [ ] Water Used Today / Yesterday
- [ ] 7-day average daily water usage
- [ ] Estimated Days Remaining using Estimation Reserve Level
- [ ] Daily/weekly/monthly water-consumption reporting
- [ ] Leak or abnormal-consumption detection
- [ ] Additional notifications/automation examples
- [ ] Multiple-tank support
- [ ] Reconsider InfluxDB/Grafana if future telemetry justifies it

## Security and Repository Governance

Never commit Wi-Fi passwords, MQTT passwords, Home Assistant tokens, API keys or other credentials.

The repository is public for reading, reuse and forks. Public visibility does not grant direct write access to the original repository. The default branch is protected against deletion and force pushes. Normal updates remain available to explicitly authorised repository identities/connections, allowing the project's controlled maintenance workflow to continue.

External contributors should work through forks and pull requests rather than being granted direct write access unless explicitly authorised by the repository owner.

## License

This project is licensed under the MIT License. See `LICENSE` for the full license text.

Copyright (c) 2026 dmseclab
