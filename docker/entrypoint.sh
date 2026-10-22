#!/usr/bin/env bash
set -e

# Start isolated Xvfb virtual display in RAM (Screen 99, 1280x800x24)
export DISPLAY=:99
Xvfb :99 -screen 0 1280x800x24 -ac -nolisten tcp -extension GLX +render -noreset &
XVFB_PID=$!

# Wait for Xvfb to initialize
sleep 1

# Launch minimal window manager
fluxbox &
WM_PID=$!

echo "Headless virtual display initialized on DISPLAY=:99 (PID: $XVFB_PID, WM: $WM_PID)"

# Execute guest command or keep alive daemon
exec "$@"
