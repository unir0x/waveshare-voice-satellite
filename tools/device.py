"""Shared connection helper: reads device_host and api_encryption_key from ../secrets.yaml."""
import re
from pathlib import Path

import aioesphomeapi

SECRETS = Path(__file__).resolve().parent.parent / "secrets.yaml"


def _secret(name: str) -> str:
    m = re.search(rf'^{name}:\s*"?([^"\n]+)"?\s*$', SECRETS.read_text(encoding="utf-8"), re.MULTILINE)
    if not m:
        raise SystemExit(f"'{name}' missing in {SECRETS}")
    return m.group(1)


async def connect() -> aioesphomeapi.APIClient:
    cli = aioesphomeapi.APIClient(_secret("device_host"), 6053, None, noise_psk=_secret("api_encryption_key"))
    await cli.connect(login=True)
    return cli


def log_text(msg) -> str:
    return msg.message.decode(errors="replace") if isinstance(msg.message, bytes) else str(msg.message)
