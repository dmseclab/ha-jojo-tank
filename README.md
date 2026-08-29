# JoJo Tank Monitor for Home Assistant

A reproducible DIY water-tank monitoring project using an Arduino-compatible controller, a submersible pressure level sensor, MQTT and Home Assistant.

> **Project status:** v0.5.4 active development / pre-v1.0 validation. The HACS custom integration is the primary Home Assistant implementation and provides native tank calculations, configurable calibration, refill detection/history, a configurable low-water threshold with hysteresis, an independent estimation reserve level, diagnostics and local Home Assistant branding. The legacy YAML/template calculation layer has been removed from the reference installation.

## Overview

The reference system uses an Arduino to read raw sensor measurements and publish them to MQTT every five minutes. The JoJo Tank Monitor Home Assistant integration performs tank-specific calibration and calculates water level, depth and available volume.

```text
Submersible pressure sensor -> Arduino -> MQTT -> Home Assistant -> JoJo Tank Monitor
                                                        |
                                                        +-- level / litres / depth
                                                        +-- low-water status
                                                        +-- refill detection
                                                        +-- 60-day refill history
                                                        `-- diagnostics
```

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

A refill begins when the calculated volume rises by at least the configured refill threshold between readings. Further qualifying rises during the configured timeout are treated as part of the same physical refill. When the timeout expires, the integration closes the event and records the net refill as:

```text
Refill amount = final refill volume - volume before refill
```

This avoids inflating the refill total by summing intermediate measurement steps.

Completed refill events are persisted by the integration across Home Assistant restarts. History is automatically trimmed to the most recent 60 days with an additional maximum of 100 events.

Each history event contains:

- `time`
- `start_l`
- `end_l`
- `amount_l`

The reference installation exposes this through `sensor.living_room_jojo_water_tank_refill_history`. The sensor state is the number of retained events and its `events` attribute contains the event records.

The reference dashboard now includes a refill verification card, water-level verification graph and a Markdown refill-history table. The table displays Date/Time, Before, After and Added values directly from the integration's persisted event history without requiring InfluxDB or Grafana.

## Current Integration Entities

Entity IDs depend on the tank/device name and Home Assistant's entity registry. The IDs below are examples from the reference installation.

| Entity / example entity ID | Purpose |
| --- | --- |
| `sensor.jojo_water_tank_tank_level` | Calculated tank level |
| `sensor.jojo_water_tank_available_water` | Calculated available water in litres |
| `sensor.jojo_water_tank_water_depth` | Calculated water depth |
| `sensor.jojo_water_tank_sensor_current` | Calculated sensor current |
| `sensor.jojo_water_tank_raw_adc` | Raw ADC received from MQTT |
| `sensor.jojo_water_tank_sensor_voltage` | Raw sensor voltage |
| `sensor.jojo_water_tank_last_reading` | Most recent integration reading |
| `sensor.living_room_jojo_water_tank_minimum_water_level` | Configured Low Water Level |
| `sensor.living_room_jojo_water_tank_estimation_reserve_level` | Independent estimation reserve |
| `binary_sensor.living_room_jojo_water_tank_low_water` | Low-water problem state with hysteresis |
| `sensor.living_room_jojo_water_tank_refill_status` | Refilling / Not Refilling |
| `sensor.living_room_jojo_water_tank_last_refill_amount` | Last completed/detected refill amount |
| `sensor.living_room_jojo_water_tank_last_refill_time` | Last refill timestamp |
| `sensor.living_room_jojo_water_tank_last_refill` | Friendly last-refill display |
| `sensor.living_room_jojo_water_tank_refill_history` | Persistent 60-day refill-event history |

## Home Assistant History Strategy

The reference Home Assistant installation uses the native Recorder database with a 60-day retention period. This is sufficient for current JoJo validation and short-term household trending, so the previous dedicated InfluxDB and Grafana containers have been retired for now. Long-term time-series storage can be reconsidered when additional energy monitoring such as the planned EM50 is introduced.

## Configuration and Maintenance

Open **Settings -> Devices & services -> JoJo Tank Monitor -> Configure**.

Current options include tank dimensions, sensor calibration, refill settings, Low Water Level and Estimation Reserve Level. **Clear Refill Data** deliberately clears stored refill data without changing calibration, dimensions, MQTT readings or Home Assistant statistics.

## Reference Automations

The reference installation uses the Low Water binary sensor for a low-water/recovery notification and a dedicated warning light. Zigbee/button alarm work is separate from the JoJo integration.

## Calibration

For a new installation, verify wiring and the sense resistor, record stable empty and full current values, enter those calibration values in the integration, and verify calculated percentage, depth and litres against known tank levels.

## Roadmap

GitHub is the source of truth for the project roadmap.

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
- [x] Add last refill amount/time and friendly state
- [x] Persist refill information across Home Assistant restarts
- [x] Add 60-day refill-event history with before/after/added values
- [x] Calculate completed refill from start-to-end volume instead of summing intermediate rises
- [x] Add refill-history sensor for dashboard use
- [x] Add refill verification dashboard and native Markdown history-table design
- [x] Configure Home Assistant Recorder for 60-day history on the reference installation
- [x] Retire InfluxDB/Grafana from the current reference homelab while 60-day HA history is sufficient
- [x] Add configurable Low Water Level and binary sensor with hysteresis
- [x] Add independent Estimation Reserve Level
- [x] Add low-water notification and warning-light automations
- [x] Remove obsolete legacy YAML/template entities from the reference installation
- [x] Add local Home Assistant integration branding/icon
- [x] Add MIT open-source license and project disclaimer

### Current validation

- [ ] Validate the new start/end/net refill calculation during the next real tank refill
- [ ] Confirm a completed refill creates one correct row in Refill History after the 15-minute timeout
- [ ] Verify refill history survives a Home Assistant restart after at least one real event is stored
- [ ] Continue real-world validation of Low Water threshold/hysteresis behaviour

### Before v1.0 stable

- [ ] Remove obsolete Arduino MQTT Discovery publications/warnings if any remain
- [ ] Add/complete wiring documentation and diagram
- [ ] Complete clean-install, calibration and troubleshooting documentation
- [ ] Perform a clean HACS installation test on a fresh Home Assistant setup
- [ ] Review repository access, branch/ruleset protection and contribution workflow
- [ ] Publish v1.0.0 stable release

### Future development

- [ ] Water Used Today
- [ ] Water Used Yesterday
- [ ] 7-day average daily water usage
- [ ] Estimated Days Remaining using the independent Estimation Reserve Level
- [ ] Daily/weekly/monthly water-consumption reporting
- [ ] Leak or abnormal-consumption detection
- [ ] Additional notifications/automation examples
- [ ] Multiple-tank support
- [ ] Reconsider InfluxDB/Grafana when longer-term or higher-volume telemetry such as EM50 energy monitoring is introduced

## Security and Repository Governance

Never commit Wi-Fi passwords, MQTT passwords, Home Assistant tokens, API keys or other credentials. The repository is public so anyone may read or fork the source code; public visibility does **not** by itself grant write access to the original repository.

Repository governance should protect the `main` branch from unintended modification. Before v1.0, review GitHub rulesets/branch protection and ensure only explicitly authorised maintainers can merge or push changes. External contributors should use forks/pull requests rather than direct write access.

## License

This project is licensed under the MIT License. See `LICENSE` for the full license text.

Copyright (c) 2026 dmseclab
