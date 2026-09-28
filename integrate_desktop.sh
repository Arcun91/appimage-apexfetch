#!/usr/bin/env bash
# ==============================================================================
# ApexFetch Desktop Integration & AppImage Double-Click Enabler
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPIMAGE_PATH="$SCRIPT_DIR/dist/ApexFetch-x86_64.AppImage"
APPS_DIR="$HOME/.local/share/applications"
ICONS_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"

mkdir -p "$APPS_DIR" "$ICONS_DIR"

echo "==> Configuring GNOME/Linux to enable double-click on AppImages..."

# 1. Enable double-click execution on .AppImage files in Nautilus / GIO
cat << 'EOF' > "$APPS_DIR/appimage-executor.desktop"
[Desktop Entry]
Type=Application
Name=AppImage Executor
Comment=Execute AppImage files directly
Exec=/bin/sh -c 'exec "$1"' dummy %f
Terminal=false
MimeType=application/vnd.appimage;application/x-iso9660-appimage;
NoDisplay=true
EOF

update-desktop-database "$APPS_DIR" 2>/dev/null || true
xdg-mime default appimage-executor.desktop application/vnd.appimage 2>/dev/null || true

# 2. Install ApexFetch to the Application Launcher Menu (Super / Windows key)
if [ -f "$APPIMAGE_PATH" ]; then
    echo "==> Adding ApexFetch to your system Application Menu..."
    cp "$SCRIPT_DIR/apexfetch.svg" "$ICONS_DIR/apexfetch.svg"
    
    cat << EOF > "$APPS_DIR/apexfetch.desktop"
[Desktop Entry]
Type=Application
Name=ApexFetch
GenericName=System Information Fetcher
Comment=High-Precision System & Hardware Identifier for Linux
Exec=${APPIMAGE_PATH} --hold
Icon=apexfetch
Terminal=true
Categories=System;Utility;ConsoleOnly;
Keywords=system;fetch;hardware;neofetch;fastfetch;specs;
EOF

    update-desktop-database "$APPS_DIR" 2>/dev/null || true
fi

echo "==> Done! You can now:"
echo "    1. Double-click ApexFetch-x86_64.AppImage in the file manager"
echo "    2. Find 'ApexFetch' directly in your GNOME / Desktop Applications menu"
