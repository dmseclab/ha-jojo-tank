# 0.6.1 evaluation and Saturday reflash

## Behavior agreed on 7 October 2026

Retain last known values, while exposing Arduino Online and stale attributes. Only valid live MQTT messages establish connectivity and Last Reading. The offline timeout defaults to 15 minutes. Retained payloads may seed an empty display but never prove that the Arduino is currently communicating.

The configured refill threshold is now the effective threshold. The median filter and three confirmations remain. The previous hidden 4% floor is removed. Existing configured values remain in place; choose 210 L explicitly in settings if wanted.

## Extended history evaluation

The October export contains 14,160 state rows. The additional September export contains 27,462 rows. Sparse state changes were reconstructed into publishes using Last Reading and voltage/current state. Writes within the same second were grouped because HA entities from one publish can differ by milliseconds. This is an approximation: uptime, retain flags, source packet IDs and physical refill annotations are absent.

| Result | 13–27 September | 1–7 October |
| --- | ---: | ---: |
| Usable reconstructed readings | 4,341 | 1,953 |
| Median / maximum interval | 300 / 387 seconds | 300 / 301 seconds |
| Gaps over 450 seconds | 0 | 0 |
| Calculated volume range | 4,870.83–5,250 L | 5,040–5,250 L |
| Publishes clamped at full | 3,037 (70.0%) | 1,675 (85.8%) |
| New detector events at explicit 75 L | 35 | 2 |
| New detector events at explicit 210 L | 0 | 0 |

The October 75 L replay produces 181 L and 82 L events. The recorded old refill fields include a 152 L event on 2 October at 18:00 SAST, which the new replay does not reproduce. These are software-detected candidates, not independently verified physical refills. No history export includes manually measured fill volumes or the events attribute. The greater sensitivity at 75 L therefore remains a tradeoff; do not use detected litres as verified consumption.

The September and October exports cover separate intervals; there is no source data here for 28–30 September. Repeated/clamped values and the unknown states around HA restarts do not prove absence of packet loss. Much of the current data is clamped at full, limiting calibration conclusions. Tank capacity, full/empty calibration and tank-height scaling remain unchanged.

## Automated verification

Fast unit regressions run with `python -m unittest discover -s tests -v`. They include configured-threshold behavior, retained/live separation, last-known snapshot restoration, expiry/recovery and timeout selection.

Real Home Assistant tests run separately:

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements-test-ha.txt
.venv/bin/python -m pytest ha_tests -q
```

The pinned runtime is Home Assistant 2025.1.4, with six tests covering platform setup, MQTT dispatch, expiry/recovery, retained messages, reload persistence, settings, completed refill history and unload cleanup. MQTT transport is mocked by HA's test fixtures; the integration, entities, state machine, event loop and storage helper are real. No production broker or HA IP is contacted. This is a compatibility baseline rather than proof for every newer HA release.

Firmware CI compiles with Renesas UNO core 1.6.0, ArduinoMqttClient 0.1.8 and ArduinoJson 6.21.5. Compilation is separate from physical board validation.

Reproduce history comparisons with:

```bash
python tools/replay_history.py /path/to/history.csv --threshold 75
python tools/replay_history.py /path/to/history.csv --threshold 210
```

## Saturday 10 October 2026

1. Back up HA and keep a copy of the currently flashed sketch with its local connection settings.
2. Update the complete HA integration folder to 0.6.1 and restart HA. Confirm existing entity IDs and calibration, plus Arduino Online and Refill Threshold. The integration works with existing firmware 6.0.0 too.
3. Download the repository sketch, retain your actual Wi-Fi/MQTT credentials and broker address, and leave discovery enabled for the first reflash. No IP changes are needed.
4. Verify the sketch using the UNO R4 WiFi board profile, then upload firmware 6.1.0. Keep the ADC resolution at 10 bits for this first comparison.
5. Check Serial Monitor at 9600 baud for firmware version and raw readings. Confirm HA receives fractional ADC values, finer voltage telemetry and a new Last Reading. A packet can still have integer ADC if all 20 samples are equal.
6. Record physical water depth before and after the reflash without a refill between measurements. The old integer averaging rounded down, so a small upward shift is possible; verify it before changing calibration.
7. During normal use, annotate the next known refill with start/end times and manual depth readings. Keep pre/post-flash histories separate for comparison.

Optional connectivity check: briefly power off only the Arduino, wait beyond the configured timeout, and confirm that Arduino Online turns off while tank values and Last Reading remain unchanged. Restore power and confirm live telemetry restores Online. This need not involve changing MQTT addressing.
