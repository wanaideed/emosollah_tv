import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")


def _load_settings():
    with open(SETTINGS_FILE, "r") as f:
        return json.load(f)


_settings = _load_settings()

# e-Musollah API
E_MUSOLLAH_URL = _settings.get("e_musollah_url", "http://localhost:5000")

# JAKIM Zone
ZONE = _settings.get("zone", "SGR01")

# Template
TEMPLATE = _settings.get("template", "dark")

# Display settings
ENABLE_EVENT_ROTATION = _settings.get("enable_event_rotation", True)
ENABLE_AKTIVITI_CALENDAR = _settings.get("enable_aktiviti_calendar", False)
ENABLE_TICKER = _settings.get("enable_ticker", True)
ENABLE_BACKGROUND_IMAGE = _settings.get("enable_background_image", False)
BACKGROUND_IMAGE_DIR = os.path.join(BASE_DIR, "static", "content", "background")
PAGE_ROTATION_SECONDS = _settings.get("page_rotation_seconds", 30)
MASUK_DURATION_SECONDS = _settings.get("masuk_duration_seconds", 30)
COUNTDOWN_DURATION_SECONDS = _settings.get("countdown_duration_seconds", 600)
JEMAAH_DURATION_SECONDS = _settings.get("jemaah_duration_seconds", 600)
MASUK_DURATION_MINUTES = _settings.get("masuk_duration_minutes", 1)
IQOMAH_DURATION_MINUTES = _settings.get("iqomah_duration_minutes", 10)
SOLAT_DURATION_MINUTES = _settings.get("solat_duration_minutes", 20)
SCREEN_WIDTH = _settings.get("screen_width", 1920)
SCREEN_HEIGHT = _settings.get("screen_height", 1080)

# Paths
DATA_DIR = os.path.join(BASE_DIR, "data")
EVENTS_DIR = os.path.join(BASE_DIR, "static", "content", "events")
PRAYER_DATA_FILE = os.path.join(DATA_DIR, "prayer_times.json")

# Flask
HOST = _settings.get("host", "0.0.0.0")
PORT = _settings.get("port", 5001)

# Musollah info
MUSOLLAH_NAME = _settings.get("musollah_name", "Musollah Al-Ikhlas")


def reload_settings():
    """Reload settings from file and update module globals."""
    global _settings, E_MUSOLLAH_URL, ZONE, TEMPLATE, MUSOLLAH_NAME
    global ENABLE_EVENT_ROTATION, ENABLE_AKTIVITI_CALENDAR, ENABLE_TICKER, ENABLE_BACKGROUND_IMAGE
    global PAGE_ROTATION_SECONDS, MASUK_DURATION_SECONDS, COUNTDOWN_DURATION_SECONDS, JEMAAH_DURATION_SECONDS
    global MASUK_DURATION_MINUTES, IQOMAH_DURATION_MINUTES, SOLAT_DURATION_MINUTES

    _settings = _load_settings()

    E_MUSOLLAH_URL = _settings.get("e_musollah_url", "http://localhost:5000")
    ZONE = _settings.get("zone", "SGR01")
    TEMPLATE = _settings.get("template", "dark")
    MUSOLLAH_NAME = _settings.get("musollah_name", "Musollah Al-Ikhlas")
    ENABLE_EVENT_ROTATION = _settings.get("enable_event_rotation", True)
    ENABLE_AKTIVITI_CALENDAR = _settings.get("enable_aktiviti_calendar", False)
    ENABLE_TICKER = _settings.get("enable_ticker", True)
    ENABLE_BACKGROUND_IMAGE = _settings.get("enable_background_image", False)
    PAGE_ROTATION_SECONDS = _settings.get("page_rotation_seconds", 30)
    MASUK_DURATION_SECONDS = _settings.get("masuk_duration_seconds", 30)
    COUNTDOWN_DURATION_SECONDS = _settings.get("countdown_duration_seconds", 600)
    JEMAAH_DURATION_SECONDS = _settings.get("jemaah_duration_seconds", 600)
    MASUK_DURATION_MINUTES = _settings.get("masuk_duration_minutes", 1)
    IQOMAH_DURATION_MINUTES = _settings.get("iqomah_duration_minutes", 10)
    SOLAT_DURATION_MINUTES = _settings.get("solat_duration_minutes", 20)
