# BMS STPT Merger

Small Windows utility to copy the **`[STPT]` section** from a `mission.ini` file into a `callsign.ini` file.

The tool:
- creates a **backup** of `callsign.ini`
- updates or adds all `[STPT]` entries
- works as a **single portable EXE**

---

## What this tool does

- Reads **`[STPT]`** from `mission.ini`
- Copies those entries into **`callsign.ini`**
- Existing keys are **overwritten**
- Missing keys are **added**
- Other sections are **not touched**

Before any change, a backup file is created:

```
callsign.ini_bkp
```

---

## Files

```
copyBMSIni.exe
config.ini
```

`config.ini` must be located **next to the EXE**.

---

## Configuration

### `config.ini`

```ini
[Paths]
callsign_ini_path = C:\FalconBMS\User\Config\callsign.ini

[Backup]
suffix = _bkp
```

### Settings

| Setting | Description |
|------|------------|
| `callsign_ini_path` | Full path to your `callsign.ini` |
| `suffix` | Backup suffix (default: `_bkp`) |

---

## How to use

### Option 1: Drag & Drop (recommended)

1. Drag `mission.ini`
2. Drop it onto `copyBMSIni.exe`
3. Done

---


### Option 2: Command line

```bat
copyBMSIni.exe C:\path\to\mission.ini
```

---

### Option 3 Right-click → Open with

- Right-click `mission.ini`
- **Open with** → `copyBMSIni.exe`

---

## Output

After a successful run:
- `callsign.ini` is updated
- `callsign.ini_bkp` contains the previous version
- A confirmation message is shown

---

## Build (for developers)

```bat
pyinstaller --clean --onefile --noconsole copyBMSIni.py
```

---
