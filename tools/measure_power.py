"""Compare battery drain with and without the WiFi power save mode.

Settles for SETTLE_MIN minutes, then alternates BLOCK_MIN-minute blocks: normal, power save, normal, power save.
Logs battery voltage/level every minute as CSV and prints the drain per block at the end.
Aborts if USB power is connected. Usage: python tools/measure_power.py <out.csv> [settle_min] [block_min] [blocks]
"""
import asyncio
import csv
import sys
import time

from device import connect

OUT = sys.argv[1]
SETTLE_MIN = int(sys.argv[2]) if len(sys.argv) > 2 else 15
BLOCK_MIN = int(sys.argv[3]) if len(sys.argv) > 3 else 30
BLOCKS = int(sys.argv[4]) if len(sys.argv) > 4 else 4


async def read_states(cli, names):
    states = {}

    def on_state(st):
        if st.key in names and hasattr(st, "state"):
            states[names[st.key]] = st.state

    cli.subscribe_states(on_state)
    await asyncio.sleep(3)
    return states


async def sample():
    cli = await connect()
    try:
        entities, services = await cli.list_entities_services()
        names = {e.key: e.name for e in entities}
        return cli, services, await read_states(cli, names)
    except Exception:
        await cli.disconnect()
        raise


async def main():
    plan = [("settle", SETTLE_MIN)] + [("normal" if i % 2 == 0 else "power_save", BLOCK_MIN) for i in range(BLOCKS)]
    rows = []
    t0 = time.time()
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["elapsed_min", "phase", "voltage", "level", "usb"])
        for phase, minutes in plan:
            forced = False
            end = time.time() + minutes * 60
            while time.time() < end:
                try:
                    cli, services, st = await sample()
                    if phase == "power_save" and not forced:
                        svc = next(s for s in services if s.name == "force_power_save")
                        await cli.execute_service(svc, {"minutes": minutes})
                        forced = True
                    await cli.disconnect()
                except Exception as exc:  # device busy or WiFi hiccup: try again next minute
                    print(f"sample failed: {exc}", flush=True)
                    await asyncio.sleep(60)
                    continue
                row = [round((time.time() - t0) / 60, 1), phase, st.get("Battery Voltage"), st.get("Battery Level"),
                       st.get("USB Connected")]
                w.writerow(row)
                f.flush()
                rows.append(row)
                print(row, flush=True)
                if st.get("USB Connected"):
                    print("USB connected, aborting", flush=True)
                    return
                await asyncio.sleep(57)

    print("\nDrain per block (voltage start -> end, mV per hour):")
    blocks, cur = [], None
    for r in rows:
        if cur is None or cur[0] != r[1]:
            cur = [r[1], []]
            blocks.append(cur)
        cur[1].append(r)
    for phase, rs in blocks:
        if phase == "settle" or len(rs) < 2 or rs[0][2] is None:
            continue
        hours = (rs[-1][0] - rs[0][0]) / 60
        mv_per_h = (rs[0][2] - rs[-1][2]) * 1000 / hours if hours else 0
        print(f"{phase:11s} {rs[0][2]:.3f} -> {rs[-1][2]:.3f} V over {hours * 60:.0f} min: {mv_per_h:.0f} mV/h, "
              f"level {rs[0][3]} -> {rs[-1][3]} %")


asyncio.run(main())
