# ⚡ Apex-Fetch

<p align="center">
  <img src="apexfetch.svg" alt="Apex-Fetch Logo" width="128" height="128">
</p>

<p align="center">
  <strong>High-Precision System & Hardware Identifier for Linux</strong><br>
  <em>Zero-bloat, instantaneous startup (<0.2s), specialized audio & DAC telemetry, and portable AppImage support.</em>
</p>

<p align="center">
  <a href="https://github.com/Arcun91/appimage-apexfetch/releases"><img src="https://img.shields.io/github/v/release/Arcun91/appimage-apexfetch?style=flat-square&color=00f2fe&label=Release" alt="Latest Release"></a>
  <a href="https://kernel.org"><img src="https://img.shields.io/badge/Platform-Linux-blue?style=flat-square&logo=linux" alt="Platform"></a>
  <a href="https://appimage.org"><img src="https://img.shields.io/badge/Format-AppImage-orange?style=flat-square" alt="AppImage"></a>
  <a href="#"><img src="https://img.shields.io/badge/Dependencies-0%20External-brightgreen?style=flat-square" alt="Zero Dependencies"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License"></a>
</p>

---

## 📸 Preview

```text
                     ./o.                       bob@roberto-82sh
                   ./sssso-                     ────────────────────────────
                 `:osssssss+-                   ◆ OS: EndeavourOS x86_64
               `:+sssssssssso/.                 ◆ Kernel: 7.2.6-arch2-1
             `-/ossssssssssssso/.               ◆ Host: LENOVO IdeaPad 5 Pro 14IAP7 (82SH)
           `-/+sssssssssssssssso+:`             ◆ Uptime: 2 days, 23 hours, 27 mins
         `-:/+sssssssssssssssssso+/.            ◆ Desktop: GNOME 50.5 (Wayland)
       `.://osssssssssssssssssssso++-           ◆ WM: Mutter
      .://+ssssssssssssssssssssssso++:          ◆ CPU: 12th Gen Intel Core i5-1240P (12C/16T) @ 4.40 GHz
    .:///ossssssssssssssssssssssssso++:         ◆ GPU: Intel Iris Xe Graphics
  `:////ssssssssssssssssssssssssssso+++.        ◆ Memory: 8.49 GiB / 15.34 GiB (55.3%) [██████░░░░]
`-////+ssssssssssssssssssssssssssso++++-        ◆ Audio: PipeWire 1.6.8 | Audio interno Stereo analogico
 `..-+oosssssssssssssssssssssssso+++++/`        ◆ Thermal: 42.0°C (Normal)
   ./++++++++++++++++++++++++++++++/:.          ◆ Disk (/): 338.53 GiB / 450.79 GiB (75.1%) [████████░░]
  `:::::::::::::::::::::::::------``            
                                                  ●  ●  ●  ●  ●  ●  ●  ●
                                                  ●  ●  ●  ●  ●  ●  ●  ●
```

---

## 🌟 Why Apex-Fetch?

Most system fetch tools either depend on heavy runtime packages (e.g. `psutil`, complex shell pipelines) or take hundreds of milliseconds to launch. 

**Apex-Fetch** is built from the ground up for **precision, responsiveness, and zero bloat**:

- **⚡ Blazing Fast (< 0.16s):** Communicates directly with the Linux kernel via `/proc` (*procfs*) and `/sys` (*sysfs*). No slow subprocess cascades or external package requirements.
- **🎨 UNIX Retro-Futuristic Aesthetic:** Clean side-by-side terminal layout, vibrant ANSI colors, distro-accurate ASCII artwork, Unicode usage meters, and an 8-color test palette.
- **🎧 Specialized Audio & USB DAC Detection:** Automatically detects active sound servers (**PipeWire**, **PulseAudio**, or **ALSA**) and identifies connected external **USB DACs / Audio Interfaces** (e.g., FiiO, Topping, AudioQuest, Schiit, Focusrite) or dedicated PCIe sound cards.
- **🌡 Thermal Sensors:** Direct millisecond CPU Package / Die temperature readouts with color-coded status thresholds (*Normal*, *Warm*, *Hot*, *Critical*).
- **🖥 Precision Hardware:** Reads motherboard & model directly from DMI/SMBIOS tables, physical/logical CPU core counts, frequency scaling governor limits, and root storage usage.
- **🖱 Dual CLI & Desktop Double-Click Support:** Functions both as an instant terminal command and as a double-clickable desktop AppImage that keeps the terminal window open until you press Enter.
- **📊 Scripting Ready (`--json`):** Full hardware and OS telemetry export in structured, clean JSON.

---

## 🚀 Quick Start

### 🐧 Linux: Standalone AppImage (Recommended)

Download the latest standalone executable from [Releases](https://github.com/Arcun91/appimage-apexfetch/releases):

```bash
# Make it executable
chmod +x ApexFetch-x86_64.AppImage

# Run from terminal
./ApexFetch-x86_64.AppImage
```

> **Desktop Double-Click**: You can also double-click `ApexFetch-x86_64.AppImage` directly from your file manager (Nautilus, Dolphin, etc.) or integrate it into your system application grid via `./integrate_desktop.sh`.

---

### 🍏 macOS: Standalone Binary or .app Bundle

Apex-Fetch natively supports macOS (Apple Silicon M1/M2/M3/M4 & Intel):

#### 1. CLI Portable Binary
Download `ApexFetch-macOS-<arch>.tar.gz` from [Releases](https://github.com/Arcun91/appimage-apexfetch/releases):

```bash
tar -xzf ApexFetch-macOS-*.tar.gz
chmod +x apexfetch
./apexfetch

# (Optional) Install system-wide
sudo mv apexfetch /usr/local/bin/
```

#### 2. Clickable macOS Application Bundle
Download `ApexFetch-macOS.app.zip` from [Releases](https://github.com/Arcun91/appimage-apexfetch/releases):
- Unzip and move `ApexFetch.app` to your `/Applications` folder.
- Double-click `ApexFetch.app` in Finder or launch it from Spotlight to open an instant terminal card.

---

### 🐍 Run Directly with Python (Any Platform)

Apex-Fetch has **zero third-party dependencies**—it runs on any standard Python 3.8+ installation on Linux or macOS:

```bash
git clone https://github.com/Arcun91/appimage-apexfetch.git
cd appimage-apexfetch
./apexfetch.py
```

---

## 💻 CLI Options & Usage

```text
Usage: apexfetch [OPTIONS]

Options:
  -h, --help        Show help message and exit
  --json            Output complete hardware telemetry as formatted JSON
  --no-logo         Print hardware specs only without ASCII art
  --compact         Print in vertical stacked mode (useful for narrow terminals)
  --hold            Keep terminal window open until Enter is pressed
  --no-color        Disable ANSI color sequences (respects NO_COLOR env)
  --distro DISTRO   Manually override distro logo (e.g. arch, debian, fedora, ubuntu)
  -v, --version     Show version number and exit
```

### JSON Export for Scripting

```bash
./apexfetch.py --json
```

<details>
<summary>Click to view sample JSON payload</summary>

```json
{
  "os": {
    "name": "EndeavourOS",
    "id": "endeavouros",
    "kernel": "7.2.6-arch2-1",
    "arch": "x86_64",
    "full_distro": "EndeavourOS x86_64"
  },
  "host": {
    "vendor": "LENOVO",
    "model": "LENOVO IdeaPad 5 Pro 14IAP7 (82SH)",
    "uptime_seconds": 257270.25,
    "uptime_formatted": "2 days, 23 hours, 27 mins"
  },
  "session": {
    "de": "GNOME 50.5",
    "wm": "Mutter",
    "display_server": "Wayland",
    "user": "bob",
    "hostname": "roberto-82sh"
  },
  "cpu": {
    "model": "12th Gen Intel Core i5-1240P",
    "cores_logical": 16,
    "cores_physical": 12,
    "max_freq_ghz": 4.4,
    "formatted": "12th Gen Intel Core i5-1240P (12C/16T) @ 4.40 GHz"
  },
  "gpus": [
    {
      "vendor": "Intel",
      "device": "Iris Xe Graphics",
      "name": "Intel Iris Xe Graphics"
    }
  ],
  "memory": {
    "total_gib": 15.34,
    "used_gib": 8.5,
    "percent": 55.4
  },
  "audio": {
    "server": "PipeWire 1.6.8",
    "active_sink": "Analog Stereo",
    "usb_dacs": []
  },
  "thermal": {
    "cpu_temp_c": 38.0,
    "source": "hwmon/coretemp",
    "status": "Normal"
  },
  "storage": {
    "mount": "/",
    "total_gib": 450.79,
    "used_gib": 338.53,
    "free_gib": 112.26,
    "percent": 75.1
  }
}
```
</details>

---

## ⚡ Performance Benchmark

Apex-Fetch bypasses heavy external shell forks wherever possible by querying Linux virtual kernel filesystems directly:

| Query Metric | Mechanism | Execution Time |
|---|---|---|
| **OS & Distro** | Direct parse of `/etc/os-release` | `~0.15 ms` |
| **Host & Motherboard** | Direct sysfs read `/sys/class/dmi/id/` | `~0.22 ms` |
| **Uptime & Memory** | Procfs read `/proc/uptime` & `/proc/meminfo` | `~0.18 ms` |
| **CPU Telemetry & Temp** | `/proc/cpuinfo` + sysfs `/sys/class/hwmon` | `~0.60 ms` |
| **Root Disk Storage** | POSIX `statvfs('/')` syscall | `~0.01 ms` |
| **GPU Model** | Single optimized `lspci -mm` query | `~70.0 ms` |
| **Total Runtime** | **Full collection + terminal layout render** | **< 0.16 seconds** |

---

## 🛠 Building the AppImage Locally

To build a standalone `.AppImage` binary from source:

```bash
chmod +x build_appimage.sh
./build_appimage.sh
```

The script automatically:
1. Compiles a standalone single-file binary with PyInstaller.
2. Structures the `AppDir` with desktop metadata and scalable vector icons.
3. Packages the final artifact into `dist/ApexFetch-x86_64.AppImage`.

---

## 🐧 Supported Distro Logos

Apex-Fetch includes built-in ASCII art logos with official color palettes for:

- **Arch Linux**
- **EndeavourOS**
- **Debian**
- **Ubuntu**
- **Fedora**
- **Linux Mint**
- **Manjaro**
- **openSUSE** (Tumbleweed / Leap)
- **Pop!_OS**
- **NixOS**
- **Gentoo**
- **Alpine Linux**
- **Void Linux**
- **RHEL / CentOS / Alma / Rocky**
- *Generic Linux / Apex Crest Fallback*

*(You can test any logo using the `--distro <name>` flag).*

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
