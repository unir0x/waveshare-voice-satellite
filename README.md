# Waveshare ESP32-S3 AMOLED voice satellite for Home Assistant

ESPHome firmware that turns a **Waveshare ESP32-S3-Touch-AMOLED-2.16** (SKU 33969) into a Home Assistant
voice satellite with an animated touch UI, battery monitoring and spoken low-battery warnings (Swedish).

## Features

- **Voice assistant**: on-device wake word "Okay Nabu" (microWakeWord), speech streamed to the Home Assistant
  Assist pipeline. Tested with local Whisper + Piper and with cloud Google Gemini, in Swedish. Replies play on the
  built-in speaker; long replies (cloud LLMs) are supported.
- **Speaker for Home Assistant**: exposed as a media player, so `tts.speak`, announcements and media from Home
  Assistant play too (the wake word pauses automatically while anything plays).
- **Click-free audio**: the amplifier is only on while sound plays, which removes the pops at start and end.
- **Server-side audio conversion**: the device asks Home Assistant for 16 kHz mono FLAC, so cloud voices are
  converted on the server. If Home Assistant fails to deliver a reply, playback is stopped after 20 s instead of
  hanging, and the face shows a red "no audio from Home Assistant" state.
- **Touch UI (LVGL)**, swipe left/right between four pages:
  1. **Face**: robot icon whose color and eyes follow the assistant state (ready, listening, thinking,
     replying, error, no Home Assistant). It is synced to the speaker: it thinks until the reply is actually
     audible and talks only while sound plays (also for warnings); the mouth opens with the actual audio level.
  2. **Status**: state, IP address, battery.
  3. **Statistics** (scrollable): last recognized speech, system info (chip, RAM/PSRAM, flash/firmware, NVS,
     WiFi, uptime, reset reason) and sensors (battery, USB/system voltage, temperatures, tilt,
     accelerometer, gyro, RTC time).
  4. **Settings**: stepped volume sliders (OFF, 80-100 %) for the assistant and for warnings, the battery
     charge control switch, and test buttons.
- **Screen off after 30 s** (burn-in protection and power saving). Wakes on touch, wake word or when the
  device is picked up (IMU).
- **Low battery warnings** at 20/15/10/5 % ("Lågt batteri. N procent. Anslut laddaren."), stored in the
  firmware so they work without Home Assistant. Separate warning volume, audible even when the assistant is
  muted.
- **Sensors in Home Assistant**: battery level/voltage, charging state, USB and system voltage, PMIC/chip/IMU
  temperature, tilt, WiFi signal, uptime, free memory, reset reason. The firmware version is shown in the device
  info.
- **RTC** kept in sync from Home Assistant.
- **Battery charge control**: with USB always connected, charging pauses at ~85-90 % (4.1 V limit) and resumes only
  at 30 %, which keeps the battery healthy. Switchable on the device and via "Charge Limit" in Home Assistant.
- **Power save schedule** on battery (01-06 daily, Mon-Fri 09-15): WiFi modem sleep while idle, wake word still
  active. Night quiet hours 01-06 postpone battery warnings.

## Hardware

| Part | Chip | Notes |
|---|---|---|
| SoC | ESP32-S3R8 | 16 MB flash, 8 MB octal PSRAM, native USB-Serial/JTAG |
| Display | CO5300 AMOLED 480x480 | QSPI, ESPHome `mipi_spi` model `WAVESHARE-ESP32-S3-TOUCH-AMOLED-2.16` |
| Touch | CST9220 | I2C 0x5A, INT GPIO11, RST GPIO40 |
| Microphones | ES7210 | I2C 0x40 |
| Speaker codec | ES8311 | I2C 0x18, amp enable GPIO46 |
| Power | AXP2101 | I2C 0x34, read-only local component |
| IMU | QMI8658 | I2C 0x6B |
| RTC | PCF85063 | I2C 0x51 |

I2C: SDA GPIO15, SCL GPIO14. I2S: MCLK GPIO42, BCLK GPIO9, WS GPIO45, mic in GPIO10, speaker out GPIO8.

## Requirements

- The board: Waveshare ESP32-S3-Touch-AMOLED-2.16 (SKU 33969), a USB-C cable and optionally a LiPo battery.
- [ESPHome](https://esphome.io) installed on your computer (`pip install esphome`, tested with 2026.9.0). The
  repository contains everything project specific; ESPHome itself is not included.
- Internet access for the first build: ESPHome downloads the ESP-IDF toolchain, the "Okay Nabu" wake word model and
  the Roboto font automatically.
- Home Assistant with the ESPHome integration and an Assist pipeline (speech-to-text + text-to-speech), reachable
  from the device via its internal URL.
- Your own `secrets.yaml` (copy `secrets.example.yaml`). Nothing secret is stored in the repository.
- Optional, only to regenerate the voice clips: Windows with the Swedish voice "Microsoft Bengt" and PowerShell 7,
  or Piper with `sv_SE-lisa-medium` (see `sounds/make_sounds.py`).

The on-screen texts and voice clips are Swedish, and the power save schedule (`schedule.h`) reflects the author's
routine; adjust them to your needs.

## Setup

1. Install ESPHome (`pip install esphome`, tested with 2026.9.0).
2. Copy `secrets.example.yaml` to `secrets.yaml` and fill in WiFi, a new API key and the device address.
3. Build and flash (Windows: run from PowerShell, not Git Bash, and keep the project on a short path such as
   `C:\esphome\...`):
   ```
   python -m esphome run waveshare-voice.yaml --device COM6            # first time, over USB
   python -m esphome upload waveshare-voice.yaml --device <device-ip>  # later, over WiFi
   ```
4. In Home Assistant add the ESPHome integration with the device IP and API key, then pick an Assist pipeline
   with speech-to-text and text-to-speech for the device.
5. Home Assistant must have an internal URL the device can reach (Settings -> System -> Network), otherwise
   replies cannot be downloaded ("the voice assistant cannot reach Home Assistant").
6. Reserve the device IP in the router so Home Assistant does not lose it.

## Project layout

| Path | Purpose |
|---|---|
| `waveshare-voice.yaml` | The whole firmware configuration |
| `secrets.example.yaml` | Template for the git-ignored `secrets.yaml` |
| `components/axp2101_lite/` | Minimal AXP2101 reader (battery, voltages, temperature, charge state). Enables ADC channels only, never touches power rails |
| `components/level_tap/` | Pass-through speaker that measures the audio level for the mouth animation |
| `schedule.h` | Power save windows and night quiet hours |
| `sysinfo.h` | ESP-IDF headers used by the statistics page and power save |
| `sounds/*_sv.wav` | Swedish voice clips embedded in the firmware |
| `sounds/make_sounds.py` | Regenerates the clips (Windows voice "Microsoft Bengt" or Piper `sv_SE-lisa-medium`) |
| `tools/` | API helper scripts: live logs, entity states, button press, media playback, warning test |

## Status

Current version: **v0.12.0** (see `CHANGELOG.md`; semantic versioning, every change is logged there and each
release is tagged and published on GitHub). The running firmware version is shown in Home Assistant and on the
statistics page.

Working: wake word, Assist round trip with clear audio (local and cloud pipelines), playback from Home Assistant,
UI pages with speaker-synced face, sensors, battery warnings, volume page, click-free speaker.

1.0.0 is planned once it has run stably in daily use for a while.

Known limitations and ideas:
- On battery the device lasts hours, not days (always-on WiFi and wake word). Measured: about 15.5 %/h normally
  (~6.5 h from full) and 10.3 %/h in power save (~9.5 h). The power save schedule (WiFi modem sleep at night and
  on weekday daytime) applies automatically on battery while keeping the wake word.
  A stronger option, deep sleep in the same windows (no wake word while asleep, wake by touch), is documented in
  `CLAUDE.md` but not enabled.
- Reply latency with a cloud pipeline (Gemini) is 4-11 s after you stop speaking, almost all of it in the cloud:
  speech-to-text ~1.5 s, answer ~1-2 s, and the Gemini voice 2.5-8 s depending on reply length (it renders the
  whole reply before sending). A local TTS such as Piper takes well under a second. The Gemini voice also returned
  HTTP 500 for time-only replies like "15:50".
- The wake word is "Okay Nabu". Other words need a different microWakeWord model; custom words (e.g. "Okay Lisa")
  would have to be trained first.
- Ideas: a clock page from the RTC, an audio level visualization page (the level is already measured).

See `CLAUDE.md` for the detailed engineering notes and lessons learned.

## License

MIT, see `LICENSE`. The voice clips in `sounds/` were generated with the Windows voice "Microsoft Bengt"; regenerate
them with `sounds/make_sounds.py` (Piper) if you need freely licensed audio. Fonts and the wake word model are
downloaded at build time under their own licenses.
