#!/usr/bin/env bash
# MyBGInfo macOS installer
# Installs the tool and registers it as a LaunchAgent to auto-start at login.

set -e

INSTALL_DIR="$HOME/Library/Application Support/MyBGInfo"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$LAUNCH_AGENTS_DIR/com.mybginfo.plist"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "Installing MyBGInfo to $INSTALL_DIR ..."

# Install Python dependencies
pip install --user pillow psutil

# Create installation directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$LAUNCH_AGENTS_DIR"

# Copy source files, assets, and config
cp -r "$REPO_ROOT/src"    "$INSTALL_DIR/"
cp -r "$REPO_ROOT/assets" "$INSTALL_DIR/"
cp -r "$REPO_ROOT/config" "$INSTALL_DIR/"

# Detect python path
PYTHON_BIN=$(command -v python3 || command -v python)

# Create LaunchAgent plist
cat > "$PLIST_FILE" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.mybginfo</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_BIN</string>
        <string>-m</string>
        <string>src.bginfo</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$INSTALL_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$INSTALL_DIR/mybginfo.log</string>
    <key>StandardErrorPath</key>
    <string>$INSTALL_DIR/mybginfo_err.log</string>
</dict>
</plist>
PLIST

# Load the LaunchAgent
launchctl load "$PLIST_FILE"

echo ""
echo "Installation complete!"
echo "MyBGInfo will run automatically at login."
echo "Run manually with: cd \"$INSTALL_DIR\" && python -m src.bginfo"
echo "Or launch the GUI: cd \"$INSTALL_DIR\" && python -m src.bginfo --gui"
