# Changelog

## 1.0.0 — 2026-10-17

- Promote JoJo Tank Monitor to the first stable Home Assistant integration release after clean-install acceptance testing on a fresh Home Assistant OS/HACS environment.
- Complete real-world soak validation of the 1900 mm / 5250 L reference installation and close physical refill-detection validation using October 2026 Home Assistant history.
- Keep the validated 75 L refill threshold and five-minute reference telemetry interval.
- Validate first telemetry, tank calculations, low-water behaviour, refill detection/closeout, single-event history, telemetry expiry, last-known values, recovery, restart persistence and settings changes end-to-end.
- Add a documented clean-install end-to-end acceptance plan and isolated MQTT telemetry simulator.
- Add installation/calibration and troubleshooting guides.
- Add local Home Assistant integration branding.
- Reference DFRobot's official 4–20 mA liquid-level wiring example and document the reference UNO R4 WiFi A2 signal input.
- Keep temperature compensation optional and disabled by default.
- Keep Arduino firmware 6.1.0 as the validated production firmware for this integration release. Firmware changes, including removal of legacy MQTT Discovery, are deferred to a separate firmware validation/release cycle.

## 0.6.2-beta.1 — 2026-10-09

- Set the default usable full depth to 1900 mm; keep capacity at 5250 L. Existing entries require the Tank height option to be updated explicitly.
- Add opt-in, configurable ambient-weather correction with a 75 mm trial cap and 100 mm hard limit.
- Expose raw physical depth, compensation temperature, applied correction and status; preserve raw electrical diagnostics.
- Allow physical depth above configured full depth while retaining percentage/volume limits.
- Fall back to raw depth for stale/unavailable/invalid weather on live telemetry. Preserve offline snapshots through reload.
- Prevent correction-only changes from creating refill rises. No Arduino change is needed.
- Trial defaults are provisional; exported temperature history is from a separate sensor and does not validate weather-based ±5% accuracy.

## 0.6.1 — 2026-10-07

- Keep last known tank values during telemetry loss and restore their snapshot after HA reload/restart.
- Add Arduino Online connectivity status, stale attributes and a configurable offline timeout (default 15 minutes).
- Treat retained snapshots as unknown-age data; only live telemetry updates Last Reading and connectivity.
- Remove the hidden 4% refill floor. The configured threshold is authoritative; expose it as a diagnostic sensor.
- Clean up callbacks/timers after failed platform setup and on unload.
- Add six real Home Assistant tests against a pinned 2025.1.4 compatibility baseline, with an isolated mocked broker transport.
- Extend unit regressions and add firmware compilation to CI.
- Firmware 6.1.0 preserves fractional ADC averages and finer telemetry precision; retains the existing 10-bit scale and five-minute interval. Add optional MQTT discovery, enabled by default.

Automated checks do not establish physical refill accuracy or long-term hardware stability.

## 0.6.0 — 2026-10-07

- Promote 0.6.0-beta.1 median filtering and sustained refill confirmation to main.
- Preserve the beta's 4% noise floor and document missed small top-ups.
- Keep slow confirmed refills open while the median catches up, recording the filtered net amount.
- Share finite voltage/current, level, depth and volume calculations across all platforms. Reject invalid measurements without replacing the last valid telemetry.
- Support current-only payloads consistently in tank sensors, low-water alarms and refill detection.
- Disable polling on MQTT-driven entities. Last Reading changes only on valid telemetry receipt.
- Clear the complete refill history and candidate state using Clear Refill Data.
- Rebaseline on retained messages, duplicate uptime, device restarts and long telemetry gaps.
- Coalesce refill storage writes and flush on integration unload.
- Add deterministic regression tests, a sparse-history replay tool and GitHub Actions checks.

Clean-install and physical refill validation remain required before v1.0.
