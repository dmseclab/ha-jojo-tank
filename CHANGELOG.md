# Changelog

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

See [validation and upgrade](docs/validation-0.6.0.md). This version does not complete the v1.0 clean-install or physical refill validation.
