"""Play a media URL as an announcement. Usage: python tools/play_test.py <url> [volume 0..1]"""
import asyncio
import sys

import aioesphomeapi

from device import connect, log_text

URL = sys.argv[1]
VOL = float(sys.argv[2]) if len(sys.argv) > 2 else None


async def main():
    cli = await connect()
    entities, _ = await cli.list_entities_services()
    mp = next(e for e in entities if e.__class__.__name__ == "MediaPlayerInfo")

    def on_log(msg):
        text = log_text(msg)
        if "axp2101_lite" not in text and "font:" not in text:
            print(text, flush=True)

    cli.subscribe_logs(on_log, log_level=aioesphomeapi.LogLevel.LOG_LEVEL_DEBUG)
    await asyncio.sleep(1)
    if VOL is not None:
        cli.media_player_command(mp.key, volume=VOL)
        await asyncio.sleep(1)
    cli.media_player_command(mp.key, media_url=URL, announcement=True)
    await asyncio.sleep(10)
    await cli.disconnect()


asyncio.run(main())
