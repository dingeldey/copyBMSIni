# BMS STPT Merger

Small Windows utility to copy the **`[STPT]` section** from a `mission.ini` file into a `callsign.ini` file and, if desired, **replace a campaign mission INI**.

The tool:
- copies **`[STPT]` entries** from a mission file
- can merge them into **`callsign.ini`**
- can **replace a campaign mission INI** in place
- works as a **single portable EXE**
- requires **no console**

---

## What this tool does

### Callsign merge
- Reads **`[STPT]`** from a dragged `mission.ini`
- Copies those entries into **`callsign.ini`**
- Existing keys are **overwritten**
- Missing keys are **added**
- Other sections are **not touched**

### Campaign mission replacement (optional)
- Scans a configured **campaign folder** for mission INI files
- Lets you:
  - replace the **newest** mission INI, or
  - **choose** which campaign INI to replace
- The selected campaign INI is **replaced in place**
  (same filename, same location)

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
campaign_folder_path = C:\FalconBMS\User\Campaigns\MyCampaign

[Search]
pattern = *.ini
```

### Settings

| Setting | Description |
|------|------------|
| `callsign_ini_path` | Full path to your `callsign.ini` |
| `campaign_folder_path` | Campaign folder containing mission INIs |
| `pattern` | Which files to consider (default: `*.ini`) |

---

## How to use

### Option 1: Drag & Drop (recommended)

1. Drag a **mission-provided `mission.ini`**
2. Drop it onto `copyBMSIni.exe`
3. Follow the on-screen dialogs

You will be asked:
- whether to merge `[STPT]` into `callsign.ini`
- whether to replace a campaign mission INI (Yes / No / Choose)

---

### Option 2: Command line

```bat
copyBMSIni.exe C:\path\to\mission.ini
```

---

### Option 3: Right-click → Open with

- Right-click `mission.ini`
- **Open with** → `copyBMSIni.exe`

---

## Campaign workflow (important)

This workflow is intended for cases where **a campaign mission does not load correctly in BMS**.

### Step-by-step

1. In **Falcon BMS**, open the campaign
2. **Save the campaign mission manually**  
   (give it a recognizable name)
3. Tab out of BMS
4. Drag the **mission-provided `mission.ini`** onto `copyBMSIni.exe`
5. Follow the prompts

The selected campaign mission INI is now replaced with the provided mission data.

---

## Load INI in BMS

After replacement:

1. Go back to **Falcon BMS**
2. Go to **Data Cartridge**
3. Select **Load**

All **STPTs**, **Lines**, and **Preplanned Threat STPTs** should now appear correctly.

---

## Build (for developers)

```bat
pyinstaller --clean --onefile --noconsole copyBMSIni.py
```
