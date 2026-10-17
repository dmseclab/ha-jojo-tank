# v1.0.0 release gate

This file is the final release gate. Do not mark v1.0.0 released until every blocking item is complete.

## Completed before release-candidate testing

- [x] 1900 mm reference full-depth calibration validated by real-world soak data.
- [x] 5250 L capacity and 100%/capacity clamping validated.
- [x] 75 L refill threshold retained after real-world refill-history review.
- [x] Physical refill-detection validation closed using October 2026 history and known likely top-up activity.
- [x] Last-known-value / Arduino Offline behaviour implemented and soak-tested.
- [x] Temperature compensation remains optional and disabled by default for the reference installation.
- [x] DFRobot official wiring example referenced; reference installation A2 input documented.
- [x] Legacy Home Assistant MQTT Discovery publication removed from firmware 6.2.0 release candidate.
- [x] Clean-install acceptance procedure documented.
- [x] Isolated MQTT telemetry simulator added.
- [x] Troubleshooting guide added.
- [x] Historical development branches compared with main before cleanup; do not delete them until the v1 candidate is accepted.

## Blocking user-side acceptance tests

- [ ] Clean HACS install succeeds in a fresh/test Home Assistant runtime.
- [ ] Simulated first telemetry creates/updates expected entities.
- [ ] Low-water scenario behaves correctly.
- [ ] Simulated sustained refill produces one correct completed history event.
- [ ] Telemetry expiry preserves last-known values and marks them stale/offline.
- [ ] Live telemetry recovery clears stale/offline state.
- [ ] Home Assistant restart restores last-known values and completed refill history correctly.
- [ ] Tank Settings can be changed and restored without recreating the integration.
- [ ] Firmware 6.2.0 compiles for Arduino UNO R4 WiFi.
- [ ] Firmware 6.2.0 is uploaded to the reference Arduino and live telemetry is confirmed.
- [ ] Production Home Assistant continues receiving fresh data after the firmware change.

## Final repository/release actions after acceptance

- [ ] Confirm GitHub Actions/regression suite is green at the final candidate commit.
- [ ] Update integration manifest version from beta to `1.0.0`.
- [ ] Update README status/roadmap from release-candidate wording to v1 stable.
- [ ] Change the changelog heading from release candidate to the actual release date.
- [ ] Remove obsolete merged/superseded development branches after one final comparison.
- [ ] Merge the release-preparation branch to protected `main` through the normal controlled workflow.
- [ ] Tag and publish `v1.0.0` only from the accepted `main` commit.
- [ ] Install the exact released v1.0.0 package in the reference Home Assistant installation and perform a final sanity check.

Future usage statistics, leak detection, additional reports and multiple-tank enhancements are post-v1 features and do not block this release.
