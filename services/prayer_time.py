import json
import os
from datetime import datetime

import config


def load_prayer_times():
    """Load prayer times from cached JSON file."""
    if not os.path.exists(config.PRAYER_DATA_FILE):
        return {}

    with open(config.PRAYER_DATA_FILE, "r") as f:
        return json.load(f)


def get_today_times(prayer_data):
    """Get prayer times for today. Key format: DD-MM-YYYY."""
    today = datetime.now().strftime("%d-%m-%Y")
    return prayer_data.get(today)


def get_next_prayer(today_times):
    """Determine the next upcoming prayer based on current time."""
    if not today_times:
        return None, None

    now = datetime.now().strftime("%H:%M")
    prayer_order = ["subuh", "syuruk", "zohor", "asar", "maghrib", "isyak"]

    for prayer in prayer_order:
        prayer_time = today_times.get(prayer)
        if prayer_time and prayer_time > now:
            return prayer, prayer_time

    # All prayers passed — next is subuh tomorrow
    return "subuh", today_times.get("subuh")


def is_prayer_time_now(today_times):
    """Check if current time is within prayer alert window."""
    if not today_times:
        return False, None

    now = datetime.now()
    now_str = now.strftime("%H:%M")
    prayer_names = ["subuh", "zohor", "asar", "maghrib", "isyak"]

    for prayer in prayer_names:
        prayer_time_str = today_times.get(prayer)
        if not prayer_time_str:
            continue

        prayer_hour, prayer_min = map(int, prayer_time_str.split(":"))
        prayer_dt = now.replace(hour=prayer_hour, minute=prayer_min, second=0)

        diff_seconds = (now - prayer_dt).total_seconds()
        alert_window = config.MASUK_DURATION_SECONDS + config.COUNTDOWN_DURATION_SECONDS + config.JEMAAH_DURATION_SECONDS
        if 0 <= diff_seconds <= alert_window:
            return True, prayer

    return False, None
