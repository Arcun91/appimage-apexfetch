#!/usr/bin/env bash
# ==============================================================================
# ApexFetch macOS Builder Script
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

APP_NAME="ApexFetch"
OUT_DIR="$SCRIPT_DIR/dist"
ARCH="$(uname -m)"

mkdir -p "$OUT_DIR"

echo "==> Building ${APP_NAME} for macOS (${ARCH})..."

# Check if pyinstaller is available
if ! command -v pyinstaller &>/dev/null; then
    echo "==> PyInstaller not found. Creating temporary build environment..."
    python3 -m venv "$SCRIPT_DIR/build/venv_mac"
    "$SCRIPT_DIR/build/venv_mac/bin/pip" install --quiet --upgrade pip pyinstaller
    PYINSTALLER="$SCRIPT_DIR/build/venv_mac/bin/pyinstaller"
else
    PYINSTALLER="pyinstaller"
fi

# 1. Compile Standalone CLI Binary
echo "==> Compiling standalone binary..."
"$PYINSTALLER" --clean --onefile \
    --name apexfetch \
    --distpath "$OUT_DIR/bin" \
    --workpath "$SCRIPT_DIR/build/pyinstaller_work" \
    --specpath "$SCRIPT_DIR/build" \
    "$SCRIPT_DIR/apexfetch.py"

# Package portable tarball
TAR_NAME="${APP_NAME}-macOS-${ARCH}.tar.gz"
echo "==> Creating portable CLI archive: ${TAR_NAME}..."
tar -czf "$OUT_DIR/$TAR_NAME" -C "$OUT_DIR/bin" apexfetch

# 2. Create macOS .app Bundle (Double-click in Finder)
APP_BUNDLE="$OUT_DIR/${APP_NAME}.app"
echo "==> Creating macOS Application Bundle: ${APP_BUNDLE}..."
rm -rf "$APP_BUNDLE"
mkdir -p "$APP_BUNDLE/Contents/MacOS"
mkdir -p "$APP_BUNDLE/Contents/Resources"

# Launcher script inside .app that invokes Terminal.app
cat << 'EOF' > "$APP_BUNDLE/Contents/MacOS/launcher"
#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
osascript -e 'tell application "Terminal" to do script "'"$DIR"'/apexfetch --hold"'
EOF
chmod +x "$APP_BUNDLE/Contents/MacOS/launcher"
cp "$OUT_DIR/bin/apexfetch" "$APP_BUNDLE/Contents/MacOS/apexfetch"

# Info.plist metadata
cat << EOF > "$APP_BUNDLE/Contents/Info.plist"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleIdentifier</key>
    <string>com.arcun91.apexfetch</string>
    <key>CFBundleName</key>
    <string>ApexFetch</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>LSUIElement</key>
    <true/>
</dict>
</plist>
EOF

# Compress .app into zip
if command -v zip &>/dev/null; then
    echo "==> Zipping ${APP_NAME}.app bundle..."
    (cd "$OUT_DIR" && zip -r -q "${APP_NAME}-macOS.app.zip" "${APP_NAME}.app")
fi

echo "==> macOS build complete!"
echo "==> Artifacts in ${OUT_DIR}:"
ls -lh "$OUT_DIR"
