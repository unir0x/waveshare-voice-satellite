# Waveshare ESP32-S3 AMOLED voice satellite for Home Assistant

ESPHome firmware that turns a **Waveshare ESP32-S3-Touch-AMOLED-2.16** (SKU 33969) into a Home Assistant
voice satellite with an animated touch UI, battery monitoring and spoken low-battery warnings (Swedish).

## Features

- **Voice assistant**: on-device wake word "Okay Nabu" (microWakeWord), speech streamed to the Home Assistant
  Assist pipeline (tested with Whisper + Piper, Swedish). Replies play on the built-in speaker.
- **Touch UI (LVGL)**, swipe left/right between four pages:
  1. **Face**: robot icon whose color and eyes follow the assistant state (ready, listening, thinking,
     replying, error, no Home Assistant).
  2. **Status**: state, IP address, battery.
  3. **Statistics** (scrollable): last recognized speech, system info (chip, RAM/PSRAM, flash/firmware, NVS,
     WiFi, uptime, reset reason) and sensors (battery, USB/system voltage, temperatures, tilt,
     accelerometer, gyro, RTC time).
  4. **Volume**: stepped sliders (OFF, 80-100 %) for the assistant and for warnings, with test buttons.
- **Screen off after 30 s** (burn-in protection and power saving). Wakes on touch or wake word.
- **Low battery warnings** at 20/15/10/5 % ("Lågt batteri. N procent. Anslut laddaren."), stored in the
  firmware so they work without Home Assistant. Separate warning volume, audible even when the assistant is
  muted.
- **Sensors in Home Assistant**: battery level/voltage, charging state, USB and system voltage, PMIC/chip/IMU
  temperature, tilt, WiFi signal, uptime, free memory, reset reason.
- **RTC** kept in sync from Home Assistant.

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
| `sysinfo.h` | ESP-IDF headers used by the statistics page |
| `sounds/*_sv.wav` | Swedish voice clips embedded in the firmware |
| `sounds/make_sounds.py` | Regenerates the clips (Windows voice "Microsoft Bengt" or Piper `sv_SE-lisa-medium`) |
| `tools/` | API helper scripts: live logs, entity states, button press, media playback, warning test |

## Status

Current version: see `CHANGELOG.md` (semantic versioning; the firmware version is shown in Home Assistant and on
the statistics page).

Working: wake word, Assist round trip with clear audio, UI pages, sensors, battery warnings, volume page.

Known issues and ideas:
- A small click may remain at the end of a warning (volume restore); needs listening test.
- "Hey Jarvis" was tried as wake word but did not trigger reliably with Swedish pronunciation. A custom
  "Okay Lisa" would need training a microWakeWord model.
- Power draw is roughly 150-250 mA (always-on WiFi and wake word); battery lasts hours, not days. Possible
  savings: WiFi power save "light", amplifier off when idle.
- Unused so far: IMU for "wake on pick-up", clock page from the RTC, audio level visualization.

See `CLAUDE.md` for the detailed engineering notes and lessons learned.
