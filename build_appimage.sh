#!/usr/bin/env bash
# ==============================================================================
# ApexFetch AppImage Builder Script
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

APP_NAME="ApexFetch"
APP_DIR="$SCRIPT_DIR/build/AppDir"
OUT_DIR="$SCRIPT_DIR/dist"
ARCH="$(uname -m)"

echo "==> Building ${APP_NAME} for architecture: ${ARCH}"

# 1. Clean previous build directories
rm -rf "$SCRIPT_DIR/build" "$OUT_DIR"
mkdir -p "$APP_DIR/usr/bin"
mkdir -p "$APP_DIR/usr/share/icons/hicolor/scalable/apps"
mkdir -p "$OUT_DIR"

# 2. Check if PyInstaller is available or can be run in a temp venv
USE_PYINSTALLER=false
if command -v pyinstaller &>/dev/null; then
    USE_PYINSTALLER=true
    PYINSTALLER_BIN="pyinstaller"
else
    echo "==> PyInstaller not in PATH. Checking if virtualenv can be used..."
    if python3 -m venv --help &>/dev/null; then
        VENV_DIR="$SCRIPT_DIR/build/venv"
        echo "==> Creating temporary build environment at ${VENV_DIR}..."
        python3 -m venv "$VENV_DIR"
        "$VENV_DIR/bin/pip" install --quiet --upgrade pip pyinstaller
        PYINSTALLER_BIN="$VENV_DIR/bin/pyinstaller"
        USE_PYINSTALLER=true
    fi
fi

# 3. Compile or copy executable
if [ "$USE_PYINSTALLER" = true ]; then
    echo "==> Compiling standalone binary with PyInstaller..."
    "$PYINSTALLER_BIN" --clean --onefile \
        --name apexfetch \
        --distpath "$APP_DIR/usr/bin" \
        --workpath "$SCRIPT_DIR/build/pyinstaller_work" \
        --specpath "$SCRIPT_DIR/build" \
        "$SCRIPT_DIR/apexfetch.py"
else
    echo "==> Packaging as lightweight portable Python executable..."
    cp "$SCRIPT_DIR/apexfetch.py" "$APP_DIR/usr/bin/apexfetch"
    chmod +x "$APP_DIR/usr/bin/apexfetch"
fi

# 4. Copy Desktop file and Icons
echo "==> Setting up AppDir metadata..."
cp "$SCRIPT_DIR/apexfetch.desktop" "$APP_DIR/apexfetch.desktop"
cp "$SCRIPT_DIR/apexfetch.svg" "$APP_DIR/apexfetch.svg"
cp "$SCRIPT_DIR/apexfetch.svg" "$APP_DIR/usr/share/icons/hicolor/scalable/apps/apexfetch.svg"
cp "$SCRIPT_DIR/apexfetch.svg" "$APP_DIR/.DirIcon"

# 5. Create AppRun launcher
cat << 'EOF' > "$APP_DIR/AppRun"
#!/bin/sh
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"

# Identify binary
if [ -x "${HERE}/usr/bin/apexfetch" ]; then
    BIN="${HERE}/usr/bin/apexfetch"
else
    BIN="python3 ${HERE}/usr/bin/apexfetch.py"
fi

# Case 1: Active terminal session (TTY) or CLI arguments passed (e.g. --json) -> run directly
if [ -t 1 ] || [ $# -gt 0 ]; then
    exec $BIN "$@"
fi

# Case 2: Double-click from graphical file manager (Nautilus, Dolphin, Thunar, etc.)
if [ -n "$DISPLAY" ] || [ -n "$WAYLAND_DISPLAY" ]; then
    TARGET_CMD="${APPIMAGE:-$BIN}"
    for TERM_CMD in gnome-terminal ptyxis konsole xfce4-terminal foot alacritty kitty xterm; do
        if command -v "$TERM_CMD" >/dev/null 2>&1; then
            case "$TERM_CMD" in
                gnome-terminal)
                    exec gnome-terminal --wait --title="ApexFetch" --geometry=115x34 -- "$TARGET_CMD" --hold
                    ;;
                ptyxis)
                    exec ptyxis --wait --title="ApexFetch" -- "$TARGET_CMD" --hold
                    ;;
                konsole)
                    exec konsole --title "ApexFetch" -e "$TARGET_CMD" --hold
                    ;;
                xfce4-terminal)
                    exec xfce4-terminal --title="ApexFetch" --geometry=115x34 -e "$TARGET_CMD --hold"
                    ;;
                foot)
                    exec foot -T "ApexFetch" -w 950x640 "$TARGET_CMD" --hold
                    ;;
                alacritty)
                    exec alacritty -T "ApexFetch" -e "$TARGET_CMD" --hold
                    ;;
                kitty)
                    exec kitty -T "ApexFetch" "$TARGET_CMD" --hold
                    ;;
                xterm)
                    exec xterm -title "ApexFetch" -geometry 115x34 -e "$TARGET_CMD" --hold
                    ;;
            esac
        fi
    done

    # Fallback to zenity dialog if no terminal emulator is found
    if command -v zenity >/dev/null 2>&1; then
        $BIN --no-color | zenity --text-info --title="ApexFetch" --width=800 --height=600 --font="Monospace 10" --ok-label="Chiudi"
        exit 0
    fi
fi

# Default fallback
exec $BIN "$@"
EOF
chmod +x "$APP_DIR/AppRun"

# 6. Fetch appimagetool if not available
APPIMAGETOOL="$SCRIPT_DIR/build/appimagetool"
if command -v appimagetool &>/dev/null; then
    APPIMAGETOOL="$(command -v appimagetool)"
else
    if [ ! -f "$APPIMAGETOOL" ]; then
        echo "==> Downloading appimagetool for ${ARCH}..."
        TOOL_URL="https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-${ARCH}.AppImage"
        curl -fsSL -L "$TOOL_URL" -o "$APPIMAGETOOL" || wget -qO "$APPIMAGETOOL" "$TOOL_URL"
        chmod +x "$APPIMAGETOOL"
    fi
fi

# 7. Generate AppImage
OUTPUT_FILE="$OUT_DIR/${APP_NAME}-${ARCH}.AppImage"
echo "==> Generating AppImage: ${OUTPUT_FILE}..."
# Use ARCH env var and --appimage-extract-and-run for nested container/environment compatibility
ARCH="$ARCH" "$APPIMAGETOOL" --appimage-extract-and-run "$APP_DIR" "$OUTPUT_FILE"

echo "==> Build complete!"
echo "==> Output executable: ${OUTPUT_FILE}"
ls -lh "$OUTPUT_FILE"
