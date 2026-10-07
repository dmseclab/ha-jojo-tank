"""Replay sparse Home Assistant CSV history through the actual MQTT callbacks.

Run: python tools/replay_history.py /path/to/history.csv
Uses test boundary doubles; does not connect to Home Assistant or MQTT.
Last Reading anchors every publish. Voltage/current state changes are held
until the next update, because Recorder omits unchanged sensor values.
"""

import argparse
import asyncio
import csv
import json
import statistics
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests.support import Clock, Harness, calculations


async def replay(path, prefix, threshold):
    with path.open(newline='', encoding='utf-8-sig') as stream:
        rows = list(csv.DictReader(stream))
    groups = defaultdict(list)
    for row in rows:
        if row['entity_id'].startswith(prefix):
            timestamp = datetime.fromisoformat(row['last_changed'].replace('Z', '+00:00'))
            # HA entity writes from one publish can differ by milliseconds.
            groups[timestamp.replace(microsecond=0)].append(row)
    h = await Harness(refill_threshold=threshold).setup()
    state = {}
    readings, volumes, currents = [], [], []
    previous = None
    gaps = []
    for timestamp, batch in sorted(groups.items()):
        for row in batch:
            state[row['entity_id']] = row['state']
        last_reading = next((row for row in batch if row['entity_id'] == prefix + 'last_reading'), None)
        if last_reading is None:
            continue
        try:
            when = datetime.fromisoformat(last_reading['state'].replace('Z', '+00:00'))
        except ValueError:
            continue
        if readings and when <= readings[-1]:
            continue
        voltage = state.get(prefix + 'sensor_voltage')
        current = state.get(prefix + 'sensor_current')
        payload = {'voltage_mv': voltage} if voltage is not None else {'current_raw_ma': current}
        volume = calculations.volume(payload, h.entry)
        if volume is None:
            continue
        if not readings:
            Clock.now = when
        Clock.advance_to(when)
        h.hass.receive(type('Message', (), {'payload':json.dumps(payload), 'topic':'replay', 'retain':False})())
        readings.append(when)
        volumes.append(volume)
        currents.append(calculations.current(payload, h.entry))
        if previous is not None:
            gaps.append((when-previous).total_seconds())
        previous = when
    if not readings:
        raise ValueError('No usable telemetry. Set --prefix to the Tank entity prefix.')
    active_at_export_end = h.runtime['refilling']
    h.settle()
    result = {
        'source_rows':len(rows),
        'configured_threshold_l':threshold,
        'reconstructed_publishes':len(readings),
        'start_utc':readings[0].isoformat(),
        'end_utc':readings[-1].isoformat(),
        'median_interval_seconds':statistics.median(gaps) if gaps else None,
        'max_interval_seconds':max(gaps) if gaps else None,
        'gaps_over_450_seconds':sum(g > 450 for g in gaps),
        'volume_min_l':round(min(volumes),2),
        'volume_max_l':round(max(volumes),2),
        'current_min_ma':round(min(currents),3),
        'current_max_ma':round(max(currents),3),
        'saturated_publishes':sum(v == h.entry.data['tank_capacity'] for v in volumes),
        'refill_active_at_export_end':active_at_export_end,
        'completed_refill_count':len(h.runtime['refill_history']),
        'single_step_rises_at_least_75_l':sum(b-a >= 75 for a,b in zip(volumes,volumes[1:])),
        'completed_refills':h.runtime['refill_history'],
    }
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv', type=Path)
    parser.add_argument('--prefix', default='sensor.jojo_water_tank_')
    parser.add_argument('--threshold', type=float, default=75.0)
    args = parser.parse_args()
    asyncio.run(replay(args.csv, args.prefix, args.threshold))
