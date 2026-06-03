import os

import config

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}


def get_event_images():
    """Return list of event image filenames sorted by name."""
    if not os.path.exists(config.EVENTS_DIR):
        return []

    images = []
    for f in sorted(os.listdir(config.EVENTS_DIR)):
        ext = os.path.splitext(f)[1].lower()
        if ext in ALLOWED_EXTENSIONS:
            images.append(f)

    return images
