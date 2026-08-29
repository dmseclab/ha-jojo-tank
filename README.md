# JoJo Tank Monitor for Home Assistant

A reproducible DIY water-tank monitoring project using an Arduino-compatible controller, a submersible pressure level sensor, MQTT and Home Assistant.

> **Project status:** v0.5.4 active development / pre-v1.0 validation. Repository governance is enabled for the default branch with deletion and force-push protection; the authorised maintenance workflow has been verified after protection was enabled.

## Current project status

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

A refill begins when the calculated volume rises by at least the configured refill threshold between readings. Further qualifying rises during the configured timeout are treated as part of the same physical refill. When the timeout expires, the integration closes the event and records:

```text
Refill amount = final refill volume - volume before refill
```

Completed events persist across Home Assistant restarts and contain `time`, `start_l`, `end_l` and `amount_l`. History is automatically limited to the latest 60 days and a maximum of 100 events.

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
