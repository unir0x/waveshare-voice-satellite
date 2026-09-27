# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/). The version lives in `waveshare-voice.yaml` (`substitutions: version`).

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

[0.9.2]: https://github.com/unir0x/waveshare-voice-satellite/releases/tag/v0.9.2
[0.9.1]: https://github.com/unir0x/waveshare-voice-satellite/releases/tag/v0.9.1
[0.9.0]: https://github.com/unir0x/waveshare-voice-satellite/releases/tag/v0.9.0
