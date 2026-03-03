#!/usr/bin/env bash
# MyBGInfo Linux installer
# Installs the tool and registers it to run at login via crontab.

set -e

INSTALL_DIR="$HOME/.local/share/mybginfo"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "Installing MyBGInfo to $INSTALL_DIR ..."

# Install Python dependencies
pip install --user pillow psutil

# Create installation directory
mkdir -p "$INSTALL_DIR"

# Copy source files, assets, and config
cp -r "$REPO_ROOT/src"    "$INSTALL_DIR/"
cp -r "$REPO_ROOT/assets" "$INSTALL_DIR/"
cp -r "$REPO_ROOT/config" "$INSTALL_DIR/"

# Add @reboot crontab entry (skip if already present)
CRON_CMD="@reboot cd \"$INSTALL_DIR\" && python -m src.bginfo"
if ! crontab -l 2>/dev/null | grep -qF "mybginfo"; then
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "Added crontab @reboot entry."
else
    echo "Crontab entry already exists. Skipping."
fi

echo ""
echo "Installation complete!"
echo "Run manually with: cd $INSTALL_DIR && python -m src.bginfo"
echo "Or launch the GUI: cd $INSTALL_DIR && python -m src.bginfo --gui"
