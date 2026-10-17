# Clean-install validation

This is the end-to-end acceptance test for the JoJo Tank Monitor v1 release candidate. It uses a **real Home Assistant runtime and the real custom integration**. Only the Arduino telemetry is simulated.

The purpose is to prove that a new user can install, configure and operate the integration without access to the reference tank hardware.

## Isolation

Use a test Home Assistant instance where possible. Use a dedicated MQTT state topic such as:

```text
jojo_test/sensor/tank/state
```

Do not point the simulated integration at the production tank topic.

## Prerequisites

- Home Assistant with the MQTT integration configured
- HACS installed for the HACS-path test
- Access to an MQTT broker from the test system
- `mosquitto_pub` available on the computer running the simulator
- JoJo Tank Monitor release candidate repository/branch available to HACS

## Fresh installation

1. Start with no JoJo Tank Monitor config entry in the test HA instance.
2. Install JoJo Tank Monitor through HACS as a custom integration/repository.
3. Restart Home Assistant if HACS requests it.
4. Go to **Settings -> Devices & services -> Add Integration** and select **JoJo Tank Monitor**.
5. Configure the test entry with MQTT topic `jojo_test/sensor/tank/state`.
6. Use the reference values unless deliberately testing another tank: 5250 L capacity, 1900 mm height, 4.00 mA empty, 11.50 mA full, 120 ohm sense resistor, 75 L refill threshold and 15-minute telemetry timeout.
7. Leave temperature compensation disabled for the baseline test.

## Simulator

Run:

```bash
python tools/mqtt_simulator.py --host MQTT_BROKER --topic jojo_test/sensor/tank/state normal
```

The simulator invokes `mosquitto_pub` and publishes retained JSON payloads matching the Arduino schema. Use `--username` and `--password` when required by the test broker. Run `python tools/mqtt_simulator.py --help` for options.

## Acceptance scenarios

### 1. First telemetry

Publish `normal`.

Pass when the device/entities appear and Arduino Online, Last Reading, Raw ADC, Sensor Voltage, Sensor Current, depth, percentage and available litres contain plausible values.

### 2. Falling level and Low Water

Publish the `low` scenario enough times for the integration to process the state.

Pass when the calculated tank level falls and Low Water follows the configured threshold/hysteresis behaviour.

### 3. Refill detection

Run:

```bash
python tools/mqtt_simulator.py --host MQTT_BROKER --topic jojo_test/sensor/tank/state refill
```

This sends a deterministic low-to-higher sequence with increasing uptime. Refill detection intentionally uses filtering and sustained confirmation. Use the test instance's configured refill timeout when waiting for close-out.

Pass when one completed refill is recorded, its amount is above the configured threshold and the refill history contains one corresponding event rather than several duplicate events.

### 4. Telemetry expiry / last-known values

Stop the simulator for longer than the configured telemetry timeout.

Pass when Arduino Online changes to offline while the last valid measurement remains visible and is marked stale. Last Reading must remain the timestamp of the last valid live payload rather than advancing during the outage.

### 5. Recovery

Publish `normal` again with an uptime value newer than the prior sample.

Pass when Arduino Online recovers automatically, stale status clears and Last Reading advances.

### 6. Home Assistant restart persistence

After at least one valid reading and completed refill event, restart Home Assistant without publishing a new live sample immediately.

Pass when the stored last-known measurement and completed refill history return after restart, connectivity does not falsely claim a new live reading, and a later simulated live payload restores normal online operation.

### 7. Options/configuration

Change one non-destructive Tank Settings value, save it and verify the entities update/recalculate as expected. Restore the reference value afterwards.

Pass when settings can be changed without recreating the integration.

## Release gate

The clean-install test is **COMPLETE/PASS** only when all seven scenarios above pass in a clean Home Assistant runtime using the release-candidate code. Record failures as defects; do not weaken an acceptance criterion to make the release pass.

The simulator is an end-to-end transport/behaviour test aid. It does not replace the project's unit tests, Home Assistant runtime tests, firmware compilation or the completed physical-tank soak validation.
