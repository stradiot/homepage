#!/bin/sh
# Register serve.py as a per-user launchd agent so the new tab page has a
# server to talk to from login onward.
set -eu

REPO=$(cd "$(dirname "$0")" && pwd)
PORT=$(sed -n 's/^PORT = //p' "$REPO/serve.py")
LABEL=local.homepage
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

# Apple's /usr/bin/python3 rather than whichever python3 is on PATH: launchd
# has no PATH to speak of, and this one survives Homebrew upgrades and prunes.
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>$REPO/serve.py</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardErrorPath</key>
  <string>/tmp/$LABEL.err</string>
</dict>
</plist>
EOF

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"

echo "serving $REPO at http://localhost:$PORT/"
echo "point New Tab Override's Custom URL at that; errors land in /tmp/$LABEL.err"
