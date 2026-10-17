# JoJo Water Tank Monitor for Home Assistant

**JoJo Tank Monitor** is an open-source Home Assistant custom integration for monitoring JoJo Tanks and other water-storage tanks from MQTT telemetry produced by an Arduino-compatible controller and a 4–20 mA level/pressure sensor.

The integration converts raw telemetry into tank percentage, water depth, available litres, low-water state, refill detection/history and diagnostics. Tank calibration and behaviour are configured in Home Assistant; the Arduino remains the telemetry source.

## Stable release

**JoJo Tank Monitor integration: v1.0.0**  
**Validated reference Arduino firmware: 6.1.0**

Integration v1.0.0 completed clean-install acceptance testing on a fresh Home Assistant OS/HACS environment on 2026-10-17. Arduino firmware is versioned and validated separately; firmware changes do not share the integration release lifecycle.

## Features

- Home Assistant custom integration with Config Flow and local branding
- HACS-compatible repository structure
- MQTT-based local communication; no cloud service required
- Tank percentage, water depth and calculated litres
- Configurable capacity, height and empty/full current calibration
- Raw ADC, voltage, current, Wi-Fi, uptime and firmware diagnostics
- Configurable low-water threshold with hysteresis
- Independent estimation reserve level
- Filtered refill detection with persistent refill history
- Last-known-value handling and Arduino Online status during telemetry loss
- Persistent state/history across Home Assistant restarts
- Optional ambient-temperature correction, disabled by default
- Home Assistant Recorder support without requiring InfluxDB or Grafana
- MIT licensed

## Installation with HACS

Until the project is included in HACS defaults:

1. Open HACS in Home Assistant.
2. Add `https://github.com/dmseclab/ha-jojo-tank` as a custom repository of type **Integration**.
3. Download **JoJo Tank Monitor** and restart Home Assistant if requested.
4. Go to **Settings → Devices & services → Add Integration**.
5. Search for **JoJo Tank Monitor** and complete the configuration flow.

See [Installation and calibration](docs/INSTALLATION.md) for the complete setup procedure and [Troubleshooting](docs/TROUBLESHOOTING.md) for operational diagnostics.

## Reference installation

The validated reference installation uses:

| Setting | Reference value |
| --- | ---: |
| Tank | JoJo vertical 5,250 L |
| Usable full water depth | 1,900 mm |
| Controller | Arduino UNO R4 WiFi |
| Sensor/interface | 4–20 mA submersible sensor / DFRobot SEN0262 |
| Arduino analog input | A2 |
| Empty calibration | 4.00 mA |
| Full calibration | 11.50 mA |
| Sense resistor | 120 ohm |
| Publish interval | 5 minutes |
| Refill threshold | 75 L |
| Refill end timeout | 15 minutes |
| Arduino offline timeout | 15 minutes |
| Estimation reserve | 10% |
| Refill history retention | 60 days / max 100 events |

These values describe the reference installation; other tanks/sensors must be calibrated to their own hardware.

## Refill detection and history

The configured refill threshold is authoritative. Refill detection uses recent readings and sustained filtered confirmation to reject sensor noise while the normal tank level/depth/volume entities remain unsmoothed. Completed events store the start volume, end volume, net amount and time, and persist across Home Assistant restarts.

Telemetry expiry does not erase the last valid tank reading. Instead, `Arduino Online` becomes disconnected and the retained measurements are marked stale. A later valid live payload restores normal online state. Retained MQTT startup data does not falsely prove live connectivity or create refill events.

## Low water and temperature correction

Low Water is configurable and uses hysteresis. Alarm automations should consider `Arduino Online` when deciding whether a level is current.

Ambient-temperature correction is optional and **disabled by default**. Enable it only when simultaneous physical/electronic measurements demonstrate a repeatable temperature-related error. Raw ADC, voltage and current are never altered by temperature correction.

## Documentation

- [Documentation index](docs/README.md)
- [Installation and calibration](docs/INSTALLATION.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Clean-install validation](docs/CLEAN_INSTALL_VALIDATION.md)
- [v1.0.0 release gate](docs/V1_RELEASE_GATE.md)
- [Arduino firmware](firmware/README.md)
- [Changelog](CHANGELOG.md)

The Arduino firmware is deliberately treated as a related but separate component. Integration v1.0.0 retains firmware 6.1.0 as the validated production firmware; later firmware revisions must complete their own physical validation before promotion.

## Development checks

From the repository root:

```bash
python -m unittest discover -s tests -v
python -m compileall -q custom_components tests tools ha_tests
```

Home Assistant runtime tests use the pinned compatibility baseline in `requirements-test-ha.txt`. GitHub Actions runs the regression suite and firmware compilation checks. The optional `tools/mqtt_simulator.py` publishes only to a `jojo_test/` namespace and is used for isolated clean-install acceptance testing.

## Security and repository governance

Never commit Wi-Fi passwords, MQTT passwords, Home Assistant tokens, API keys or other credentials. The public repository is readable and forkable; changes to the original project are maintained through the protected default branch and controlled pull-request workflow.

## License

This project is licensed under the MIT License. See `LICENSE`.

Copyright (c) 2026 dmseclab
