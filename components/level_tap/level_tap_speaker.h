#pragma once

#include <atomic>
#include <cmath>

#include "esphome/components/speaker/speaker.h"
#include "esphome/core/component.h"
#include "esphome/core/hal.h"

namespace esphome::level_tap {

// Pass-through speaker: forwards everything to the output speaker unchanged and records the RMS level of the
// audio it forwards (16-bit PCM) in 20 ms bins, so the UI can read the level that is audible right now.
class LevelTapSpeaker : public Component, public speaker::Speaker {
 public:
  void set_output_speaker(speaker::Speaker *output) { this->output_ = output; }
  void set_output_delay(uint32_t ms) { this->output_delay_ms_ = ms; }

  void setup() override {
    this->output_->add_audio_output_callback(
        [this](uint32_t frames, int64_t timestamp) { this->audio_output_callback_.call(frames, timestamp); });
  }

  void loop() override {
    // Mirror the output speaker's state: upstream components poll is_running()/is_stopped().
    if (this->output_->is_running())
      this->state_ = speaker::STATE_RUNNING;
    else if (this->output_->is_stopped())
      this->state_ = speaker::STATE_STOPPED;
  }

  float get_setup_priority() const override { return setup_priority::DATA; }

  void start() override {
    this->output_->set_audio_stream_info(this->audio_stream_info_);
    this->output_->start();
    if (this->state_ == speaker::STATE_STOPPED)
      this->state_ = speaker::STATE_STARTING;
  }
  void stop() override { this->output_->stop(); }
  void finish() override { this->output_->finish(); }
  bool has_buffered_data() const override { return this->output_->has_buffered_data(); }
  void set_pause_state(bool pause_state) override { this->output_->set_pause_state(pause_state); }
  bool get_pause_state() const override { return this->output_->get_pause_state(); }
  void set_volume(float volume) override {
    this->volume_ = volume;
    this->output_->set_volume(volume);
  }
  float get_volume() override { return this->output_->get_volume(); }
  void set_mute_state(bool mute_state) override {
    this->mute_state_ = mute_state;
    this->output_->set_mute_state(mute_state);
  }
  bool get_mute_state() override { return this->output_->get_mute_state(); }

  size_t play(const uint8_t *data, size_t length, TickType_t ticks_to_wait) override {
    size_t written = this->output_->play(data, length, ticks_to_wait);
    this->measure_(data, written);
    return written;
  }
  size_t play(const uint8_t *data, size_t length) override {
    size_t written = this->output_->play(data, length);
    this->measure_(data, written);
    return written;
  }

  /// RMS level (0..1) of the audio that is audible now: the loudest 20 ms bin within the last `window_ms`,
  /// shifted back by the output delay. Returns 0 if nothing was written in that period.
  float get_level(uint32_t window_ms = 100) const {
    uint32_t now = millis();
    uint32_t newest = now - this->output_delay_ms_;
    float level = 0.0f;
    for (const auto &bin : this->bins_) {
      uint32_t t = bin.time.load(std::memory_order_relaxed);
      if (t == 0 || (int32_t) (newest - t) < 0 || newest - t > window_ms)
        continue;
      level = std::max(level, bin.rms.load(std::memory_order_relaxed));
    }
    return level;
  }

 protected:
  struct Bin {
    std::atomic<uint32_t> time{0};
    std::atomic<float> rms{0.0f};
  };
  static constexpr size_t NUM_BINS = 32;  // 32 x 20 ms = 640 ms of history
  static constexpr uint32_t BIN_MS = 20;

  // Called from the audio task that feeds this speaker; bins are single-writer, read by the main loop.
  void measure_(const uint8_t *data, size_t length) {
    size_t n = length / 2;
    if (n == 0)
      return;
    const int16_t *s = reinterpret_cast<const int16_t *>(data);
    double sum = 0;
    for (size_t i = 0; i < n; i++)
      sum += (double) s[i] * s[i];
    float rms = std::sqrt(sum / n) / 32768.0f;

    uint32_t now = millis();
    uint32_t slot = now / BIN_MS;
    Bin &bin = this->bins_[slot % NUM_BINS];
    if (bin.time.load(std::memory_order_relaxed) / BIN_MS != slot) {
      bin.rms.store(rms, std::memory_order_relaxed);
      bin.time.store(now, std::memory_order_relaxed);
    } else if (rms > bin.rms.load(std::memory_order_relaxed)) {
      bin.rms.store(rms, std::memory_order_relaxed);
    }
  }

  speaker::Speaker *output_{nullptr};
  uint32_t output_delay_ms_{150};
  Bin bins_[NUM_BINS];
};

}  // namespace esphome::level_tap
