# 0.6.0 validation and upgrade

## Field history reviewed on 7 October 2026

The supplied export contains 7,199 state rows, covering 4–7 October in South African time. It contains four days, rather than a full seven days. The initial Recorder snapshot includes a Last Reading from 3 October 21:55:59 UTC. The final reading is 7 October 16:00:56 UTC.

| Measurement | Result |
| --- | ---: |
| Reconstructed tank publishes | 1,082 |
| Median / maximum publish interval | 300 / 301 seconds |
| Recorded gaps over 450 seconds | 0 |
| Calculated volume range | 5,040–5,250 L |
| Current range | 11.2–12.3 mA |
| Publishes clamped at full calibration | 870 (80.4%) |
| Individual rises at least 75 L | 25 |
| Completed refills during callback replay | 0 |

Recorder exports omit unchanged states. The replay uses Last Reading to reconstruct each publish and holds the most recent voltage/current value until it changes. It uses the documented reference calibration and deterministic Home Assistant boundary doubles while running the actual integration callbacks and timer logic. It cannot recover MQTT retain flags, missing uptime or omitted packet metadata.

The exported refill fields stayed unchanged. Zero replay events are consistent with this history, but are not proof that no physical water was added. Most readings are clamped at the configured full current; physical top-ups above that point and changes smaller than the noise floor may be invisible. Temperature readings alone cannot establish sensor temperature compensation or distinguish real consumption from drift. Capacity and calibration remain unchanged.

## Verification

Run from the repository root with Python 3.12 or newer:

```bash
python -m unittest discover -s tests -v
python -m compileall -q custom_components tests tools
python tools/replay_history.py /path/to/history.csv
```

Use `--prefix sensor.your_tank_` if the raw tank entity prefix differs. The replay tool expects Last Reading plus Sensor Voltage or Sensor Current entities with that prefix, in the standard `entity_id,state,last_changed` CSV format. It uses reference calibration, so custom hardware/configuration needs matching harness settings before interpreting the result.

The regression suite covers noise recovery, sustained/slow refills, duplicate-event prevention, uptime restarts, retained messages, telemetry gaps, invalid values, timestamp stability, clearing during/after a refill, unload persistence and low-water hysteresis. Tests simulate the Home Assistant boundary; a full Home Assistant runtime and a fresh HACS installation have not been exercised here.

## Upgrade from 0.5.4 or 0.6.0-beta.1

1. Create a Home Assistant backup.
2. In HACS, open JoJo Tank Monitor, choose Redownload and select `main` if no 0.6.0 release is listed. For a manual installation, replace the entire `custom_components/jojo_tank` directory. The new `calculations.py` file is required; updating only `__init__.py` and `manifest.json` is insufficient.
3. Restart Home Assistant. Confirm the installed manifest shows `0.6.0`.
4. Wait for the next five-minute publish. Check volume, current, Last Reading and logs. Allow around 20 minutes for the refill filter to rebuild its baseline.
5. Confirm existing entity IDs, calibration and completed history are present. Clearing old noisy history is optional and irreversible; export it first if wanted.

No Arduino reflash is required. Firmware and default tank calibration are unchanged. Completed history survives the update; an in-progress refill does not.

## Remaining field checks

- Observe one known physical refill larger than the effective threshold. Confirm one event, start/end/net amount and close-out after readings settle.
- Restart Home Assistant and confirm that completed event remains.
- Verify low-water warning/clear behavior near its configured threshold.
- Perform a clean HACS installation on a separate Home Assistant instance before v1.0.
