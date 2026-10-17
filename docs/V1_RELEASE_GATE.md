# v1.0.0 release gate

JoJo Tank Monitor integration v1.0.0 acceptance was completed on 2026-10-17.

## Completed before release-candidate testing

- [x] 1900 mm reference full-depth calibration validated by real-world soak data.
- [x] 5250 L capacity and 100%/capacity clamping validated.
- [x] 75 L refill threshold retained after real-world refill-history review.
- [x] Physical refill-detection validation closed using October 2026 history and known likely top-up activity.
- [x] Last-known-value / Arduino Offline behaviour implemented and soak-tested.
- [x] Temperature compensation remains optional and disabled by default for the reference installation.
- [x] DFRobot official wiring example referenced; reference installation A2 input documented.
- [x] Clean-install acceptance procedure documented.
- [x] Isolated MQTT telemetry simulator added.
- [x] Troubleshooting guide added.

## Clean-install acceptance — PASS

Validated on a fresh Home Assistant OS 18.3 / Home Assistant Core 2026.10.2 test VM using HACS and `v1.0.0-rc.1`.

- [x] Clean HACS install succeeds in a fresh Home Assistant runtime.
- [x] Local integration branding/icon loads correctly.
- [x] Simulated first telemetry creates/updates expected entities and calculations.
- [x] Low-water scenario changes to Problem below the configured threshold and recovers correctly.
- [x] Simulated sustained refill is detected and closes after the configured timeout.
- [x] Exactly one completed refill-history event is stored for the simulated refill.
- [x] Telemetry expiry preserves last-known values and marks the Arduino offline.
- [x] Live telemetry recovery restores online state without creating a duplicate refill.
- [x] Home Assistant restart restores last-known values and completed refill history without duplication.
- [x] Tank Settings can be changed and restored without recreating the integration or losing refill history.
- [x] Release-candidate regression workflow passed.

## Integration / firmware release separation

Arduino firmware is maintained as a related but separate release stream. Firmware 6.1.0 remains the validated production firmware at the time of the JoJo Tank Monitor integration v1.0.0 release. The proposed firmware changes that remove legacy Home Assistant MQTT Discovery will be physically tested and promoted separately; they do not block the Home Assistant integration v1.0.0 release.

## Final repository/release actions

- [x] Promote integration manifest to `1.0.0`.
- [x] Record clean-install acceptance results.
- [x] Separate unvalidated Arduino firmware changes from the integration v1 release.
- [ ] Merge the accepted release-preparation branch to protected `main`.
- [ ] Tag and publish `v1.0.0` from the accepted `main` commit.
- [ ] Verify HACS sees the stable v1.0.0 release.
- [ ] Complete post-release branch/repository cleanup.

Future usage statistics, leak detection, additional reports and multiple-tank enhancements are post-v1 features and do not block this release.
