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

## Ambient temperature correction (0.6.2 beta)

Optional correction uses the current `temperature` attribute of a Home Assistant weather entity, default `weather.forecast_home`. No firmware change is required. Enable it in **Configure → Tank Settings** after installing this beta. Existing installations remain disabled until explicitly enabled.

Trial defaults are **20°C reference**, **5 mm/°C**, and **75 mm maximum**:

`corrected depth = raw depth + min(75, max(0, temperature_C - 20) × 5)`

These are conservative starting settings, **not coefficients fitted to weather history**. The available August–October CSV contains `sensor.temp_1_temperature`, not the weather entity's temperature attribute. Consumption, refills and historical aggregation confound the apparent thermal slopes. The beta does not establish ±5% accuracy throughout the tank's operating range.

For illustration, 1755 mm at 35°C becomes 1830 mm, 3.7% below a 1900 mm manual reference. This assumes the weather temperature really is 35°C at that reading. The default usable full reference is now 1900 mm, based on repeated manual full readings; capacity remains 5250 L in the reference build. Existing installations must change Tank height to 1900 mm in Configure → Tank Settings: changing the default does not overwrite saved calibration. Empty and full currents remain unchanged. This height adjustment also scales raw calculated depth, so a reading previously calculated as 1755 mm at a height of 1850 mm becomes about 1802 mm before temperature correction. Physical depth can exceed the full reference; percentage and litres stop at 100% and configured capacity.

New diagnostics show **Raw Water Depth**, **Compensation Temperature**, **Temperature Correction**, and **Temperature Compensation** status. ADC, voltage and current remain unchanged. Correction is applied only to live MQTT snapshots. Offline readings keep their last known values; restored corrected snapshots remain marked stale until live telemetry arrives.

Weather must have a finite temperature in °C or °F, attributes updated within two hours, and a converted temperature within 0–45°C. Missing, unavailable, stale or invalid weather uses raw depth on the next live measurement. Correction is disabled for an empty raw measurement. Settings permit a 0–45°C reference, 0–10 mm/°C coefficient, and a hard 100 mm maximum cap.

Refill tracking shifts its stored detection values by the correction-only volume change, including weather fallback. A weather change alone cannot produce a refill. This guard does not identify every slow physical sensor recovery as temperature drift; physical refill accuracy still requires operational verification.

Disable the option to return to raw depth on the next live reading. This beta changes the depth display from an upper-clamped usable depth to physical depth; level and volume retain their existing limits.

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

> **Current development version on main:** v0.6.1. The project is still undergoing real-world validation before v1.0.0.

The HACS custom integration is the primary Home Assistant implementation. It provides native tank calculations, configurable calibration, refill detection/history, configurable low-water threshold with hysteresis, independent estimation reserve level and diagnostics. The legacy YAML/template calculation layer has been removed from the reference installation.

## Reference Installation Values

| Setting | Reference value |
| --- | ---: |
| Tank capacity | 5,250 L |
| Usable full water depth | 1,900 mm |
| Empty calibration | 4.00 mA |
| Full calibration | 11.50 mA |
| Sense resistor | 120 ohm |
| Publish interval | 5 minutes |
| Refill detection threshold | 75 L |
| Refill end timeout | 15 minutes |
| Arduino offline timeout | 15 minutes (user configurable) |
| Low water level | 20% (user configurable) |
| Estimation reserve level | 10% (user configurable) |
| Refill history retention | 60 days / max 100 events |

## Refill Detection and History

Version 0.6.1 uses **exactly the configured refill threshold**. There is no hidden minimum or capacity percentage override. The default is 75 L; the diagnostic Refill Threshold entity shows the active value. Refill detection still uses a median of five readings, a recent low-water baseline and three consecutive filtered confirmations. The threshold applies to the sustained filtered rise, so brief physical top-ups may still be missed. Lower settings are more sensitive to measurement recovery; use an explicit 210 L setting if you want the earlier beta's conservative threshold on the reference tank.

At the reference five-minute publish interval, the filter needs about 20 minutes after a sustained step before confirmation, once its baseline is established. Tank level, available water, depth and raw diagnostics remain unsmoothed. Only refill detection is filtered.

Once a refill is confirmed, its end volume follows the filtered high-water mark. Rising readings keep the close-out timer active while the median catches up, including slow refills. When readings stop rising for the configured timeout, the integration closes the event and records:

```text
Refill amount = final refill volume - volume before refill
```

Completed events persist across Home Assistant restarts and contain `time`, `start_l`, `end_l` and `amount_l`. History is automatically limited to the latest 60 days and a maximum of 100 events.

Device restarts, expired telemetry and long telemetry gaps establish a new baseline. In-progress detection is discarded across those boundaries. Completed history is preserved. Retained startup messages can seed an empty display but do not establish a new Last Reading, prove connectivity, override a stored live measurement or count toward a refill.

**Clear Refill Data** clears stored events, the last refill amount/time, active timers and detection candidates. It leaves Home Assistant Recorder statistics in place.

For changes, validation findings and upgrade steps, see [CHANGELOG](CHANGELOG.md) and [0.6.1 validation and Saturday reflash](docs/validation-0.6.1.md).

## Last Known Values and Connectivity

Tank measurements remain visible when telemetry stops. `Arduino Online` turns off after the configured timeout (15 minutes by default), and measurement entities receive `stale: true`. This status means no recent valid live MQTT measurement; it cannot distinguish Arduino failure from Wi-Fi or broker failure. Last Reading remains the original receipt time rather than advancing during an outage.

The last valid payload and receipt timestamp are stored and restored across Home Assistant restarts. Connectivity remains off until a valid live message arrives. On a first installation, a retained measurement has unknown age and Last Reading remains unknown until live telemetry arrives. Low Water retains its last known state and also exposes the stale attribute. Alarm automations should check Arduino Online when deciding whether to act on a current level.

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
- [x] Compare explicit 75 L and 210 L settings on September and October history
- [x] Verify setup, MQTT dispatch, expiry, recovery, settings and reload in a real HA test runtime

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
