"""Stream device logs over the API. Usage: python tools/watch_logs.py [seconds]"""
import asyncio
import sys

import aioesphomeapi

from device import connect, log_text

SECONDS = int(sys.argv[1]) if len(sys.argv) > 1 else 45


async def main():
    cli = await connect()

    def on_log(msg):
        text = log_text(msg)
        if "axp2101_lite" not in text and "font:" not in text:
            print(text, flush=True)

    cli.subscribe_logs(on_log, log_level=aioesphomeapi.LogLevel.LOG_LEVEL_VERBOSE)
    await asyncio.sleep(SECONDS)
    await cli.disconnect()


asyncio.run(main())
