import os
import json
import glob
import shutil
from datetime import datetime

import requests
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

import config
from services.prayer_time import load_prayer_times, get_today_times, get_next_prayer, is_prayer_time_now
from services.content_manager import get_event_images

app = Flask(__name__)
CORS(app, resources={r'/api/*': {'origins': '*'}})

# Load prayer data once at startup
prayer_data = load_prayer_times()


@app.route("/")
def kiosk():
    bg_url = None
    if config.ENABLE_BACKGROUND_IMAGE:
        bg_path = os.path.join(config.BACKGROUND_IMAGE_DIR, "background.png")
        if os.path.exists(bg_path):
            mtime = int(os.path.getmtime(bg_path))
            bg_url = f"/static/content/background/background.png?v={mtime}"

    return render_template("kiosk.html",
        musollah_name=config.MUSOLLAH_NAME,
        template=config.TEMPLATE,
        enable_ticker=config.ENABLE_TICKER,
        background_url=bg_url,
    )


@app.route("/waktu_solat")
def waktu_solat():
    solat = request.args.get("solat", "")
    return render_template("waktu_solat/index.html",
        musollah_name=config.MUSOLLAH_NAME,
        template=config.TEMPLATE,
        solat=solat,
        masuk_duration_minutes=config.MASUK_DURATION_MINUTES,
        iqomah_duration_minutes=config.IQOMAH_DURATION_MINUTES,
        solat_duration_minutes=config.SOLAT_DURATION_MINUTES,
    )


@app.route("/api/prayer-times")
def api_prayer_times():
    """Return today's prayer times."""
    today_times = get_today_times(prayer_data)
    if not today_times:
        return jsonify({"error": "No prayer data for today"}), 404

    next_prayer, next_time = get_next_prayer(today_times)
    alert_active, alert_prayer = is_prayer_time_now(today_times)

    return jsonify({
        "times": today_times,
        "next_prayer": next_prayer,
        "next_time": next_time,
        "alert_active": alert_active,
        "alert_prayer": alert_prayer,
    })


@app.route("/api/events")
def api_events():
    """Return list of event image URLs."""
    images = get_event_images()
    urls = [f"/static/content/events/{img}" for img in images]
    return jsonify({"images": urls})


@app.route("/api/config")
def api_config():
    """Return display config for frontend."""
    return jsonify({
        "rotation_seconds": config.PAGE_ROTATION_SECONDS,
        "masuk_duration_seconds": config.MASUK_DURATION_SECONDS,
        "countdown_duration_seconds": config.COUNTDOWN_DURATION_SECONDS,
        "jemaah_duration_seconds": config.JEMAAH_DURATION_SECONDS,
        "musollah_name": config.MUSOLLAH_NAME,
        "enable_event_rotation": config.ENABLE_EVENT_ROTATION,
        "enable_aktiviti_calendar": config.ENABLE_AKTIVITI_CALENDAR,
        "enable_ticker": config.ENABLE_TICKER,
        "template": config.TEMPLATE,
    })


@app.route("/api/test-alert/<prayer>")
def test_alert(prayer):
    """Test endpoint - triggers prayer alert. Usage: /api/test-alert/zohor"""
    return jsonify({
        "times": get_today_times(prayer_data) or {},
        "next_prayer": prayer,
        "next_time": "00:00",
        "alert_active": True,
        "alert_prayer": prayer,
    })


# ---------------------------------------------------------------------------
# Sync endpoints — pull from e-Musollah
# ---------------------------------------------------------------------------

def _emusollah_url():
    """Get e-Musollah API base URL from config."""
    return config.E_MUSOLLAH_URL.rstrip('/')


@app.route("/api/sync/settings")
def sync_settings():
    """Fetch TV settings from e-Musollah and overwrite local settings.json."""
    try:
        url = f"{_emusollah_url()}/api/musollah/tv-settings"
        res = requests.get(url, timeout=15)
        res.raise_for_status()
        data = res.json()

        if not data.get('success'):
            return jsonify({"success": False, "message": "e-Musollah returned error."}), 502

        remote = data['data']

        # Read current local settings to preserve e_musollah_url and local-only fields
        with open(config.SETTINGS_FILE, 'r') as f:
            local = json.load(f)

        # Map remote fields to local settings.json keys
        local['zone']                       = remote.get('zone', local.get('zone', 'SGR01'))
        local['musollah_name']              = remote.get('musollah_name') or local.get('musollah_name', '')
        local['template']                   = remote.get('template', local.get('template', 'dark'))
        local['enable_event_rotation']      = remote.get('enable_event_rotation', False)
        local['enable_aktiviti_calendar']   = remote.get('enable_aktiviti_calendar', False)
        local['enable_ticker']              = remote.get('enable_ticker', False)
        local['enable_background_image']    = remote.get('enable_background_image', True)
        local['page_rotation_seconds']      = remote.get('page_rotation_seconds', 30)
        local['masuk_duration_seconds']     = remote.get('masuk_duration_seconds', 30)
        local['countdown_duration_seconds'] = remote.get('countdown_duration_seconds', 600)
        local['jemaah_duration_seconds']    = remote.get('jemaah_duration_seconds', 600)
        # Keep e_musollah_url, host, port, screen_width, screen_height unchanged

        with open(config.SETTINGS_FILE, 'w') as f:
            json.dump(local, f, indent=4)

        # Reload config
        config.reload_settings()

        return jsonify({
            "success": True,
            "message": "Settings synced successfully.",
            "data": local,
        })

    except requests.RequestException as e:
        return jsonify({"success": False, "message": f"Cannot reach e-Musollah: {e}"}), 502
    except Exception as e:
        return jsonify({"success": False, "message": f"Sync failed: {e}"}), 500


@app.route("/api/sync/events")
def sync_events():
    """Fetch event images + aktiviti posters from e-Musollah, clear local events folder, download all."""
    try:
        events_dir = config.EVENTS_DIR
        os.makedirs(events_dir, exist_ok=True)

        # Clear existing event images
        for old_file in glob.glob(os.path.join(events_dir, '*')):
            if os.path.isfile(old_file) and not old_file.endswith('.gitkeep'):
                os.remove(old_file)

        downloaded = 0

        # 1. Fetch TV event images (from Pengurusan Event)
        try:
            url = f"{_emusollah_url()}/api/musollah/tv-events"
            res = requests.get(url, timeout=15)
            res.raise_for_status()
            data = res.json()
            if data.get('success'):
                for ev in data.get('data', []):
                    img_url = ev.get('url', '')
                    filename = ev.get('filename', '')
                    if not img_url or not filename:
                        continue
                    try:
                        full_url = f"{_emusollah_url()}{img_url}"
                        img_res = requests.get(full_url, timeout=30)
                        img_res.raise_for_status()
                        filepath = os.path.join(events_dir, filename)
                        with open(filepath, 'wb') as f:
                            f.write(img_res.content)
                        downloaded += 1
                    except Exception:
                        continue
        except Exception:
            pass

        # 2. Fetch aktiviti posters for current month (if enabled)
        aktiviti_count = 0
        if config.ENABLE_AKTIVITI_CALENDAR:
            try:
                url = f"{_emusollah_url()}/api/musollah/tv-aktiviti-posters"
                res = requests.get(url, timeout=15)
                res.raise_for_status()
                data = res.json()
                if data.get('success'):
                    for item in data.get('data', []):
                        img_url = item.get('url', '')
                        filename = item.get('filename', '')
                        if not img_url or not filename:
                            continue
                        # Prefix with date to ensure sorted display order (asc)
                        tarikh = item.get('tarikh', '')
                        save_name = f"aktiviti_{tarikh}_{filename}"
                        try:
                            full_url = f"{_emusollah_url()}{img_url}"
                            img_res = requests.get(full_url, timeout=30)
                            img_res.raise_for_status()
                            filepath = os.path.join(events_dir, save_name)
                            with open(filepath, 'wb') as f:
                                f.write(img_res.content)
                            downloaded += 1
                            aktiviti_count += 1
                        except Exception:
                            continue
            except Exception:
                pass

        msg = f"Events synced. {downloaded} images downloaded"
        if aktiviti_count > 0:
            msg += f" ({aktiviti_count} dari Aktiviti Calendar)"
        msg += "."

        return jsonify({
            "success": True,
            "message": msg,
            "count": downloaded,
            "aktiviti_count": aktiviti_count,
        })

    except Exception as e:
        return jsonify({"success": False, "message": f"Sync failed: {e}"}), 500


@app.route("/api/sync/background")
def sync_background():
    """Fetch background image from e-Musollah and overwrite local background."""
    try:
        # First get settings to find background_url
        url = f"{_emusollah_url()}/api/musollah/tv-settings"
        res = requests.get(url, timeout=15)
        res.raise_for_status()
        data = res.json()

        if not data.get('success'):
            return jsonify({"success": False, "message": "e-Musollah returned error."}), 502

        bg_url = data['data'].get('background_url')
        if not bg_url:
            return jsonify({"success": True, "message": "No background image configured."})

        # Download background
        full_url = f"{_emusollah_url()}{bg_url}"
        img_res = requests.get(full_url, timeout=30)
        img_res.raise_for_status()

        bg_dir = config.BACKGROUND_IMAGE_DIR
        os.makedirs(bg_dir, exist_ok=True)
        bg_path = os.path.join(bg_dir, "background.png")

        with open(bg_path, 'wb') as f:
            f.write(img_res.content)

        return jsonify({
            "success": True,
            "message": "Background image synced successfully.",
        })

    except requests.RequestException as e:
        return jsonify({"success": False, "message": f"Cannot reach e-Musollah: {e}"}), 502
    except Exception as e:
        return jsonify({"success": False, "message": f"Sync failed: {e}"}), 500


@app.route("/api/sync/prayer-times")
def sync_prayer_times():
    """Fetch prayer times from JAKIM API using zone from local settings."""
    global prayer_data

    zone = config.ZONE
    year = datetime.now().year
    all_times = {}

    try:
        for month in range(1, 13):
            params = {
                "r": "esolatApi/takwimsolat",
                "period": "month",
                "zone": zone,
                "year": year,
                "month": month,
            }
            res = requests.get("https://www.e-solat.gov.my/index.php", params=params, timeout=30)
            res.raise_for_status()
            api_data = res.json()

            prayer_list = api_data.get("prayerTime", [])
            for entry in prayer_list:
                date_raw = entry.get("date", "")
                try:
                    dt = datetime.strptime(date_raw.strip(), "%d-%b-%Y")
                    date_key = dt.strftime("%d-%m-%Y")
                except ValueError:
                    continue

                all_times[date_key] = {
                    "hijri": entry.get("hijri", "").strip(),
                    "day": entry.get("day", "").strip(),
                    "subuh": entry.get("fajr", "").strip()[:5],
                    "syuruk": entry.get("syuruk", "").strip()[:5],
                    "zohor": entry.get("dhuhr", "").strip()[:5],
                    "asar": entry.get("asr", "").strip()[:5],
                    "maghrib": entry.get("maghrib", "").strip()[:5],
                    "isyak": entry.get("isha", "").strip()[:5],
                }

        if not all_times:
            return jsonify({"success": False, "message": "No prayer data received from JAKIM API."}), 502

        # Save to file
        os.makedirs(config.DATA_DIR, exist_ok=True)
        with open(config.PRAYER_DATA_FILE, 'w') as f:
            json.dump(all_times, f, indent=2)

        # Reload into memory
        prayer_data = load_prayer_times()

        return jsonify({
            "success": True,
            "message": f"Prayer times synced for zone {zone}, year {year}.",
            "zone": zone,
            "days": len(all_times),
        })

    except requests.RequestException as e:
        return jsonify({"success": False, "message": f"JAKIM API error: {e}"}), 502
    except Exception as e:
        return jsonify({"success": False, "message": f"Sync failed: {e}"}), 500


if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=False)
