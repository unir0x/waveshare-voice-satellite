#pragma once

#include "esphome/core/time.h"

// Power save schedule (local time): every night 01:00-06:00 and Monday-Friday 09:00-15:00.
// Returns the end of the current window in minutes since midnight, or -1 outside a window.
inline int sleep_window_end(const esphome::ESPTime &t) {
  int m = t.hour * 60 + t.minute;
  if (m >= 60 && m < 360)
    return 360;
  bool weekday = t.day_of_week >= 2 && t.day_of_week <= 6;  // ESPTime: 1 = Sunday ... 7 = Saturday
  if (weekday && m >= 540 && m < 900)
    return 900;
  return -1;
}

// Night quiet hours 01:00-06:00: no spontaneous sounds (battery warnings are postponed).
inline bool quiet_hours(const esphome::ESPTime &t) {
  int m = t.hour * 60 + t.minute;
  return m >= 60 && m < 360;
}
