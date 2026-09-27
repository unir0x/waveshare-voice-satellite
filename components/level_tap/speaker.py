"""Pass-through speaker that measures the audio level on its way to the output speaker."""
import esphome.codegen as cg
from esphome.components import audio, speaker
import esphome.config_validation as cv
from esphome.const import (
    CONF_BITS_PER_SAMPLE,
    CONF_ID,
    CONF_NUM_CHANNELS,
    CONF_OUTPUT_SPEAKER,
    CONF_SAMPLE_RATE,
    PLATFORM_ESP32,
)
from esphome.types import ConfigType

from . import level_tap_ns

AUTO_LOAD = ["audio"]

LevelTapSpeaker = level_tap_ns.class_("LevelTapSpeaker", cg.Component, speaker.Speaker)

CONF_OUTPUT_DELAY = "output_delay"


def _set_stream_limits(config: ConfigType) -> ConfigType:
    # Pure pass-through: accept exactly the stream the output speaker is configured for.
    audio.set_stream_limits(
        min_bits_per_sample=config[CONF_BITS_PER_SAMPLE],
        max_bits_per_sample=config[CONF_BITS_PER_SAMPLE],
        min_channels=config[CONF_NUM_CHANNELS],
        max_channels=config[CONF_NUM_CHANNELS],
        min_sample_rate=config[CONF_SAMPLE_RATE],
        max_sample_rate=config[CONF_SAMPLE_RATE],
    )(config)
    return config


CONFIG_SCHEMA = cv.All(
    speaker.SPEAKER_SCHEMA.extend(
        {
            cv.GenerateID(): cv.declare_id(LevelTapSpeaker),
            cv.Required(CONF_OUTPUT_SPEAKER): cv.use_id(speaker.Speaker),
            cv.Required(CONF_SAMPLE_RATE): cv.int_range(8000, 48000),
            cv.Optional(CONF_NUM_CHANNELS, default=1): cv.int_range(1, 2),
            cv.Optional(CONF_BITS_PER_SAMPLE, default=16): cv.one_of(16, int=True),
            # time between writing samples to the output speaker and hearing them (its buffer + DMA)
            cv.Optional(CONF_OUTPUT_DELAY, default="150ms"): cv.positive_time_period_milliseconds,
        }
    ).extend(cv.COMPONENT_SCHEMA),
    cv.only_on([PLATFORM_ESP32]),
    _set_stream_limits,
)


def _validate_output(config: ConfigType) -> None:
    audio.final_validate_audio_schema(
        "level_tap",
        audio_device=CONF_OUTPUT_SPEAKER,
        bits_per_sample=config[CONF_BITS_PER_SAMPLE],
        channels=config[CONF_NUM_CHANNELS],
        sample_rate=config[CONF_SAMPLE_RATE],
    )(config)


FINAL_VALIDATE_SCHEMA = _validate_output


async def to_code(config: ConfigType) -> None:
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await speaker.register_speaker(var, config)
    output = await cg.get_variable(config[CONF_OUTPUT_SPEAKER])
    cg.add(var.set_output_speaker(output))
    cg.add(var.set_output_delay(config[CONF_OUTPUT_DELAY]))
