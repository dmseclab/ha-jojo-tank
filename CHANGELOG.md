# Changelog

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
