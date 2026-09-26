"""Regenerate the on-device voice clips: synthesize, resample to 16 kHz, trim silence, normalize.

ENGINE "sapi" uses the Windows voice "Microsoft Bengt" (sv-SE); "piper" uses sv_SE-lisa-medium.
"""
import io
import os
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

ENGINE = "sapi"
SAPI_VOICE = "Microsoft Bengt"
SAPI_RATE = -1
PIPER_VOICE = Path(r"C:\esphome\piper-voices\sv_SE-lisa-medium.onnx")

OUT = Path(__file__).parent
TARGET_RATE = 16000  # the device codec runs at 16 kHz; on-device resampling sounded wobbly
PHRASES = {
    "low_battery": "Lågt batteri.",
    "pct_20": "20 procent.",
    "pct_15": "15 procent.",
    "pct_10": "10 procent.",
    "pct_5": "5 procent.",
    "connect_charger": "Anslut laddaren.",
    "test_volume": "Hej! Så här låter jag på den här volymen.",
}
THRESHOLD = 300
PAD_S = 0.05
PEAK_DBFS = -5.0  # full-scale clips crackled on the device; -3 dBFS still crackled
COMPRESSION = 0.8  # power-law compression: raises quiet speech without raising peaks


def read_wav(data: bytes) -> tuple[int, np.ndarray]:
    with wave.open(io.BytesIO(data)) as w:
        return w.getframerate(), np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float64)


def synth_sapi(text: str) -> tuple[int, np.ndarray]:
    fd, tmp = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    # Must be PowerShell 7 (pwsh): Windows PowerShell 5.1 only sees desktop SAPI voices (no Bengt) and
    # silently falls back to the English voice.
    ps = (
        "$ErrorActionPreference = 'Stop';"
        "Add-Type -AssemblyName System.Speech;"
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
        f"$s.SelectVoice('{SAPI_VOICE}'); $s.Rate = {SAPI_RATE};"
        f"if ($s.Voice.Culture.Name -ne 'sv-SE') {{ throw 'Swedish voice not selected' }};"
        "$f = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(16000,"
        " [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono);"
        f"$s.SetOutputToWaveFile('{tmp}', $f); $s.Speak($env:SAPI_TEXT); $s.Dispose()"
    )
    subprocess.run(["pwsh", "-NoProfile", "-Command", ps], check=True, env={**os.environ, "SAPI_TEXT": text})
    data = Path(tmp).read_bytes()
    os.remove(tmp)
    return read_wav(data)


def synth_piper(text: str) -> tuple[int, np.ndarray]:
    from piper import PiperVoice

    global _piper
    if "_piper" not in globals():
        _piper = PiperVoice.load(str(PIPER_VOICE))
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        _piper.synthesize_wav(text, wf)
    return read_wav(buf.getvalue())


def resample(x: np.ndarray, src: int, dst: int, half_taps: int = 48) -> np.ndarray:
    if src == dst:
        return x
    ratio = dst / src
    cutoff = min(1.0, ratio) * 0.95
    n_out = int(len(x) * ratio)
    t = np.arange(n_out) / ratio
    k0 = np.floor(t).astype(int)
    offsets = np.arange(-half_taps + 1, half_taps + 1)
    idx = k0[:, None] + offsets[None, :]
    h = cutoff * np.sinc(cutoff * (t[:, None] - idx)) * np.kaiser(2 * half_taps, 8.0)[None, :]
    xp = np.pad(x, (half_taps, half_taps + 1))
    return (xp[idx + half_taps] * h).sum(axis=1)


def trim(samples: np.ndarray, rate: int) -> np.ndarray:
    loud = np.nonzero(np.abs(samples) > THRESHOLD)[0]
    pad = int(rate * PAD_S)
    return samples[max(0, loud[0] - pad):min(len(samples), loud[-1] + pad)]


synth = synth_sapi if ENGINE == "sapi" else synth_piper
for name, text in PHRASES.items():
    rate, x = synth(text)
    y = trim(resample(x, rate, TARGET_RATE), TARGET_RATE)
    y /= np.abs(y).max()
    y = np.sign(y) * np.abs(y) ** COMPRESSION
    y *= 32767 * 10 ** (PEAK_DBFS / 20)
    y = np.clip(np.round(y), -32768, 32767).astype("<i2")
    path = OUT / f"{name}_sv.wav"
    with wave.open(str(path), "wb") as o:
        o.setnchannels(1)
        o.setsampwidth(2)
        o.setframerate(TARGET_RATE)
        o.writeframes(y.tobytes())
    print(f"{path.name}: {len(y) / TARGET_RATE:.2f}s, {TARGET_RATE} Hz, {len(y) * 2 / 1024:.0f} kB")
