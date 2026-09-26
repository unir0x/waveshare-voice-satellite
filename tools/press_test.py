"""Press a template button by name and print logs. Usage: python tools/press_test.py ["Test Speaker"]"""
import asyncio
import sys

import aioesphomeapi

from device import connect, log_text

NAME = sys.argv[1] if len(sys.argv) > 1 else "Test Speaker"


async def main():
    cli = await connect()
    entities, _ = await cli.list_entities_services()
    btn = next(e for e in entities if getattr(e, "name", "") == NAME)
    cli.subscribe_logs(lambda m: print(log_text(m), flush=True), log_level=aioesphomeapi.LogLevel.LOG_LEVEL_DEBUG)
    await asyncio.sleep(1)
    cli.button_command(btn.key)
    await asyncio.sleep(8)
    await cli.disconnect()


asyncio.run(main())
