from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Optional, Tuple, List

# -------------------------------------------------
# Windows MessageBox helper
# -------------------------------------------------
def msg(title: str, text: str, error=False):
    try:
        import ctypes
        flags = 0x10 if error else 0x40
        ctypes.windll.user32.MessageBoxW(None, text, title, flags)
    except Exception:
        print(f"{title}: {text}")

# -------------------------------------------------
# Simple INI reader (section -> key -> value)
# -------------------------------------------------
def read_ini(path: Path) -> Dict[str, Dict[str, str]]:
    data = {}
    section = None

    for raw in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith(";") or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            data.setdefault(section, {})
            continue
        if section and "=" in line:
            k, v = line.split("=", 1)
            data[section][k.strip()] = v.strip()

    return data

# -------------------------------------------------
# Line-preserving patcher for callsign.ini
# -------------------------------------------------
class IniPatcher:
    def __init__(self, path: Path):
        self.path = path
        self.lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()

    def set_section(self, section: str, values: Dict[str, str]):
        sec_start = None
        sec_end = None

        for i, line in enumerate(self.lines):
            if line.strip() == f"[{section}]":
                sec_start = i
                continue
            if sec_start is not None and line.strip().startswith("[") and line.strip().endswith("]"):
                sec_end = i
                break

        if sec_start is None:
            self.lines.append("")
            self.lines.append(f"[{section}]")
            for k, v in values.items():
                self.lines.append(f"{k}={v}")
            return

        if sec_end is None:
            sec_end = len(self.lines)

        existing = {}
        for i in range(sec_start + 1, sec_end):
            if "=" in self.lines[i]:
                k = self.lines[i].split("=", 1)[0].strip()
                existing[k] = i

        for k, v in values.items():
            if k in existing:
                self.lines[existing[k]] = f"{k}={v}"
            else:
                self.lines.insert(sec_end, f"{k}={v}")
                sec_end += 1

    def write(self):
        self.path.write_text("\n".join(self.lines) + "\n", encoding="utf-8")

# -------------------------------------------------
# Read config.ini
# -------------------------------------------------
def read_config(path: Path):
    cfg = read_ini(path)
    try:
        callsign = Path(cfg["Paths"]["callsign_ini_path"]).expanduser()
    except Exception:
        raise RuntimeError("callsign_ini_path fehlt in config.ini")

    suffix = cfg.get("Backup", {}).get("suffix", "_bkp")
    return callsign, suffix

# -------------------------------------------------
# Main
# -------------------------------------------------
def main(argv):
    exe_dir = Path(sys.argv[0]).resolve().parent
    cfg_path = exe_dir / "config.ini"

    if not cfg_path.exists():
        msg("INI Merge", f"config.ini fehlt:\n{cfg_path}", True)
        return 2

    if len(argv) < 2:
        msg("INI Merge", "mission.ini per Drag & Drop auf die EXE ziehen")
        return 1

    mission_ini = Path(argv[1]).resolve()
    if not mission_ini.exists():
        msg("INI Merge", f"mission.ini nicht gefunden:\n{mission_ini}", True)
        return 2

    try:
        callsign_ini, bkp_suffix = read_config(cfg_path)
    except Exception as e:
        msg("INI Merge", str(e), True)
        return 2

    if not callsign_ini.exists():
        msg("INI Merge", f"callsign.ini nicht gefunden:\n{callsign_ini}", True)
        return 2

    mission_data = read_ini(mission_ini)
    stpt = mission_data.get("STPT")

    if not stpt:
        msg("INI Merge", "mission.ini enthält keine [STPT] Section", True)
        return 2

    # Backup
    backup = callsign_ini.with_name(callsign_ini.name + bkp_suffix)
    backup.write_bytes(callsign_ini.read_bytes())

    # Patch
    patcher = IniPatcher(callsign_ini)
    patcher.set_section("STPT", stpt)
    patcher.write()

    msg(
        "INI Merge",
        f"Fertig.\n\n"
        f"mission.ini:\n{mission_ini}\n\n"
        f"callsign.ini:\n{callsign_ini}\n"
        f"Backup:\n{backup}\n"
        f"STPT Einträge: {len(stpt)}"
    )
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
