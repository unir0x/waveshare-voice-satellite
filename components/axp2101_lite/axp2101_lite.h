#pragma once

#include "esphome/core/component.h"
#include "esphome/core/log.h"
#include "esphome/components/i2c/i2c.h"
#include "esphome/components/sensor/sensor.h"
#include "esphome/components/binary_sensor/binary_sensor.h"
#include "esphome/components/text_sensor/text_sensor.h"

namespace esphome {
namespace axp2101_lite {

class Axp2101Lite : public PollingComponent, public i2c::I2CDevice {
 public:
  void set_level(sensor::Sensor *s) { level_ = s; }
  void set_voltage(sensor::Sensor *s) { voltage_ = s; }
  void set_vbus(sensor::Sensor *s) { vbus_ = s; }
  void set_vsys(sensor::Sensor *s) { vsys_ = s; }
  void set_temperature(sensor::Sensor *s) { temperature_ = s; }
  void set_charging(binary_sensor::BinarySensor *s) { charging_ = s; }
  void set_connected(binary_sensor::BinarySensor *s) { connected_ = s; }
  void set_usb(binary_sensor::BinarySensor *s) { usb_ = s; }
  void set_charge_state(text_sensor::TextSensor *s) { charge_state_ = s; }

  void setup() override {
    uint8_t v;
    // Monitoring only: enable ADC channels VBAT/VBUS/VSYS/die temp (0x30), fuel gauge (0x18 bit3) and
    // battery detection (0x68 bit0). No power rails are touched.
    if (this->read_byte(0x30, &v)) this->write_byte(0x30, v | 0x1D);
    if (this->read_byte(0x18, &v)) this->write_byte(0x18, v | 0x08);
    if (this->read_byte(0x68, &v)) this->write_byte(0x68, v | 0x01);
  }

  void update() override {
    uint8_t status1 = 0, status2 = 0, pct = 0;
    if (!this->read_byte(0x00, &status1) || !this->read_byte(0x01, &status2)) {
      ESP_LOGW("axp2101_lite", "status register read failed");
      return;
    }
    uint16_t vbat = 0, vbus = 0, vsys = 0, tdie = 0;
    bool have_vbat = this->read14_(0x34, &vbat);
    bool have_p = this->read_byte(0xA4, &pct);

    bool usb = status1 & 0x20;
    bool connected = (status1 & 0x08) || (have_vbat && vbat > 2500);
    bool charging = ((status2 >> 5) & 0x03) == 0x01;
    if (connected_ != nullptr) connected_->publish_state(connected);
    if (charging_ != nullptr) charging_->publish_state(charging);
    if (usb_ != nullptr) usb_->publish_state(usb);

    if (vbus_ != nullptr && this->read14_(0x38, &vbus)) vbus_->publish_state(usb ? vbus / 1000.0f : 0.0f);
    if (vsys_ != nullptr && this->read14_(0x3A, &vsys)) vsys_->publish_state(vsys / 1000.0f);
    if (temperature_ != nullptr && this->read14_(0x3C, &tdie))
      temperature_->publish_state(22.0f + (7274.0f - tdie) / 20.0f);

    if (charge_state_ != nullptr) {
      static const char *const STATES[] = {"Underhållsladdning", "Förladdning", "Laddar (konstant ström)",
                                           "Laddar (konstant spänning)", "Fulladdad", "Laddar inte"};
      uint8_t cs = status2 & 0x07;
      const char *txt = !connected ? "Inget batteri" : (cs < 6 ? STATES[cs] : "Okänt");
      if (charge_state_->state != txt)
        charge_state_->publish_state(txt);
    }

    if (!connected)
      return;
    if (voltage_ != nullptr && have_vbat) voltage_->publish_state(vbat / 1000.0f);
    if (level_ != nullptr && have_p && pct <= 100) level_->publish_state(pct);
  }

  float get_setup_priority() const override { return setup_priority::DATA; }

 protected:
  bool read14_(uint8_t reg, uint16_t *out) {
    uint8_t h = 0, l = 0;
    if (!this->read_byte(reg, &h) || !this->read_byte(reg + 1, &l))
      return false;
    *out = ((h & 0x3F) << 8) | l;
    return true;
  }

  sensor::Sensor *level_{nullptr};
  sensor::Sensor *voltage_{nullptr};
  sensor::Sensor *vbus_{nullptr};
  sensor::Sensor *vsys_{nullptr};
  sensor::Sensor *temperature_{nullptr};
  binary_sensor::BinarySensor *charging_{nullptr};
  binary_sensor::BinarySensor *connected_{nullptr};
  binary_sensor::BinarySensor *usb_{nullptr};
  text_sensor::TextSensor *charge_state_{nullptr};
};

}  // namespace axp2101_lite
}  // namespace esphome
