# ESPHome voice satellite (Waveshare ESP32-S3-Touch-AMOLED-2.16)

Home Assistant voice satellite on a Waveshare SKU 33969 board (ESP32-S3R8, 16 MB flash, 8 MB octal PSRAM).
Wake word "Okay Nabu" runs on-device; speech goes to the Home Assistant Assist pipeline (Whisper + Piper,
Swedish). User-facing overview: `README.md`.

## Files
- `waveshare-voice.yaml` – the whole firmware config.
- `secrets.yaml` – WiFi, `api_encryption_key` (also used for OTA encryption) and `device_host` (for tools/).
  Git-ignored; template in `secrets.example.yaml`. Never commit secrets or hardcode the key in scripts.
- `components/axp2101_lite/` – local AXP2101 reader (0x34): battery V/%, USB and system voltage, die temperature,
  charge state. Only enables ADC channels (reg 0x30), fuel gauge (0x18) and battery detection (0x68). Community
  AXP2101 components write M5Stack rail registers – do not use them.
- `sysinfo.h` – ESP-IDF headers (ota, image, flash, psram, nvs, chip info) for the statistics page lambdas.
- `sounds/` – Swedish clips and `make_sounds.py` (see "Voice clips").
- `tools/` – aioesphomeapi helpers; `device.py` reads host and key from `secrets.yaml`.
  `watch_logs.py [s]`, `read_states.py`, `press_test.py "<button>"`, `play_test.py <url> [vol]`,
  `test_battery_warning.py [levels]`.

## Build and flash
Run from PowerShell (not Git Bash: ESP-IDF rejects MSYS) with the Python 3.12 install that has ESPHome (not the
WindowsApps or venv pythons). Keep the project on a short path (Windows path limit breaks ESP-IDF).
```
python -m esphome compile waveshare-voice.yaml
python -m esphome upload waveshare-voice.yaml --device <device_host>   # OTA
python -m esphome upload waveshare-voice.yaml --device COM6            # USB fallback
```
`esphome logs` / `run` stream forever; use `tools/watch_logs.py <seconds>` or a detached process.
Logger must use `hardware_uart: USB_SERIAL_JTAG` to see logs on COM6.

## Hardware (verified)
- I2C: SDA GPIO15, SCL GPIO14. ES8311 0x18, AXP2101 0x34, ES7210 0x40, PCF85063 0x51, CST9220 0x5A, QMI8658 0x6B.
- I2S: MCLK GPIO42, BCLK GPIO9, WS GPIO45, mic in GPIO10, speaker out GPIO8, amp enable GPIO46.
- Display: CO5300 QSPI, `mipi_spi` model `WAVESHARE-ESP32-S3-TOUCH-AMOLED-2.16`, clk GPIO38, data GPIO4-7.
  Fonts need `glyphsets: [GF_Latin_Core]` for å/ä/ö.
- Touch: `cst9220`, INT GPIO11, RST GPIO40.
- IMU: `motion: platform: qmi8658` (2G / 256DPS / 31.25 Hz, polled 1 s). RTC: read at boot, written on every
  Home Assistant time sync (stores UTC).
- Flash: bootloader + table, otadata, phy_init, app0 7.75 MB, app1 7.75 MB, nvs 448 kB. Firmware ~2.1 MB.

## Audio lessons
- ONE shared `i2s_audio` hub for mic and speaker (ESP32 master). Two hubs with mic as clock master, or ES8311 as
  master, both failed.
- `resampler` speaker in front of the I2S speaker; codec runs at 16 kHz.
- Announcement pipeline `format: NONE` (HA sends MP3; FLAC-only builds cannot decode it).
- ES8311 volume 100 % is +32 dB and clips; 0 dB is ~75 %. `volume_max: 81%` = level tuned by ear.
- Stop `micro_wake_word` while the voice assistant runs or a clip plays; restart it afterwards.
- Idea not done: advertise 16 kHz mono FLAC in the announcement pipeline so HA transcodes server-side.

## UI (LVGL)
- Pages (swipe left/right, wrap, 4 dots): `page_face`, `page_status`, `page_stats`, `page_volume`.
- Face: robot icon (head outline, antenna, ears, pill eyes, mouth only when replying); color/eyes driven by global
  `face_mode` (0 idle, 1 listening, 2 thinking, 3 replying, 4 error, 5 no HA) in a 100 ms `interval` lambda,
  only while `screen_on`. Labels refresh every 1 s via `refresh_labels`.
- Screen off after 30 s: black `blackout` obj on top_layer, brightness 0, `lvgl.pause`. Wakes on touch or wake
  word; the face shifts a few px on each wake against burn-in.
- Avoid LVGL shadows and full-screen gradients: a 400 px circle with 40 px shadow took ~450 ms to redraw and broke
  speaker playback; gradients band in 16-bit color.
- `style_definitions` cannot hold `clickable`/`scrollable`; set them on the widget.
- ESPHome clears LV_OBJ_FLAG_SCROLLABLE on widgets with `on_swipe_*`, so the stats page scrolls a child obj
  `stats_scroll` (scroll_dir VER); horizontal gestures bubble to the page.
- Volume page: two stepped sliders (0..5): 0 = OFF, 1..5 = 80/85/90/95/100 % (0.75 + p*0.05). "Assistent"
  mutes/sets the media player; "Varningar" sets global `warn_volume` (restore_value, 0 disables warnings).
  Apply on_release only; `update_vol_ui` skips pressed sliders and is frozen by `warn_active` during warnings.
  A continuous slider with on_value -> volume_set -> on_volume -> slider.update looped, flickered and tripped the
  task watchdog. Button grids were tried and dropped as cluttered.

## Voice clips
- `sounds/*_sv.wav`: "Lågt batteri.", "N procent." (20/15/10/5), "Anslut laddaren.", volume test phrase.
- `make_sounds.py`: ENGINE "sapi" (Windows "Microsoft Bengt", current) or "piper" (sv_SE-lisa-medium, model in
  C:\esphome\piper-voices). Resampled to 16 kHz on the PC (on-device resampling sounded wobbly), silence trimmed,
  power-law compression 0.8, peak -5 dBFS (0 and -3 dBFS crackled).
- SAPI must run in PowerShell 7 (`pwsh`): Windows PowerShell 5.1 cannot see Bengt and silently falls back to the
  English voice Zira. The script checks the culture is sv-SE.
- Warning = three clips in sequence via `media_player.speaker.play_on_device_media_file` (announcement), waiting
  for `media_player.is_announcing` to end between parts. `batt_warn_level` warns once per threshold on the way
  down; resets at >= 25 % or when charging/USB connected. The script temporarily switches to `warn_volume`, then
  waits 700 ms before restoring volume/mute (restoring at speaker stop clicked).
- Test: HA button "Test Low Battery Warning", API action `test_battery_warning(level)`,
  `tools/test_battery_warning.py`.

## Environment
- Device on DHCP (Deco X60 mesh; the first WiFi attempt often fails auth, retries succeed). If the IP changes,
  find it with a ping sweep and `arp -a` for the device MAC, update `device_host` and the HA ESPHome entry.
  Static `manual_ip` hides the device from the Deco client list.
- Home Assistant runs in Docker; its internal URL must be a LAN address the device can reach or TTS fails.
- "Ursäkta jag förstår inte" from Assist is an HA-side issue: expose entities to Assist with names/areas.
- Wake words: only okay_nabu, hey_jarvis, alexa, hey_mycroft exist; "Hey Jarvis" did not trigger reliably with
  Swedish pronunciation and was reverted.

## Versioning (always)
- Semantic versioning, single source of truth: `substitutions: version` in `waveshare-voice.yaml`. It feeds
  `esphome: project: version` (shown in Home Assistant device info) and the statistics page.
- Every change that is committed gets a version bump: PATCH for fixes/tweaks, MINOR for new features, MAJOR for
  breaking changes (e.g. new secrets required, re-pairing with HA). 1.0.0 once it has run stably in daily use.
- For each version: update `CHANGELOG.md` (Keep a Changelog), flash the device, commit, annotated tag `vX.Y.Z`,
  push commit and tag, create a GitHub release from the changelog entry.

## Git
- Remote `origin`: https://github.com/unir0x/waveshare-voice-satellite (private), branch `master`.
- Before committing, scan staged files for secrets (`git grep --cached` for the WiFi password, API key, MAC).
  `secrets.yaml` and `.esphome/` (compiled-in secrets) must stay ignored.

## Ideas / not done
- Verify the click at the end of warnings is gone; else toggle the amp around the volume restore.
- Power: WiFi `power_save_mode: light`, amp off when idle.
- IMU wake-on-pick-up, RTC clock page, audio level visualization page.
