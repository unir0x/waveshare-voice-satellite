# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/). The version lives in `waveshare-voice.yaml` (`substitutions: version`).

## [Unreleased]

## [0.10.0] - 2026-09-27

### Added
- Power save schedule (switch "Power Save Schedule", on by default): every night 01:00-06:00 and Monday-Friday
  09:00-15:00, on battery only, WiFi runs in modem-sleep while the device keeps listening for "Okay Nabu". Full
  power returns instantly on the wake word or playback. API action `force_power_save(minutes)` for testing.
- Night quiet hours 01:00-06:00: battery warnings are postponed until 06:00.
- Statistics page shows the power save state.
- When the 20 s guard stops a reply that never produced audio, the face turns red with "Inget ljud från Home
  Assistant" for 4 s instead of silently returning to ready.

## [0.9.4] - 2026-09-27

### Changed
- The speaker asks Home Assistant for 16 kHz mono FLAC, so TTS and media (including 24 kHz cloud voices such
  as Gemini) are converted on the server instead of resampled on the device.
- `tools/watch_logs.py` prints elapsed time for each line, to measure pipeline latency.
- Developer notes (CLAUDE.md) document the shared I2S bus rule and the amplifier gating.
- README updated for v0.9.3: speaker-synced face, playback from Home Assistant, click-free audio, cloud
  pipelines, current status and limitations.
- The release routine now includes updating the README.
- README no longer mentions the abandoned "Hey Jarvis" test; it states the wake word is "Okay Nabu".

### Fixed
- A reply whose audio Home Assistant cannot deliver (e.g. HTTP 500 from the TTS proxy) no longer leaves the
  speaker stuck retrying: playback is stopped if no sound has played within 20 s.

## [0.9.3] - 2026-09-27

### Changed
- Every change is now logged here as soon as it is made; the section becomes a version entry on release.

### Fixed
- Clicks before and after speech: the speaker amplifier (GPIO46) is now only on while audio plays. It switches on
  30 ms after the I2S speaker has started and off 150 ms after the last sample, before the speaker stops (500 ms),
  so it is off during both codec pops. The built-in clips got 200 ms leading silence so no word is cut.
- Volume test phrase is now "Så här låter jag på den här volymen." (dropped the "Hej!" that got clipped).

## [0.9.2] - 2026-09-27

### Changed
- The face follows the speaker instead of pipeline events: it thinks until reply audio actually plays and talks
  only while the speaker outputs sound (also for warnings and the test phrase); after the reply has started it
  never falls back to thinking, which removes a yellow flicker at the end. The status text follows too.
- Long replies (e.g. cloud LLM assistants) may play for up to 2 minutes before the display returns to "ready"
  (was 30 s).

## [0.9.1] - 2026-09-27

### Fixed
- Audio started from outside the voice assistant (e.g. `tts.speak` or media played from Home Assistant) never
  played and left the player stuck in "playing": the wake word microphone kept the shared I2S bus. The wake word
  now pauses whenever the media player plays or announces and resumes when it is idle.
- The "Test Speaker" button looped forever for the same reason; it now plays the test phrase.

## [0.9.0] - 2026-09-26

First versioned release. Core features work; not yet proven in long-term daily use.

### Added
- Home Assistant voice satellite: on-device wake word "Okay Nabu", Assist pipeline over the ESPHome API,
  replies on the built-in speaker (ES7210 microphones, ES8311 codec on one shared I2S bus).
- LVGL touch UI with four swipeable pages: animated robot face, status, scrollable statistics
  (last heard, system, sensors) and volume.
- Screen off after 30 s, wake on touch or wake word, burn-in protection.
- Battery monitoring through a read-only AXP2101 component: level, voltages, temperature, charge state.
- QMI8658 IMU (tilt, acceleration, gyro) and PCF85063 RTC synced from Home Assistant.
- Swedish low battery warnings at 20/15/10/5 % embedded in the firmware, with a separate warning volume.
- Stepped volume sliders (OFF, 80-100 %) for assistant and warnings, with test buttons.
- Helper scripts in `tools/` reading the device address and API key from `secrets.yaml`.

### Known issues
- A small click may remain at the end of a warning.
- Power draw about 150-250 mA; battery lasts hours.

[Unreleased]: https://github.com/unir0x/waveshare-voice-satellite/compare/v0.10.0...HEAD
[0.10.0]: https://github.com/unir0x/waveshare-voice-satellite/releases/tag/v0.10.0
[0.9.4]: https://github.com/unir0x/waveshare-voice-satellite/releases/tag/v0.9.4
[0.9.3]: https://github.com/unir0x/waveshare-voice-satellite/releases/tag/v0.9.3
[0.9.2]: https://github.com/unir0x/waveshare-voice-satellite/releases/tag/v0.9.2
[0.9.1]: https://github.com/unir0x/waveshare-voice-satellite/releases/tag/v0.9.1
[0.9.0]: https://github.com/unir0x/waveshare-voice-satellite/releases/tag/v0.9.0
