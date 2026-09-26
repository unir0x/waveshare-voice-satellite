"""Play the low battery warning for given levels. Usage: python tools/test_battery_warning.py [20 15 10 5]"""
import asyncio
import sys

from device import connect


async def main():
    levels = [int(x) for x in sys.argv[1:]] or [20, 15, 10, 5]
    cli = await connect()
    _, services = await cli.list_entities_services()
    svc = next(s for s in services if s.name == "test_battery_warning")
    for level in levels:
        print(f"Playing {level} %", flush=True)
        await cli.execute_service(svc, {"level": level})
        await asyncio.sleep(10)
    await cli.disconnect()


asyncio.run(main())
