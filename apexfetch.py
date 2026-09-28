#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apex-Fetch: High-Precision System & Hardware Identifier for Linux
Specialized, zero-bloat CLI/TUI fetch tool with instant startup (< 0.5s).
"""

import argparse
import glob
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

VERSION = "1.0.0"

# ==============================================================================
# ANSI Color Palette & Terminal Styling
# ==============================================================================
class Colors:
    """Terminal styling and ANSI 256/16 colors."""
    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def _code(self, code: str) -> str:
        return f"\033[{code}m" if self.enabled else ""

    @property
    def reset(self) -> str: return self._code("0")
    @property
    def bold(self) -> str: return self._code("1")
    @property
    def dim(self) -> str: return self._code("2")
    @property
    def italic(self) -> str: return self._code("3")
    @property
    def underline(self) -> str: return self._code("4")

    # Standard colors
    @property
    def black(self) -> str: return self._code("30")
    @property
    def red(self) -> str: return self._code("31")
    @property
    def green(self) -> str: return self._code("32")
    @property
    def yellow(self) -> str: return self._code("33")
    @property
    def blue(self) -> str: return self._code("34")
    @property
    def magenta(self) -> str: return self._code("35")
    @property
    def cyan(self) -> str: return self._code("36")
    @property
    def white(self) -> str: return self._code("37")

    # Bright / Neon retro-futuristic shades
    @property
    def bright_red(self) -> str: return self._code("91")
    @property
    def bright_green(self) -> str: return self._code("92")
    @property
    def bright_yellow(self) -> str: return self._code("93")
    @property
    def bright_blue(self) -> str: return self._code("94")
    @property
    def bright_magenta(self) -> str: return self._code("95")
    @property
    def bright_cyan(self) -> str: return self._code("96")
    @property
    def bright_white(self) -> str: return self._code("97")

    # High fidelity 256 colors
    @property
    def apex_cyan(self) -> str: return self._code("38;5;81")
    @property
    def apex_neon_green(self) -> str: return self._code("38;5;120")
    @property
    def apex_purple(self) -> str: return self._code("38;5;141")
    @property
    def apex_pink(self) -> str: return self._code("38;5;205")
    @property
    def apex_coral(self) -> str: return self._code("38;5;203")
    @property
    def apex_amber(self) -> str: return self._code("38;5;215")
    @property
    def apex_gray(self) -> str: return self._code("38;5;244")
    @property
    def apex_dark_gray(self) -> str: return self._code("38;5;238")


ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*[mK]")

def strip_ansi(text: str) -> str:
    """Strip ANSI escape sequences for proper column width alignment."""
    return ANSI_ESCAPE_PATTERN.sub("", text)

def visible_length(text: str) -> int:
    """Return visible character count disregarding ANSI escape codes."""
    return len(strip_ansi(text))


# ==============================================================================
# Precision System & Hardware Data Collector
# ==============================================================================
class SystemCollector:
    """
    Direct sysfs / procfs / stdlib system collector.
    Avoids slow external forks whenever possible for sub-millisecond data retrieval.
    """

    @staticmethod
    def get_os_release() -> Dict[str, str]:
        """Parse /etc/os-release or /usr/lib/os-release."""
        info = {}
        for path in ("/etc/os-release", "/usr/lib/os-release"):
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8", errors="replace") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#") and "=" in line:
                                k, v = line.split("=", 1)
                                info[k.strip()] = v.strip().strip('"').strip("'")
                    if info:
                        break
                except Exception:
                    pass
        return info

    @staticmethod
    def get_os_info() -> Dict[str, Any]:
        """Retrieve OS name, kernel version, and architecture."""
        os_release = SystemCollector.get_os_release()
        distro_name = os_release.get("PRETTY_NAME") or os_release.get("NAME") or "Linux"
        distro_id = os_release.get("ID", "linux").lower()
        distro_version = os_release.get("VERSION_ID", "")
        kernel_release = platform.release()
        arch = platform.machine()

        return {
            "name": distro_name,
            "id": distro_id,
            "version": distro_version,
            "kernel": kernel_release,
            "arch": arch,
            "full_distro": f"{distro_name} {arch}".strip()
        }

    @staticmethod
    def get_host_info() -> Dict[str, Any]:
        """Read motherboard and model info from DMI tables, with ARM/Pi fallback."""
        def read_dmi(name: str) -> str:
            path = f"/sys/class/dmi/id/{name}"
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8", errors="replace") as f:
                        val = f.read().strip()
                        if val.lower() not in (
                            "none", "to be filled by o.e.m.", "default string",
                            "type2 - board vendor name1", "system product name", "unknown"
                        ):
                            return val
                except Exception:
                    pass
            return ""

        vendor = read_dmi("sys_vendor")
        prod_name = read_dmi("product_name")
        prod_version = read_dmi("product_version")
        prod_family = read_dmi("product_family")
        board_name = read_dmi("board_name")

        # Fallback for ARM (Raspberry Pi, etc.)
        if not prod_name and os.path.exists("/proc/device-tree/model"):
            try:
                with open("/proc/device-tree/model", "r", encoding="utf-8", errors="replace") as f:
                    prod_name = f.read().strip().replace("\x00", "")
            except Exception:
                pass

        # Build clean model string
        parts = []
        if vendor:
            parts.append(vendor)
        
        # Determine best descriptive model
        main_model = prod_version if prod_version and prod_version != prod_name else prod_name
        if not main_model:
            main_model = prod_family or board_name or "Standard Linux PC"

        parts.append(main_model)
        if prod_name and prod_name != main_model:
            parts.append(f"({prod_name})")

        host_model = " ".join(parts).strip()

        # Uptime
        uptime_seconds = 0.0
        if os.path.exists("/proc/uptime"):
            try:
                with open("/proc/uptime", "r", encoding="utf-8") as f:
                    uptime_seconds = float(f.readline().split()[0])
            except Exception:
                pass

        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)

        up_parts = []
        if days > 0:
            up_parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours > 0:
            up_parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        up_parts.append(f"{minutes} min{'s' if minutes != 1 else ''}")
        uptime_formatted = ", ".join(up_parts)

        return {
            "vendor": vendor,
            "product": prod_name,
            "version": prod_version,
            "board": board_name,
            "model": host_model,
            "uptime_seconds": uptime_seconds,
            "uptime_formatted": uptime_formatted
        }

    @staticmethod
    def get_session_info() -> Dict[str, Any]:
        """Detect Desktop Environment, Window Manager, and Display Server."""
        de_name = os.environ.get("XDG_CURRENT_DESKTOP") or os.environ.get("DESKTOP_SESSION") or ""
        display_type = os.environ.get("XDG_SESSION_TYPE", "")

        # Fallback display detection
        if not display_type or display_type == "unspecified":
            if os.environ.get("WAYLAND_DISPLAY"):
                display_type = "wayland"
            elif os.environ.get("DISPLAY"):
                display_type = "x11"
            else:
                display_type = "tty"

        # Refine DE & WM
        wm_name = "Unknown"
        de_version = ""

        # Common Window Managers / Compositors check
        is_wayland = display_type.lower() == "wayland"
        
        # Check specific DEs
        if "GNOME" in de_name.upper():
            wm_name = "Mutter"
            try:
                p = subprocess.run(["gnome-shell", "--version"], capture_output=True, text=True, timeout=0.2)
                if p.returncode == 0:
                    m = re.search(r"(\d+(\.\d+)*)", p.stdout)
                    if m:
                        de_version = m.group(1)
            except Exception:
                pass
            de_display = f"GNOME {de_version}".strip()
        elif "KDE" in de_name.upper() or "PLASMA" in de_name.upper():
            wm_name = "KWin"
            try:
                p = subprocess.run(["plasmashell", "--version"], capture_output=True, text=True, timeout=0.2)
                if p.returncode == 0:
                    m = re.search(r"(\d+(\.\d+)*)", p.stdout)
                    if m:
                        de_version = m.group(1)
            except Exception:
                pass
            de_display = f"KDE Plasma {de_version}".strip()
        elif "HYPRLAND" in de_name.upper() or os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
            de_display = "Hyprland"
            wm_name = "Hyprland"
        elif "SWAY" in de_name.upper() or os.environ.get("SWAYSOCK"):
            de_display = "Sway"
            wm_name = "Sway"
        elif "XFCE" in de_name.upper():
            de_display = "XFCE"
            wm_name = "Xfwm4"
        elif "I3" in de_name.upper():
            de_display = "i3"
            wm_name = "i3"
        elif "CINNAMON" in de_name.upper():
            de_display = "Cinnamon"
            wm_name = "Muffin"
        elif "MATE" in de_name.upper():
            de_display = "MATE"
            wm_name = "Marco"
        else:
            de_display = de_name if de_name else "Headless / CLI"
            wm_name = de_name if de_name else "None"

        display_server_formatted = "Wayland" if is_wayland else ("X11" if display_type.lower() == "x11" else display_type.capitalize())

        return {
            "de": de_display,
            "wm": wm_name,
            "display_server": display_server_formatted,
            "session_type": display_type,
            "user": os.environ.get("USER", "user"),
            "hostname": platform.node()
        }

    @staticmethod
    def get_cpu_info() -> Dict[str, Any]:
        """Extract CPU model name, core counts, and frequency."""
        model = "Unknown Processor"
        cores_logical = os.cpu_count() or 1
        cores_physical = None
        max_ghz = 0.0

        # /proc/cpuinfo
        if os.path.exists("/proc/cpuinfo"):
            try:
                physical_ids = set()
                core_ids = set()
                with open("/proc/cpuinfo", "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("model name") and model == "Unknown Processor":
                            model = line.split(":", 1)[1].strip()
                        elif line.startswith("physical id"):
                            physical_ids.add(line.split(":", 1)[1].strip())
                        elif line.startswith("core id"):
                            core_ids.add(line.split(":", 1)[1].strip())
                if physical_ids and core_ids:
                    cores_physical = len(physical_ids) * len(core_ids)
            except Exception:
                pass

        # Clean model name
        clean_model = model
        clean_model = re.sub(r"\((R|TM|tm|r)\)", "", clean_model)
        clean_model = re.sub(r"\s+", " ", clean_model).strip()

        # Frequency detection
        for p in (
            "/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq",
            "/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq"
        ):
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        val_khz = int(f.read().strip())
                        max_ghz = round(val_khz / 1_000_000.0, 2)
                        if max_ghz > 0:
                            break
                except Exception:
                    pass

        # Formatting
        core_repr = f"({cores_logical})"
        if cores_physical and cores_physical != cores_logical:
            core_repr = f"({cores_physical}C/{cores_logical}T)"
        
        freq_repr = f" @ {max_ghz:.2f} GHz" if max_ghz > 0 else ""
        formatted = f"{clean_model} {core_repr}{freq_repr}".strip()

        return {
            "model": clean_model,
            "cores_logical": cores_logical,
            "cores_physical": cores_physical,
            "max_freq_ghz": max_ghz,
            "formatted": formatted
        }

    @staticmethod
    def get_gpu_info() -> List[Dict[str, str]]:
        """Identify GPU adapters via lspci with vendor & model cleanup."""
        gpus = []
        try:
            p = subprocess.run(
                ["lspci", "-mm"],
                capture_output=True, text=True, timeout=0.5
            )
            if p.returncode == 0:
                for line in p.stdout.splitlines():
                    # Format: Slot "Class" "Vendor" "Device" -rRev ...
                    m = re.findall(r'"([^"]*)"', line)
                    if len(m) >= 3:
                        pci_class, vendor, device = m[0], m[1], m[2]
                        if any(c in pci_class for c in ("VGA", "3D", "Display")):
                            # Clean vendor
                            clean_vendor = vendor
                            if "Intel" in vendor: clean_vendor = "Intel"
                            elif "NVIDIA" in vendor: clean_vendor = "NVIDIA"
                            elif "AMD" in vendor or "Advanced Micro Devices" in vendor: clean_vendor = "AMD"

                            # Clean device name
                            clean_device = device
                            bracket_match = re.search(r"\[(.*?)\]", device)
                            if bracket_match:
                                clean_device = bracket_match.group(1)

                            # Remove redundant vendor prefixes
                            if clean_device.startswith(clean_vendor):
                                full_gpu = clean_device
                            else:
                                full_gpu = f"{clean_vendor} {clean_device}"

                            gpus.append({
                                "vendor": clean_vendor,
                                "device": clean_device,
                                "name": full_gpu,
                                "class": pci_class
                            })
        except Exception:
            pass

        # Fallback to standard lspci if -mm failed
        if not gpus:
            try:
                p = subprocess.run(["lspci"], capture_output=True, text=True, timeout=0.5)
                if p.returncode == 0:
                    for line in p.stdout.splitlines():
                        if any(x in line for x in ("VGA compatible controller:", "3D controller:", "Display controller:")):
                            desc = line.split("controller:", 1)[1].strip()
                            # Clean up rev
                            desc = re.sub(r"\(rev [0-9a-fA-F]+\)", "", desc).strip()
                            gpus.append({"name": desc})
            except Exception:
                pass

        if not gpus:
            gpus.append({"name": "Integrated / Generic Graphics"})

        return gpus

    @staticmethod
    def get_memory_info() -> Dict[str, Any]:
        """Compute RAM metrics from /proc/meminfo."""
        mem = {}
        if os.path.exists("/proc/meminfo"):
            try:
                with open("/proc/meminfo", "r", encoding="utf-8") as f:
                    for line in f:
                        parts = line.split(":", 1)
                        if len(parts) == 2:
                            val = parts[1].strip().split()[0]
                            mem[parts[0].strip()] = int(val) * 1024  # to bytes
            except Exception:
                pass

        total_bytes = mem.get("MemTotal", 0)
        avail_bytes = mem.get("MemAvailable", mem.get("MemFree", 0) + mem.get("Buffers", 0) + mem.get("Cached", 0))
        used_bytes = max(0, total_bytes - avail_bytes)

        pct = (used_bytes / total_bytes * 100) if total_bytes > 0 else 0.0

        def to_gib(b: int) -> float:
            return round(b / (1024 ** 3), 2)

        return {
            "total_bytes": total_bytes,
            "used_bytes": used_bytes,
            "free_bytes": avail_bytes,
            "total_gib": to_gib(total_bytes),
            "used_gib": to_gib(used_bytes),
            "free_gib": to_gib(avail_bytes),
            "percent": round(pct, 1)
        }

    @staticmethod
    def get_audio_info() -> Dict[str, Any]:
        """
        Detect active audio server (PipeWire / PulseAudio / ALSA),
        and identify dedicated sound cards / external USB DACs.
        """
        xdg_runtime = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
        
        # Audio Server Detection
        server = "ALSA (Kernel direct)"
        pw_socket = os.path.join(xdg_runtime, "pipewire-0")
        pulse_socket = os.path.join(xdg_runtime, "pulse", "native")

        if os.path.exists(pw_socket):
            # Probe pipewire version
            server = "PipeWire"
            try:
                p = subprocess.run(["pipewire", "--version"], capture_output=True, text=True, timeout=0.2)
                if p.returncode == 0:
                    m = re.search(r"libpipewire\s+([0-9.]+)", p.stdout)
                    if m:
                        server = f"PipeWire {m.group(1)}"
            except Exception:
                pass
        elif os.path.exists(pulse_socket):
            server = "PulseAudio"

        # Dedicated cards and USB DAC detection from /proc/asound/cards
        sound_cards = []
        usb_dacs = []

        if os.path.exists("/proc/asound/cards"):
            try:
                with open("/proc/asound/cards", "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.rstrip()
                        m = re.match(r"^\s*(\d+)\s+\[([^\]]+)\]:\s*(.*)$", line)
                        if m:
                            idx, tag, rest = m.groups()
                            parts = [p.strip() for p in rest.split(" - ", 1)]
                            driver = parts[0]
                            name = parts[1] if len(parts) > 1 else driver
                            
                            is_usb = "usb" in driver.lower() or "usb" in name.lower() or "dac" in name.lower()
                            card_item = {
                                "index": idx,
                                "tag": tag.strip(),
                                "driver": driver,
                                "name": name,
                                "is_usb_dac": is_usb
                            }
                            sound_cards.append(card_item)
                            if is_usb:
                                usb_dacs.append(name)
            except Exception:
                pass

        # Active Output Sink
        active_sink = ""
        try:
            p = subprocess.run(["pactl", "list", "sinks"], capture_output=True, text=True, timeout=0.3)
            if p.returncode == 0:
                for line in p.stdout.splitlines():
                    if "Description:" in line:
                        active_sink = line.split(":", 1)[1].strip()
                        break
        except Exception:
            pass

        if not active_sink and sound_cards:
            # Fallback to first card name
            active_sink = sound_cards[0]["name"]
        elif not active_sink:
            active_sink = "Generic Audio Device"

        return {
            "server": server,
            "active_sink": active_sink,
            "usb_dacs": usb_dacs,
            "cards": sound_cards
        }

    @staticmethod
    def get_thermal_info() -> Dict[str, Any]:
        """Read CPU temperature directly from sysfs hwmon or sensors fallback."""
        cpu_temp = None
        source = None

        # 1. Direct sysfs hwmon scan (< 1ms)
        for h in glob.glob("/sys/class/hwmon/hwmon*"):
            try:
                name_file = os.path.join(h, "name")
                if os.path.exists(name_file):
                    with open(name_file, "r", encoding="utf-8") as f:
                        sensor_name = f.read().strip()
                    if sensor_name in ("coretemp", "k10temp", "zenpower", "cpu_thermal", "acpitz"):
                        # Read temp1_input or package input
                        tfile = os.path.join(h, "temp1_input")
                        if os.path.exists(tfile):
                            with open(tfile, "r", encoding="utf-8") as f:
                                cpu_temp = round(int(f.read().strip()) / 1000.0, 1)
                                source = f"hwmon/{sensor_name}"
                                break
            except Exception:
                pass

        # 2. sensors command fallback
        if cpu_temp is None:
            try:
                p = subprocess.run(["sensors"], capture_output=True, text=True, timeout=0.3)
                if p.returncode == 0:
                    for line in p.stdout.splitlines():
                        if any(k in line for k in ("Package id 0:", "Tctl:", "Tdie:", "CPU Temperature:", "temp1:")):
                            m = re.search(r"\+([0-9.]+)°C", line)
                            if m:
                                cpu_temp = float(m.group(1))
                                source = "sensors"
                                break
            except Exception:
                pass

        # Status categorization
        status = "Normal"
        if cpu_temp is not None:
            if cpu_temp >= 85:
                status = "Critical"
            elif cpu_temp >= 75:
                status = "Hot"
            elif cpu_temp >= 55:
                status = "Warm"

        return {
            "cpu_temp_c": cpu_temp,
            "source": source,
            "status": status
        }

    @staticmethod
    def get_storage_info() -> Dict[str, Any]:
        """Query primary root partition statistics via os.statvfs."""
        try:
            st = os.statvfs("/")
            total_bytes = st.f_blocks * st.f_frsize
            free_bytes = st.f_bavail * st.f_frsize
            used_bytes = max(0, total_bytes - free_bytes)
            pct = (used_bytes / total_bytes * 100) if total_bytes > 0 else 0.0

            def to_gib(b: int) -> float:
                return round(b / (1024 ** 3), 2)

            return {
                "mount": "/",
                "total_bytes": total_bytes,
                "used_bytes": used_bytes,
                "free_bytes": free_bytes,
                "total_gib": to_gib(total_bytes),
                "used_gib": to_gib(used_bytes),
                "free_gib": to_gib(free_bytes),
                "percent": round(pct, 1)
            }
        except Exception:
            return {
                "mount": "/",
                "total_bytes": 0,
                "used_bytes": 0,
                "free_bytes": 0,
                "total_gib": 0.0,
                "used_gib": 0.0,
                "free_gib": 0.0,
                "percent": 0.0
            }


# ==============================================================================
# Distribution ASCII Art Library
# ==============================================================================
class DistroLogo:
    """Manages stylized ASCII logos and palette mapping."""
    
    @staticmethod
    def get_logo(distro_id: str, c: Colors) -> List[str]:
        d = distro_id.lower()
        r = c.reset

        # EndeavourOS
        if "endeavour" in d:
            c1, c2, c3 = c.apex_coral, c.apex_purple, c.apex_cyan
            raw = [
                (c1, "                     ./o.                   "),
                (c1, "                   ./sssso-                 "),
                (c1, "                 `:osssssss+-               "),
                (c1, "               `:+sssssssssso/.             "),
                (c2, "             `-/ossssssssssssso/.           "),
                (c2, "           `-/+sssssssssssssssso+:`         "),
                (c2, "         `-:/+sssssssssssssssssso+/.        "),
                (c2, "       `.://osssssssssssssssssssso++-       "),
                (c2, "      .://+ssssssssssssssssssssssso++:      "),
                (c2, "    .:///ossssssssssssssssssssssssso++:     "),
                (c3, "  `:////ssssssssssssssssssssssssssso+++.    "),
                (c3, "`-////+ssssssssssssssssssssssssssso++++-    "),
                (c3, " `..-+oosssssssssssssssssssssssso+++++/`    "),
                (c3, "   ./++++++++++++++++++++++++++++++/:.      "),
                (c3, "  `:::::::::::::::::::::::::------``        "),
            ]
            return [f"{col}{line}{r}" for col, line in raw]

        # Arch Linux
        if "arch" in d:
            c1, c2 = c.apex_cyan, c.bright_cyan
            raw = [
                (c1, "                  -`                  "),
                (c1, "                 .o+`                 "),
                (c1, "                `ooo/                 "),
                (c1, "               `+oooo:                "),
                (c1, "              `+oooooo:               "),
                (c1, "              -+oooooo+:              "),
                (c1, "            `/:-:++oooo+:             "),
                (c2, "           `/++++/+++++++:            "),
                (c2, "          `/++++++++++++++:           "),
                (c2, "         `/+++ooooooooooooo/`         "),
                (c2, "        ./ooosssso++osssssso+`        "),
                (c2, "       .oossssso-````/ossssss+`       "),
                (c1, "      -osssssso.      :ssssssso.      "),
                (c1, "     :osssssss/        osssso+++.     "),
                (c1, "    /ossssssss/        +ssssooo/-     "),
                (c1, "  `/ossssso+/:-        -:/+osssso+-   "),
                (c1, " `+sso+:-`                 `.-/+oso:  "),
                (c1, "`++:.                           `-/+/ "),
            ]
            return [f"{col}{line}{r}" for col, line in raw]

        # Ubuntu
        if "ubuntu" in d:
            c1, c2 = c.apex_coral, c.apex_amber
            raw = [
                (c1, "            .-/+oossssoo+/-.            "),
                (c1, "        `:+ssssssssssssssssss+:         "),
                (c1, "      -+ssssssssssssssssssyyssss+-      "),
                (c1, "    .ossssssssssssssssssdMMMNysssso.    "),
                (c2, "   /ssssssssssshdmmNNmmyNMMMMhssssss/   "),
                (c2, "  +ssssssssshmydMMMMMMMNddddyssssssss+  "),
                (c2, " /sssssssshNMMMyhhyyyyhmNMMMNhssssssss/ "),
                (c2, ".ssssssssdMMMNhsssssssssshNMMMdssssssss."),
                (c2, "+sssshhhyNMMNyssssssssssssyNMMMysssssss+"),
                (c1, "ossyNMMMNyMMhsssssssssssssshmmmhssssssso"),
                (c1, "ossyNMMMNyMMhsssssssssssssshmmmhssssssso"),
                (c1, "+sssshhhyNMMNyssssssssssssyNMMMysssssss+"),
                (c1, ".ssssssssdMMMNhsssssssssshNMMMdssssssss."),
                (c1, " /sssssssshNMMMyhhyyyyhdNMMMNhssssssss/ "),
                (c1, "  +sssssssssdmydMMMMMMMMddddyssssssss+  "),
                (c1, "   /ssssssssssshdmNNNNmyNMMMMhssssss/   "),
                (c1, "    .ossssssssssssssssssdMMMNysssso.    "),
                (c1, "      -+sssssssssssssssssyyyssss+-      "),
            ]
            return [f"{col}{line}{r}" for col, line in raw]

        # Debian
        if "debian" in d:
            c1 = c.apex_coral
            raw = [
                "       _,met$$$$$gg.       ",
                "    ,g$$$$$$$$$$$$$$$P.    ",
                "  ,g$$P\"\"       \"\"\"Y$$.\".  ",
                " ,$$P'              `$$$.  ",
                "',$$P       ,ggs.     `$$b:",
                "`d$$'     ,$P\"'   .    $$$ ",
                " $$P      d$'     ,    $$$P",
                " $$:      $$.   -    ,d$$' ",
                " $$;      Y$b._   _,d$P'   ",
                " Y$$.    `.`\"Y$$$$P\"'      ",
                " `$$b      \"-.__           ",
                "  `Y$$b                    ",
                "   `Y$$.                   ",
                "     `$$b.                 ",
                "       `Y$$b.              ",
                "         `\"Y$b._           ",
                "             `\"\"\"\"         ",
            ]
            return [f"{c1}{line}{r}" for line in raw]

        # Fedora
        if "fedora" in d:
            c1, c2 = c.apex_cyan, c.bright_white
            raw = [
                (c1, "          /:-------------:\\          "),
                (c1, "       :-------------------::        "),
                (c1, "     :-----------/shhOHbmp---:\\      "),
                (c1, "   /-----------omMMMNNNMMD  ---:     "),
                (c1, "  :-----------sMMMMNMNMP.    ---:    "),
                (c1, " :-----------:MMMdP-------    ---\\   "),
                (c2, ",------------:MMMr--------      ---: "),
                (c2, ":------------:MMMo-------       ---: "),
                (c2, ":------------.MMMb-------      ---:  "),
                (c2, " :------------:MMMo--------------/   "),
                (c1, "  \\------------/hMMMb-----------/    "),
                (c1, "   \\-------------:odNMMMDhpp/--:     "),
                (c1, "     :-----------/shhOHbmp---:\\      "),
                (c1, "       :-------------------::        "),
                (c1, "          \\:-------------:/          "),
            ]
            return [f"{col}{line}{r}" for col, line in raw]

        # Linux Mint
        if "mint" in d:
            c1 = c.apex_neon_green
            raw = [
                "   `...-:::::-...`   ",
                "  .-/+oooooooooooo+/-` ",
                " `+ooooo+/::::/oooooo+`",
                " +oooo/`        `/oooo+",
                "+oooo-  `--...`   -oooo+",
                "+oooo` `+ooooo-   `oooo+",
                "+oooo`  :ooooo-   `oooo+",
                "+oooo`  :ooooo-   `oooo+",
                "+oooo`  :ooooo-   `oooo+",
                "+oooo`  :ooooo-   `oooo+",
                "+oooo-  .ooooo-   -oooo+",
                " +oooo/` :oooo- `/oooo+ ",
                " `+ooooo+:---:/oooooo+` ",
                "  .-/+oooooooooooo+/-`  ",
                "   `...-:::::-...`    ",
            ]
            return [f"{c1}{line}{r}" for line in raw]

        # Manjaro
        if "manjaro" in d:
            c1 = c.apex_neon_green
            raw = [
                "██████████████████  ████████",
                "██████████████████  ████████",
                "██████              ████████",
                "██████  ██████████  ████████",
                "██████  ██████████  ████████",
                "██████  ██████████  ████████",
                "██████  ██████████  ████████",
                "██████  ██████████  ████████",
                "██████  ██████████  ████████",
                "██████  ██████████  ████████",
                "██████  ██████████  ████████",
                "██████  ██████████  ████████",
            ]
            return [f"{c1}{line}{r}" for line in raw]

        # openSUSE
        if "suse" in d:
            c1 = c.apex_neon_green
            raw = [
                "           .---.           ",
                "          /     \\          ",
                "     _..-'(      )`-.._    ",
                "    ;      `-..-'      ;   ",
                "    `.                .'   ",
                "      `'-...____...-'`     ",
                "       (  o  )(  o  )      ",
                "        `.__/  \\__.'       ",
                "         /        \\        ",
                "        (  \\___/  )        ",
                "         `-.....-'         ",
            ]
            return [f"{c1}{line}{r}" for line in raw]

        # Pop!_OS
        if "pop" in d:
            c1, c2 = c.apex_cyan, c.apex_amber
            raw = [
                (c1, "             /////////////             "),
                (c1, "         /////////////////////         "),
                (c1, "      ///////*                *//////  "),
                (c1, "    /////*                       *//// "),
                (c1, "   ////*                           *///"),
                (c2, "  ///*      .////////////////.      *//"),
                (c2, "  ///*      .////////////////.      *//"),
                (c2, "  ///*      .////////////////.      *//"),
                (c2, "  ///*      .////////////////.      *//"),
                (c1, "   ////*    .////////////////.     *///"),
                (c1, "    ////*         //////         *//// "),
                (c1, "      ///////*              *//////    "),
                (c2, "         ///////          ///////      "),
                (c2, "             /////////////             "),
            ]
            return [f"{col}{line}{r}" for col, line in raw]

        # NixOS
        if "nix" in d:
            c1, c2 = c.apex_cyan, c.bright_blue
            raw = [
                (c1, "  \\\\  \\\\ //          "),
                (c1, " ==\\\\__\\\\/ //        "),
                (c1, "   //   \\\\//         "),
                (c2, "==//     //==        "),
                (c2, " //\\\\___//           "),
                (c2, "// /\\\\  \\\\==         "),
                (c1, "  // \\\\  \\\\          "),
            ]
            return [f"{col}{line}{r}" for col, line in raw]

        # Generic / Apex Crest Fallback
        c1, c2, c3 = c.apex_cyan, c.apex_purple, c.apex_neon_green
        raw = [
            (c1, "            ▲            "),
            (c1, "           / \\           "),
            (c1, "          /   \\          "),
            (c1, "         /  ▲  \\         "),
            (c2, "        /  / \\  \\        "),
            (c2, "       /  /   \\  \\       "),
            (c2, "      /  /  ▲  \\  \\      "),
            (c2, "     /  /  / \\  \\  \\     "),
            (c3, "    /  /__/   \\__\\  \\    "),
            (c3, "   /_________________\\   "),
            (c3, "   ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼   "),
        ]
        return [f"{col}{line}{r}" for col, line in raw]


# ==============================================================================
# UI Formatting & Layout Engine
# ==============================================================================
class ApexRenderer:
    """Renders retro-futuristic side-by-side terminal card."""

    def __init__(self, colors: Colors):
        self.c = colors

    def make_bar(self, percent: float, width: int = 12) -> str:
        """Render a high-precision unicode usage bar."""
        clamped = max(0.0, min(100.0, percent))
        filled_len = int(round((clamped / 100.0) * width))
        empty_len = width - filled_len
        
        # Color gradient based on utilization
        if clamped >= 90:
            fill_color = self.c.bright_red
        elif clamped >= 75:
            fill_color = self.c.apex_amber
        else:
            fill_color = self.c.apex_neon_green

        bar_filled = f"{fill_color}{'█' * filled_len}{self.c.reset}"
        bar_empty = f"{self.c.apex_dark_gray}{'░' * empty_len}{self.c.reset}"
        return f"{self.c.dim}[{self.c.reset}{bar_filled}{bar_empty}{self.c.dim}]{self.c.reset}"

    def make_color_strip(self) -> str:
        """Neofetch / Fastfetch style 8-color test palette dots."""
        c = self.c
        dots = [
            f"{c.black}●{c.reset}",
            f"{c.red}●{c.reset}",
            f"{c.green}●{c.reset}",
            f"{c.yellow}●{c.reset}",
            f"{c.blue}●{c.reset}",
            f"{c.magenta}●{c.reset}",
            f"{c.cyan}●{c.reset}",
            f"{c.white}●{c.reset}",
        ]
        bright_dots = [
            f"{c.apex_dark_gray}●{c.reset}",
            f"{c.bright_red}●{c.reset}",
            f"{c.bright_green}●{c.reset}",
            f"{c.bright_yellow}●{c.reset}",
            f"{c.bright_blue}●{c.reset}",
            f"{c.bright_magenta}●{c.reset}",
            f"{c.bright_cyan}●{c.reset}",
            f"{c.bright_white}●{c.reset}",
        ]
        return "  " + "  ".join(dots) + "\n  " + "  ".join(bright_dots)

    def build_info_lines(self, data: Dict[str, Any]) -> List[str]:
        """Construct styled, labeled lines for the right-hand specs column."""
        c = self.c
        lines = []

        # Header: user@hostname
        user = data["session"]["user"]
        host = data["session"]["hostname"]
        header_text = f"{c.bold}{c.apex_cyan}{user}{c.reset}{c.bold}{c.bright_white}@{c.reset}{c.bold}{c.apex_purple}{host}{c.reset}"
        lines.append(header_text)
        
        # Divider line matching length
        plain_len = len(f"{user}@{host}")
        divider = f"{c.dim}{c.apex_dark_gray}{'─' * max(plain_len, 28)}{c.reset}"
        lines.append(divider)

        # Label helper
        def row(icon: str, label: str, value: str) -> str:
            lbl = f"{c.apex_cyan}{icon} {c.bold}{label}:{c.reset}"
            return f"{lbl} {value}"

        # OS / Distro
        os_info = data["os"]
        lines.append(row("◆", "OS", f"{os_info['name']} {os_info['arch']}"))
        lines.append(row("◆", "Kernel", f"{c.bright_white}{os_info['kernel']}{c.reset}"))

        # Host / Uptime
        host_info = data["host"]
        lines.append(row("◆", "Host", f"{host_info['model']}"))
        lines.append(row("◆", "Uptime", f"{c.apex_neon_green}{host_info['uptime_formatted']}{c.reset}"))

        # Desktop / Session
        sess = data["session"]
        lines.append(row("◆", "Desktop", f"{sess['de']} ({c.apex_amber}{sess['display_server']}{c.reset})"))
        if sess["wm"] and sess["wm"] != "Unknown" and sess["wm"] != sess["de"]:
            lines.append(row("◆", "WM", f"{sess['wm']}"))

        # Hardware Core: CPU
        cpu = data["cpu"]
        lines.append(row("◆", "CPU", f"{cpu['formatted']}"))

        # Hardware Core: GPU
        for gpu in data["gpus"]:
            lines.append(row("◆", "GPU", f"{gpu['name']}"))

        # Hardware Core: Memory
        mem = data["memory"]
        mem_bar = self.make_bar(mem["percent"], width=10)
        lines.append(row("◆", "Memory", f"{mem['used_gib']} GiB / {mem['total_gib']} GiB ({mem['percent']}%) {mem_bar}"))

        # Audio Subsystem
        audio = data["audio"]
        audio_val = f"{c.apex_purple}{audio['server']}{c.reset}"
        if audio["usb_dacs"]:
            dac_names = ", ".join(audio["usb_dacs"])
            audio_val += f" | {c.apex_pink}[USB DAC]{c.reset} {dac_names}"
        elif audio["active_sink"]:
            audio_val += f" | {audio['active_sink']}"
        lines.append(row("◆", "Audio", audio_val))

        # Thermal / Sensors
        therm = data["thermal"]
        if therm["cpu_temp_c"] is not None:
            temp_val = therm["cpu_temp_c"]
            if therm["status"] == "Critical":
                temp_str = f"{c.bold}{c.bright_red}{temp_val}°C (Critical){c.reset}"
            elif therm["status"] == "Hot":
                temp_str = f"{c.apex_coral}{temp_val}°C (Hot){c.reset}"
            elif therm["status"] == "Warm":
                temp_str = f"{c.apex_amber}{temp_val}°C (Warm){c.reset}"
            else:
                temp_str = f"{c.apex_neon_green}{temp_val}°C (Normal){c.reset}"
            lines.append(row("◆", "Thermal", temp_str))
        else:
            lines.append(row("◆", "Thermal", f"{c.dim}Sensors N/A{c.reset}"))

        # Storage
        disk = data["storage"]
        disk_bar = self.make_bar(disk["percent"], width=10)
        lines.append(row("◆", "Disk (/)", f"{disk['used_gib']} GiB / {disk['total_gib']} GiB ({disk['percent']}%) {disk_bar}"))

        # Spacing and Color Strip
        lines.append("")
        for strip_line in self.make_color_strip().splitlines():
            lines.append(strip_line)

        return lines

    def render(self, logo_lines: List[str], info_lines: List[str], compact: bool = False, no_logo: bool = False) -> str:
        """Render side-by-side or stacked layout."""
        if no_logo or not logo_lines:
            return "\n".join(info_lines)

        term_width = shutil.get_terminal_size((80, 24)).columns
        logo_width = max(visible_length(l) for l in logo_lines)
        gap = 4

        # If terminal width is too narrow, fall back to compact vertical stack
        if compact or term_width < (logo_width + gap + 40):
            out = []
            out.extend(logo_lines)
            out.append("")
            out.extend(info_lines)
            return "\n".join(out)

        # Side-by-side layout
        total_rows = max(len(logo_lines), len(info_lines))
        out_rows = []

        for i in range(total_rows):
            left = logo_lines[i] if i < len(logo_lines) else ""
            right = info_lines[i] if i < len(info_lines) else ""
            pad = logo_width - visible_length(left) + gap
            out_rows.append(f"{left}{' ' * pad}{right}")

        return "\n".join(out_rows)


# ==============================================================================
# CLI Entrypoint & Controller
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        prog="ApexFetch",
        description="Apex-Fetch: High-Precision System & Hardware Identifier for Linux.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Designed for instant execution (<0.5s) and standalone AppImage deployment."
    )
    parser.add_argument("--json", action="store_true", help="Output full hardware telemetry as raw JSON")
    parser.add_argument("--no-logo", action="store_true", help="Print specs only without ASCII art")
    parser.add_argument("--compact", action="store_true", help="Print in vertical stacked mode")
    parser.add_argument("--hold", action="store_true", help="Keep window open until Enter is pressed (for GUI double-click launches)")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI color formatting")
    parser.add_argument("--distro", type=str, default="", help="Override distribution logo (e.g. arch, debian, fedora)")
    parser.add_argument("--version", "-v", action="version", version=f"ApexFetch {VERSION}")

    args = parser.parse_args()

    # Determine color enablement
    use_colors = not args.no_color and sys.stdout.isatty() and "NO_COLOR" not in os.environ
    colors = Colors(enabled=use_colors)

    # 1. Gather Telemetry (Ultra-fast parallel / direct procfs queries)
    os_info = SystemCollector.get_os_info()
    host_info = SystemCollector.get_host_info()
    session_info = SystemCollector.get_session_info()
    cpu_info = SystemCollector.get_cpu_info()
    gpu_info = SystemCollector.get_gpu_info()
    memory_info = SystemCollector.get_memory_info()
    audio_info = SystemCollector.get_audio_info()
    thermal_info = SystemCollector.get_thermal_info()
    storage_info = SystemCollector.get_storage_info()

    telemetry = {
        "os": os_info,
        "host": host_info,
        "session": session_info,
        "cpu": cpu_info,
        "gpus": gpu_info,
        "memory": memory_info,
        "audio": audio_info,
        "thermal": thermal_info,
        "storage": storage_info
    }

    # 2. Handle JSON Export
    if args.json:
        print(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    # 3. Render Visual UI
    distro_key = args.distro if args.distro else os_info["id"]
    logo_lines = DistroLogo.get_logo(distro_key, colors)
    
    renderer = ApexRenderer(colors)
    info_lines = renderer.build_info_lines(telemetry)
    
    rendered_output = renderer.render(
        logo_lines=logo_lines,
        info_lines=info_lines,
        compact=args.compact,
        no_logo=args.no_logo
    )

    print()
    print(rendered_output)
    print()

    # 4. Hold terminal window if requested (for desktop/GUI launches)
    if args.hold:
        try:
            prompt_str = f"{colors.dim}{colors.apex_cyan}  [Premere Invio per uscire...]{colors.reset} " if colors.enabled else "  [Premere Invio per uscire...] "
            input(prompt_str)
        except (KeyboardInterrupt, EOFError):
            pass


if __name__ == "__main__":
    main()
