import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import binary_sensor, i2c, sensor, text_sensor
from esphome.const import (
    CONF_ID,
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_BATTERY_CHARGING,
    DEVICE_CLASS_PLUG,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_VOLTAGE,
    ENTITY_CATEGORY_DIAGNOSTIC,
    STATE_CLASS_MEASUREMENT,
    UNIT_CELSIUS,
    UNIT_PERCENT,
    UNIT_VOLT,
)

DEPENDENCIES = ["i2c"]
AUTO_LOAD = ["sensor", "binary_sensor", "text_sensor"]

ns = cg.esphome_ns.namespace("axp2101_lite")
Axp2101Lite = ns.class_("Axp2101Lite", cg.PollingComponent, i2c.I2CDevice)


def _volt():
    return sensor.sensor_schema(
        unit_of_measurement=UNIT_VOLT,
        accuracy_decimals=2,
        device_class=DEVICE_CLASS_VOLTAGE,
        state_class=STATE_CLASS_MEASUREMENT,
    )


SENSORS = {
    "battery_level": ("set_level", sensor.sensor_schema(
        unit_of_measurement=UNIT_PERCENT,
        accuracy_decimals=0,
        device_class=DEVICE_CLASS_BATTERY,
        state_class=STATE_CLASS_MEASUREMENT,
    )),
    "battery_voltage": ("set_voltage", _volt()),
    "usb_voltage": ("set_vbus", _volt()),
    "system_voltage": ("set_vsys", _volt()),
    "temperature": ("set_temperature", sensor.sensor_schema(
        unit_of_measurement=UNIT_CELSIUS,
        accuracy_decimals=1,
        device_class=DEVICE_CLASS_TEMPERATURE,
        state_class=STATE_CLASS_MEASUREMENT,
        entity_category=ENTITY_CATEGORY_DIAGNOSTIC,
    )),
}
BINARY_SENSORS = {
    "charging": ("set_charging", binary_sensor.binary_sensor_schema(device_class=DEVICE_CLASS_BATTERY_CHARGING)),
    "battery_connected": ("set_connected", binary_sensor.binary_sensor_schema()),
    "usb_connected": ("set_usb", binary_sensor.binary_sensor_schema(device_class=DEVICE_CLASS_PLUG)),
}

CONFIG_SCHEMA = (
    cv.Schema(
        {
            cv.GenerateID(): cv.declare_id(Axp2101Lite),
            **{cv.Optional(k): v[1] for k, v in SENSORS.items()},
            **{cv.Optional(k): v[1] for k, v in BINARY_SENSORS.items()},
            cv.Optional("charge_state"): text_sensor.text_sensor_schema(),
        }
    )
    .extend(cv.polling_component_schema("30s"))
    .extend(i2c.i2c_device_schema(0x34))
)


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await i2c.register_i2c_device(var, config)

    for key, (setter, _) in SENSORS.items():
        if key in config:
            s = await sensor.new_sensor(config[key])
            cg.add(getattr(var, setter)(s))
    for key, (setter, _) in BINARY_SENSORS.items():
        if key in config:
            s = await binary_sensor.new_binary_sensor(config[key])
            cg.add(getattr(var, setter)(s))
    if "charge_state" in config:
        s = await text_sensor.new_text_sensor(config["charge_state"])
        cg.add(var.set_charge_state(s))
