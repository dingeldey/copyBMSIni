from __future__ import annotations

import os
import sys
import shutil
import stat
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from datetime import datetime


# -------------------------------------------------
# Windows MessageBox helper (OK + Yes/No + Yes/No/Cancel)
# -------------------------------------------------
def msg(title: str, text: str, error: bool = False):
    try:
        import ctypes
        flags = 0x10 if error else 0x40  # MB_ICONERROR / MB_ICONINFORMATION
        ctypes.windll.user32.MessageBoxW(None, text, title, flags)
    except Exception:
        # No console fallback, since this is usually a windowed exe
        pass


def ask_yes_no(title: str, text: str, default_no: bool = True) -> bool:
    """Return True if user pressed Yes, False otherwise."""
    import ctypes
    MB_YESNO = 0x04
    MB_ICONQUESTION = 0x20
    MB_DEFBUTTON2 = 0x100  # default = No
    flags = MB_YESNO | MB_ICONQUESTION | (MB_DEFBUTTON2 if default_no else 0)
    res = ctypes.windll.user32.MessageBoxW(None, text, title, flags)
    IDYES = 6
    return res == IDYES


def ask_campaign_action(title: str, text: str) -> str:
    """
    3 choices without TaskDialog and without stdin:
      - Yes    -> "yes"    (replace newest)
      - No     -> "no"     (skip)
      - Cancel -> "choose" (open chooser)
    """
    import ctypes
    MB_YESNOCANCEL = 0x03
    MB_ICONQUESTION = 0x20
    MB_DEFBUTTON2 = 0x100  # default = No (safest)
    flags = MB_YESNOCANCEL | MB_ICONQUESTION | MB_DEFBUTTON2

    res = ctypes.windll.user32.MessageBoxW(
        None,
        text + "\n\nYes = replace newest\nNo = skip\nCancel = choose manually",
        title,
        flags,
    )
    IDYES = 6
    IDNO = 7
    IDCANCEL = 2

    if res == IDYES:
        return "yes"
    if res == IDCANCEL:
        return "choose"
    return "no"


# -------------------------------------------------
# Tk list chooser (for "Choose…")
# -------------------------------------------------
def choose_file_tk(title: str, candidates: List[Path]) -> Optional[Path]:
    """
    Shows a simple list UI to pick a file. Returns selected Path or None.
    """
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.title(title)
    root.geometry("980x520")

    selected: dict = {"path": None}

    frm = ttk.Frame(root, padding=10)
    frm.pack(fill="both", expand=True)

    ttk.Label(frm, text="Select a campaign INI to overwrite:").pack(anchor="w")

    listbox = tk.Listbox(frm, width=160, height=20)
    listbox.pack(fill="both", expand=True, pady=(8, 8))

    idx_to_path: List[Path] = []

    def fmt(p: Path) -> str:
        try:
            mtime = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            mtime = "unknown time"
        return f"{mtime}  |  {p}"

    for p in candidates:
        idx_to_path.append(p)
        listbox.insert("end", fmt(p))

    # preselect first (newest)
    if candidates:
        listbox.selection_set(0)
        listbox.activate(0)

    btn_row = ttk.Frame(frm)
    btn_row.pack(fill="x")

    def on_choose():
        sel = listbox.curselection()
        if sel:
            selected["path"] = idx_to_path[sel[0]]
        root.destroy()

    def on_cancel():
        selected["path"] = None
        root.destroy()

    ttk.Button(btn_row, text="Choose", command=on_choose).pack(side="right", padx=(8, 0))
    ttk.Button(btn_row, text="Cancel", command=on_cancel).pack(side="right")

    root.mainloop()
    return selected["path"]


# -------------------------------------------------
# Simple INI reader (section -> key -> value)
# -------------------------------------------------
def read_ini(path: Path) -> Dict[str, Dict[str, str]]:
    data: Dict[str, Dict[str, str]] = {}
    section: Optional[str] = None

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

        existing: Dict[str, int] = {}
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
def read_config(path: Path) -> Tuple[Path, Path, str]:
    cfg = read_ini(path)

    try:
        callsign = Path(cfg["Paths"]["callsign_ini_path"]).expanduser()
    except Exception:
        raise RuntimeError("Missing callsign_ini_path in config.ini ([Paths])")

    try:
        campaign_folder = Path(cfg["Paths"]["campaign_folder_path"]).expanduser()
    except Exception:
        raise RuntimeError("Missing campaign_folder_path in config.ini ([Paths])")

    pattern = cfg.get("Search", {}).get("pattern", "*.ini")
    return callsign, campaign_folder, pattern


# -------------------------------------------------
# Campaign INI candidates
# -------------------------------------------------
def list_campaign_inis(folder: Path, pattern: str) -> List[Path]:
    if not folder.exists() or not folder.is_dir():
        raise RuntimeError(f"campaign_folder_path is not a valid folder:\n{folder}")

    candidates = [p for p in folder.rglob(pattern) if p.is_file()]
    if not candidates:
        raise RuntimeError(f"No files found in:\n{folder}\n(pattern={pattern})")

    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)  # newest first
    return candidates


# -------------------------------------------------
# Replace target file with source file, keeping target name
# (delete/replace semantics; robust on Windows)
# -------------------------------------------------
def _clear_readonly(p: Path) -> None:
    try:
        mode = p.stat().st_mode
        if not (mode & stat.S_IWRITE):
            os.chmod(p, mode | stat.S_IWRITE)
    except Exception:
        pass


def replace_with_same_name(source: Path, target: Path) -> None:
    """
    Ensures target ends up containing source contents, while keeping target's filename.
    Steps:
      1) copy source -> temp file in target folder
      2) os.replace(temp, target) (overwrites existing target)
    This effectively does "delete target then place source as target".
    """
    if not source.exists():
        raise RuntimeError(f"Source does not exist:\n{source}")

    target.parent.mkdir(parents=True, exist_ok=True)

    # Prepare temp next to target (same folder helps os.replace be reliable)
    tmp = target.with_name(target.name + ".tmp_repl")

    # Clean up previous temp if present
    if tmp.exists():
        _clear_readonly(tmp)
        tmp.unlink()

    # If target is read-only, clear it so replace works
    if target.exists():
        _clear_readonly(target)

    # Copy source to temp
    shutil.copyfile(source, tmp)

    # Atomically replace temp -> target (overwrites target if exists)
    os.replace(str(tmp), str(target))


# -------------------------------------------------
# Main
# -------------------------------------------------
def main(argv) -> int:
    exe_dir = Path(sys.argv[0]).resolve().parent
    cfg_path = exe_dir / "config.ini"

    if not cfg_path.exists():
        msg("INI Merge", f"Missing config.ini:\n{cfg_path}", True)
        return 2

    if len(argv) < 2:
        msg("INI Merge", "Drag & drop mission.ini onto the EXE")
        return 1

    dragged_ini = Path(argv[1]).resolve()
    if not dragged_ini.exists():
        msg("INI Merge", f"File not found:\n{dragged_ini}", True)
        return 2

    try:
        callsign_ini, campaign_folder, pattern = read_config(cfg_path)
    except Exception as e:
        msg("INI Merge", str(e), True)
        return 2

    if not callsign_ini.exists():
        msg("INI Merge", f"callsign.ini not found:\n{callsign_ini}", True)
        return 2

    # Read dragged INI and get STPT
    mission_data = read_ini(dragged_ini)
    stpt = mission_data.get("STPT")
    if not stpt:
        msg("INI Merge", "Dragged INI does not contain a [STPT] section", True)
        return 2

    # Ask: patch callsign.ini?
    q_callsign = (
        "Apply [STPT] from the dragged INI to callsign.ini?\n\n"
        f"TARGET:\n{callsign_ini}\n\n"
        f"SOURCE (drag & drop):\n{dragged_ini}\n\n"
        f"STPT entries: {len(stpt)}\n\n"
        "Proceed?"
    )
    do_callsign = ask_yes_no("INI Merge – callsign.ini", q_callsign, default_no=True)

    callsign_done = False
    if do_callsign:
        patcher = IniPatcher(callsign_ini)
        patcher.set_section("STPT", stpt)
        patcher.write()
        callsign_done = True

    # Campaign candidates
    try:
        candidates = list_campaign_inis(campaign_folder, pattern)
    except Exception as e:
        msg("INI Merge", f"Campaign scan failed:\n\n{e}", True)
        return 2

    newest = candidates[0]

    # 3-choice campaign action (Yes/No/Cancel where Cancel = Choose)
    dialog_text = (
        f"Campaign folder:\n{campaign_folder}\n"
        f"Pattern: {pattern}\n\n"
        f"Newest candidate:\n{newest}\n\n"
        f"Source (drag & drop):\n{dragged_ini}"
    )
    action = ask_campaign_action("INI Merge – Campaign", dialog_text)

    campaign_done = False
    target_campaign_ini: Optional[Path] = None

    if action == "yes":
        target_campaign_ini = newest
    elif action == "choose":
        picked = choose_file_tk("INI Merge – Choose target INI", candidates)
        if picked is not None:
            target_campaign_ini = picked

    # Confirm overwrite (safety)
    if target_campaign_ini is not None:
        confirm = (
            "You are about to REPLACE this file (same name kept):\n\n"
            f"{target_campaign_ini}\n\n"
            "With this dragged file:\n\n"
            f"{dragged_ini}\n\n"
            "Proceed?"
        )
        if ask_yes_no("INI Merge – Confirm replace", confirm, default_no=True):
            try:
                # This keeps the target name: delete/replace semantics
                replace_with_same_name(dragged_ini, target_campaign_ini)
                campaign_done = True
            except Exception as e:
                msg("INI Merge", f"Campaign replace failed:\n\n{e}", True)
                return 2

    # Summary
    summary = "Done.\n\n"
    summary += "(1) callsign.ini: patched\n" if callsign_done else "(1) callsign.ini: skipped\n"
    if campaign_done:
        summary += f"(2) campaign INI: replaced\n    target: {target_campaign_ini}\n"
    else:
        summary += "(2) campaign INI: skipped\n"

    msg("INI Merge", summary)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
