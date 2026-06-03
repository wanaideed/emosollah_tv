#!/bin/bash
# Musollah Content TV - Kiosk Launcher for Raspberry Pi
# This script starts Flask and Chromium in kiosk mode.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Disable screen blanking
xset s off
xset -dpms
xset s noblank

# Hide mouse cursor
unclutter -idle 0 &

# Start Flask in background
python3 app.py &
FLASK_PID=$!

# Wait for Flask to start
sleep 3

# Launch Chromium in kiosk mode
chromium-browser \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-restore-session-state \
    --disable-translate \
    --no-first-run \
    --start-fullscreen \
    --incognito \
    --autoplay-policy=no-user-gesture-required \
    http://localhost:5001 &

CHROMIUM_PID=$!

# Trap exit to clean up
trap "kill $FLASK_PID $CHROMIUM_PID 2>/dev/null" EXIT

# Wait for either process to exit
wait
