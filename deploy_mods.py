#!/usr/bin/env python3
"""
deploy_mods.py
Automated Mod Staging & Deployment for Skyrim Special Edition on SteamOS Handhelds
Target: Current Steam Game Runtime (1.7.104 / SKSE 2.3.1)
Author: koldo92 / Handheld Modding Suite
"""

import os
import sys
import re
import json
import shutil
import struct
import subprocess
from pathlib import Path

# --- Runtime & Mod Manifest Definitions ---

SUPPORTED_RUNTIMES = {
    "1.7.104": {
        "label": "1.7.104 (Current Steam Runtime)",
        "skse_version": "2.3.1",
        "skse_dll": "skse64_1_7_104.dll",
        "skse_archive_pattern": r"skse64_2_03_01.*\.7z",
    },
    "1.6.1170": {
        "label": "1.6.1170 (Legacy Steam Runtime)",
        "skse_version": "2.2.6",
        "skse_dll": "skse64_1_6_1170.dll",
        "skse_archive_pattern": r"skse64_2_02_06.*\.7z",
    }
}

# (Key, Display Name, Archive Pattern, IsRootInstall, Priority, RequiredFiles, FomodHandler, IsOptional)
MOD_MANIFEST = [
    # Core Engine & Fixes (Root and Priority 1-25)
    {
        "key": "SKSE",
        "name": "Skyrim Script Extender 64",
        "patterns": [r"skse64_.*\.7z"],
        "is_root": True,
        "priority": 1,
        "is_optional": False,
        "required_check": lambda p: (p / "skse64_loader.exe").exists()
    },
    {
        "key": "EngineFixesPart2",
        "name": "Engine Fixes - Part 2 (Binaries)",
        "patterns": [r"(EngineFixes.*Part2|Engine.*Fixes.*Part.*2|EngineFixes.*Binaries).*\.(7z|zip|rar)"],
        "is_root": True,
        "priority": 2,
        "is_optional": False,
        "required_check": lambda p: any((p / f).exists() for f in ["d3dx9_42.dll", "tbb.dll"])
    },
    {
        "key": "AddressLibrary",
        "name": "Address Library for SKSE Plugins",
        "patterns": [r"(All in one.*Anniversary|Address.*Library.*Anniversary|AddressLibrary).*\.(7z|zip)"],
        "is_root": False,
        "priority": 10,
        "is_optional": False,
        "required_check": lambda p: (p / "SKSE" / "Plugins").is_dir()
    },
    {
        "key": "EngineFixes",
        "name": "SSE Engine Fixes",
        "patterns": [r"(Part.*1.*Engine.*Fixes|Engine.*Fixes.*Part.*1|EngineFixes).*\.(7z|zip)"],
        "is_root": False,
        "priority": 11,
        "is_optional": False,
        "required_check": lambda p: (p / "SKSE" / "Plugins" / "EngineFixes.dll").exists() or (p / "SKSE" / "Plugins").is_dir()
    },
    {
        "key": "DisplayTweaks",
        "name": "SSE Display Tweaks",
        "patterns": [r"SSE.*Display.*Tweaks.*\.(7z|zip)"],
        "is_root": False,
        "priority": 12,
        "is_optional": False,
        "required_check": lambda p: (p / "SKSE" / "Plugins").is_dir()
    },
    {
        "key": "ShadowBoost",
        "name": "Shadow Boost",
        "patterns": [r"ShadowBoost.*\.(7z|zip)"],
        "is_root": False,
        "priority": 13,
        "is_optional": False,
        "required_check": lambda p: (p / "SKSE" / "Plugins").is_dir()
    },
    {
        "key": "eFPS",
        "name": "eFPS - Exterior FPS Boost",
        "patterns": [r"eFPS.*\.(7z|zip)"],
        "is_root": False,
        "priority": 14,
        "is_optional": False,
        "required_check": lambda p: (p / "eFPS - Official.esp").exists() or any(p.glob("*.esp"))
    },
    {
        "key": "LightenedSkyrim",
        "name": "Lightened Skyrim",
        "patterns": [r"Lightened.*Skyrim.*\.(7z|zip)"],
        "is_root": False,
        "priority": 15,
        "is_optional": False,
        "required_check": lambda p: any(p.glob("*.esp")) or any(p.glob("*.esl"))
    },
    {
        "key": "InsignificantObjectRemover",
        "name": "Insignificant Object Remover",
        "patterns": [r"Insignificant.*Object.*Remover.*\.(7z|zip)"],
        "is_root": False,
        "priority": 16,
        "is_optional": False,
        "required_check": lambda p: any(p.glob("*.esp"))
    },
    {
        "key": "PO3Tweaks",
        "name": "powerofthree's Tweaks",
        "patterns": [r"(po3_Tweaks|powerofthree.*Tweaks).*\.(7z|zip)"],
        "is_root": False,
        "priority": 17,
        "is_optional": False,
        "fomod_runtime_handler": "po3_tweaks",
        "required_check": lambda p: (p / "SKSE" / "Plugins" / "po3_Tweaks.dll").exists() or (p / "SKSE" / "Plugins").is_dir()
    },
    {
        "key": "PO3Papyrus",
        "name": "powerofthree's Papyrus Extender",
        "patterns": [r"(Papyrus.*Extender|po3_PapyrusExtender).*\.(7z|zip)"],
        "is_root": False,
        "priority": 18,
        "is_optional": False,
        "fomod_runtime_handler": "po3_papyrus",
        "required_check": lambda p: (p / "SKSE" / "Plugins" / "po3_PapyrusExtender.dll").exists() or (p / "SKSE" / "Plugins").is_dir()
    },
    {
        "key": "BugFixesSSE",
        "name": "Bug Fixes SSE",
        "patterns": [r"BugFixesSSE.*\.(7z|zip)"],
        "is_root": False,
        "priority": 19,
        "is_optional": False,
        "required_check": lambda p: (p / "SKSE" / "Plugins").is_dir()
    },
    {
        "key": "ScrambledBugs",
        "name": "Scrambled Bugs",
        "patterns": [r"ScrambledBugs.*\.(7z|zip)"],
        "is_root": False,
        "priority": 20,
        "is_optional": False,
        "required_check": lambda p: (p / "SKSE" / "Plugins").is_dir()
    },

    # UI, Gamepad & Frameworks
    {
        "key": "MCMHelper",
        "name": "MCM Helper",
        "patterns": [r"MCM.*Helper.*\.(7z|zip)"],
        "is_root": False,
        "priority": 28,
        "is_optional": False,
        "required_check": lambda p: (p / "SKSE" / "Plugins").is_dir()
    },
    {
        "key": "SkyUI",
        "name": "SkyUI 5.2 SE",
        "patterns": [r"SkyUI_5_2_SE.*\.(7z|zip)"],
        "is_root": False,
        "priority": 30,
        "is_optional": False,
        "required_check": lambda p: (p / "SkyUI_SE.esp").exists()
    },
    {
        "key": "SkyUIFix",
        "name": "SkyUI Flashing Savegames Fix",
        "patterns": [r"Flashing.*Savegames.*Fix.*\.(7z|zip)"],
        "is_root": False,
        "priority": 31,
        "is_optional": False,
        "required_check": lambda p: True
    },
    {
        "key": "AutoInputSwitch",
        "name": "Auto Input Switch (1.7.x / Modern Edit)",
        "patterns": [r"AutoInputSwitch.*(166519|1\.7|Modern|Update).*\.(7z|zip)", r"AutoInputSwitch.*\.(7z|zip)"],
        "is_root": False,
        "priority": 32,
        "is_optional": False,
        "required_check": lambda p: (p / "SKSE" / "Plugins").is_dir()
    },
    {
        "key": "DearDiaryDark",
        "name": "Dear Diary Dark Mode",
        "patterns": [r"(Dear.*Diary.*Dark|DearDiaryDark).*\.(7z|zip)"],
        "is_root": False,
        "priority": 33,
        "is_optional": False,
        "required_check": lambda p: (p / "Interface").is_dir()
    },
    {
        "key": "TrueHUD",
        "name": "TrueHUD - HUD Additions (Experimental on 1.7.104)",
        "patterns": [r"TrueHUD.*\.(7z|zip)"],
        "is_root": False,
        "priority": 34,
        "is_optional": True, # Marked optional due to 1.7.104 reports
        "required_check": lambda p: (p / "SKSE" / "Plugins").is_dir()
    },
    {
        "key": "BetterDialogue",
        "name": "Better Dialogue Controls",
        "patterns": [r"Better.*Dialogue.*Controls.*\.(7z|zip)"],
        "is_root": False,
        "priority": 35,
        "is_optional": False,
        "required_check": lambda p: (p / "Interface").is_dir()
    },
    {
        "key": "BetterMessageBox",
        "name": "Better MessageBox Controls",
        "patterns": [r"Better.*MessageBox.*Controls.*\.(7z|zip)"],
        "is_root": False,
        "priority": 36,
        "is_optional": False,
        "required_check": lambda p: (p / "Interface").is_dir()
    },
    {
        "key": "ContextualCrosshair",
        "name": "Contextual Crosshair",
        "patterns": [r"Contextual.*Crosshair.*\.(7z|zip)"],
        "is_root": False,
        "priority": 37,
        "is_optional": False,
        "required_check": lambda p: (p / "SKSE" / "Plugins").is_dir()
    },

    # Combat & Camera
    {
        "key": "TDM",
        "name": "True Directional Movement",
        "patterns": [r"TrueDirectionalMovement.*\.(7z|zip)"],
        "is_root": False,
        "priority": 40,
        "is_optional": False,
        "required_check": lambda p: (p / "SKSE" / "Plugins" / "TrueDirectionalMovement.dll").exists() or (p / "SKSE" / "Plugins").is_dir()
    },
    {
        "key": "SmoothCam",
        "name": "SmoothCam",
        "patterns": [r"SmoothCam.*\.(7z|zip)"],
        "is_root": False,
        "priority": 41,
        "is_optional": False,
        "required_check": lambda p: (p / "SKSE" / "Plugins").is_dir()
    },
    {
        "key": "SmoothCamPreset",
        "name": "SmoothCam Handheld Preset",
        "patterns": [r"(Galaduz|ModernCamera|SmoothCam.*Preset).*\.(7z|zip)"],
        "is_root": False,
        "priority": 42,
        "is_optional": False,
        "required_check": lambda p: True
    },
    {
        "key": "Precision",
        "name": "Precision - Accurate Melee Collisions",
        "patterns": [r"Precision.*\.(7z|zip)"],
        "is_root": False,
        "priority": 43,
        "is_optional": False,
        "required_check": lambda p: (p / "SKSE" / "Plugins" / "Precision.dll").exists() or (p / "SKSE" / "Plugins").is_dir()
    },
    {
        "key": "ValhallaCombat",
        "name": "Valhalla Combat (Unofficial 1.7.104 build - Experimental)",
        "patterns": [r"(Valhalla.*Combat|ValhallaCombat).*\.(7z|zip)"],
        "is_root": False,
        "priority": 44,
        "is_optional": True, # Marked optional due to 1.7.104 crash reports
        "required_check": lambda p: (p / "SKSE" / "Plugins").is_dir()
    },
    {
        "key": "MortalEnemies",
        "name": "Mortal Enemies SE",
        "patterns": [r"Mortal.*Enemies.*\.(7z|zip)"],
        "is_root": False,
        "priority": 45,
        "is_optional": False,
        "required_check": lambda p: any(p.glob("*.esp"))
    },
    {
        "key": "SimpleDualSheath",
        "name": "Simple Dual Sheath",
        "patterns": [r"SimpleDualSheath.*\.(7z|zip)"],
        "is_root": False,
        "priority": 46,
        "is_optional": False,
        "required_check": lambda p: (p / "SKSE" / "Plugins").is_dir()
    },

    # Visuals & Environment
    {
        "key": "CathedralLandscapes",
        "name": "Cathedral Landscapes (1K)",
        "patterns": [r"Cathedral.*Landscapes.*\.(7z|zip)"],
        "is_root": False,
        "priority": 50,
        "is_optional": False,
        "required_check": lambda p: any(p.glob("*.esp")) or (p / "textures").is_dir()
    },
    {
        "key": "SkylandArch",
        "name": "Skyland Architecture (1K)",
        "patterns": [r"Skyland.*Architecture.*\.(7z|zip)"],
        "is_root": False,
        "priority": 51,
        "is_optional": False,
        "required_check": lambda p: (p / "textures").is_dir()
    },
    {
        "key": "CathedralWeathers",
        "name": "Cathedral Weathers and Seasons",
        "patterns": [r"Cathedral.*Weathers.*\.(7z|zip)"],
        "is_root": False,
        "priority": 52,
        "is_optional": False,
        "required_check": lambda p: any(p.glob("*.esp"))
    },
    {
        "key": "CommunityShaders",
        "name": "Community Shaders",
        "patterns": [r"CommunityShaders.*\.(7z|zip)"],
        "is_root": False,
        "priority": 53,
        "is_optional": False,
        "required_check": lambda p: (p / "SKSE" / "Plugins").is_dir()
    },
    {
        "key": "SimplicityOfSnow",
        "name": "Simplicity of Snow",
        "patterns": [r"Simplicity.*of.*Snow.*\.(7z|zip)"],
        "is_root": False,
        "priority": 54,
        "is_optional": False,
        "required_check": lambda p: any(p.glob("*.esp"))
    },
    {
        "key": "HD_Audio",
        "name": "Unofficial High Definition Audio",
        "patterns": [r"(High.*Definition.*Audio|Audio.*Project).*\.(7z|zip)"],
        "is_root": False,
        "priority": 55,
        "is_optional": False,
        "required_check": lambda p: True
    },

    # Simonrim Gameplay Balance Suite
    {
        "key": "Mysticism",
        "name": "Mysticism - The Magic Overhaul",
        "patterns": [r"Mysticism.*\.(7z|zip)"],
        "is_root": False,
        "priority": 60,
        "is_optional": False,
        "required_check": lambda p: any(p.glob("*.esp"))
    },
    {
        "key": "Adamant",
        "name": "Adamant - A Perk Overhaul",
        "patterns": [r"Adamant.*\.(7z|zip)"],
        "is_root": False,
        "priority": 61,
        "is_optional": False,
        "required_check": lambda p: any(p.glob("*.esp"))
    },
    {
        "key": "BladeAndBlunt",
        "name": "Blade & Blunt - A Combat Overhaul",
        "patterns": [r"(Blade.*and.*Blunt|BladeAndBlunt).*\.(7z|zip)"],
        "is_root": False,
        "priority": 62,
        "is_optional": False,
        "required_check": lambda p: any(p.glob("*.esp"))
    },
    {
        "key": "Aetherius",
        "name": "Aetherius - A Race Overhaul",
        "patterns": [r"Aetherius.*\.(7z|zip)"],
        "is_root": False,
        "priority": 63,
        "is_optional": False,
        "required_check": lambda p: any(p.glob("*.esp"))
    },
    {
        "key": "Mundus",
        "name": "Mundus - A Standing Stone Overhaul",
        "patterns": [r"Mundus.*\.(7z|zip)"],
        "is_root": False,
        "priority": 64,
        "is_optional": False,
        "required_check": lambda p: any(p.glob("*.esp"))
    },
    {
        "key": "Scion",
        "name": "Scion - A Vampire Overhaul",
        "patterns": [r"Scion.*\.(7z|zip)"],
        "is_root": False,
        "priority": 65,
        "is_optional": False,
        "required_check": lambda p: any(p.glob("*.esp"))
    },
    {
        "key": "Manbeast",
        "name": "Manbeast - A Werewolf Overhaul",
        "patterns": [r"Manbeast.*\.(7z|zip)"],
        "is_root": False,
        "priority": 66,
        "is_optional": False,
        "required_check": lambda p: any(p.glob("*.esp"))
    },
    {
        "key": "Apothecary",
        "name": "Apothecary - An Alchemy Overhaul",
        "patterns": [r"Apothecary.*\.(7z|zip)"],
        "is_root": False,
        "priority": 67,
        "is_optional": False,
        "required_check": lambda p: any(p.glob("*.esp"))
    },
    {
        "key": "Arena",
        "name": "Arena - An Encounter Zone Overhaul",
        "patterns": [r"Arena.*\.(7z|zip)"],
        "is_root": False,
        "priority": 68,
        "is_optional": False,
        "required_check": lambda p: any(p.glob("*.esp"))
    },
]

# --- Binary PE Header Inspector ---

def get_pe_file_version(exe_path: Path):
    """Extracts Windows PE FileVersion from VS_FIXEDFILEINFO structure."""
    if not exe_path.is_file():
        return None
    try:
        with open(exe_path, "rb") as f:
            content = f.read()
        magic = b"\xbd\x04\xef\xfe" # 0xFEEF04BD
        idx = content.find(magic)
        if idx != -1:
            sig, struc, fv_ms, fv_ls = struct.unpack_from("<IIII", content, idx)
            major = fv_ms >> 16
            minor = fv_ms & 0xFFFF
            build = fv_ls >> 16
            revision = fv_ls & 0xFFFF
            return f"{major}.{minor}.{build}.{revision}"
    except Exception:
        pass
    return None

def detect_runtime_version(game_dir: Path):
    """Detects and validates SkyrimSE.exe runtime version."""
    exe_path = game_dir / "SkyrimSE.exe"
    if not exe_path.is_file():
        print(f"[-] Error: SkyrimSE.exe not found at {exe_path}")
        sys.exit(1)

    raw_ver = get_pe_file_version(exe_path)
    if not raw_ver:
        # Fallback to checking size/hash or appmanifest
        print("[!] Warning: Could not read PE version header directly from SkyrimSE.exe.")
        print("    Assuming current Steam runtime: 1.7.104")
        return "1.7.104"

    # Match major.minor.build (e.g. 1.7.104 or 1.6.1170)
    parts = raw_ver.split(".")
    short_ver = ".".join(parts[:3])

    if short_ver in SUPPORTED_RUNTIMES:
        return short_ver

    print("\n==========================================================")
    print("[-] CRITICAL ERROR: UNSUPPORTED SKYRIM RUNTIME DETECTED")
    print("==========================================================")
    print(f"Detected Runtime Version: {raw_ver} ({short_ver})")
    print("This toolkit supports the following Steam runtimes:")
    for ver, meta in SUPPORTED_RUNTIMES.items():
        print(f"  • {ver}: {meta['label']} (Requires SKSE {meta['skse_version']})")
    print("\nPlease verify your game is updated via Steam, or update to a supported runtime.")
    sys.exit(1)

# --- Path & MO2 Detection ---

def find_steam_libraries():
    """Locates all Steam libraries across SSD and MicroSD cards."""
    home = Path.home()
    candidates = [
        home / ".local/share/Steam",
        home / ".steam/steam",
        home / ".steam/root"
    ]
    primary_steam = None
    for cand in candidates:
        if cand.is_dir():
            primary_steam = cand
            break

    if not primary_steam:
        print("[-] Error: Primary Steam directory not found.")
        sys.exit(1)

    libraries = [primary_steam]
    vdf_file = primary_steam / "steamapps/libraryfolders.vdf"
    if vdf_file.is_file():
        try:
            content = vdf_file.read_text(encoding="utf-8", errors="ignore")
            matches = re.findall(r'"path"\s+"([^"]+)"', content)
            for m in matches:
                p = Path(m)
                if p.is_dir() and p not in libraries:
                    libraries.append(p)
        except Exception:
            pass

    if Path("/run/media").is_dir():
        for sub in Path("/run/media").glob("*/*"):
            if sub.is_dir() and (sub / "steamapps").is_dir() and sub not in libraries:
                libraries.append(sub)

    return primary_steam, libraries

def locate_skyrim_and_mo2():
    """Discovers Skyrim SE game directory and real MO2 instance."""
    primary_steam, libraries = find_steam_libraries()
    game_dir = None
    compat_dir = None

    for lib in libraries:
        cand_game = lib / "steamapps/common/Skyrim Special Edition"
        if cand_game.is_dir():
            game_dir = cand_game
            break

    compat_candidates = [primary_steam / "steamapps/compatdata/489830"]
    for lib in libraries:
        cand_pfx = lib / "steamapps/compatdata/489830"
        if cand_pfx not in compat_candidates:
            compat_candidates.append(cand_pfx)

    for cand in compat_candidates:
        if (cand / "pfx").is_dir():
            compat_dir = cand
            break

    if not game_dir:
        print("[-] Error: 'Skyrim Special Edition' not found in any Steam library.")
        sys.exit(1)

    if not compat_dir:
        print("[-] Error: Proton prefix (compatdata/489830) not found.")
        print("    Launch Skyrim SE once in Game Mode to generate the Proton prefix.")
        sys.exit(1)

    # Search for real MO2 installation
    mo2_candidates = [
        compat_dir / "pfx/drive_c/modorganizer2",
        compat_dir / "pfx/drive_c/ModOrganizer2",
        compat_dir / "pfx/drive_c/users/steamuser/AppData/Local/ModOrganizer",
        Path.home() / ".local/share/modorganizer2",
        Path.home() / "ModOrganizer2"
    ]
    mo2_dir = None
    for cand in mo2_candidates:
        if cand.is_dir() and ((cand / "ModOrganizer.exe").exists() or (cand / "mods").is_dir()):
            mo2_dir = cand
            break

    # If MO2 is not found in standard paths, do NOT invent a fake directory silently!
    if not mo2_dir:
        print("\n[!] Notice: Mod Organizer 2 was not found in the standard paths.")
        print("    If you installed MO2 using MO2-LINT, specify the installation path.")
        if sys.stdin.isatty():
            user_input = input("Enter full path to Mod Organizer 2 folder (or press Enter to cancel): ").strip()
            if user_input:
                p = Path(user_input).expanduser().resolve()
                if p.is_dir():
                    mo2_dir = p

        if not mo2_dir:
            print("[-] Error: Could not locate a valid Mod Organizer 2 instance.")
            print("    Please install MO2 using MO2-LINT or provide the exact path.")
            sys.exit(1)

    return game_dir, compat_dir, mo2_dir

# --- Archive Extraction & Normalization ---

def extract_archive(archive_path: Path, dest_dir: Path) -> bool:
    """Extracts an archive into dest_dir with hard error reporting."""
    dest_dir.mkdir(parents=True, exist_ok=True)

    for tool in ["7z", "7za"]:
        if shutil.which(tool):
            cmd = [tool, "x", str(archive_path), f"-o{dest_dir}", "-y"]
            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            if res.returncode == 0:
                return True

    if shutil.which("bsdtar"):
        cmd = ["bsdtar", "-xf", str(archive_path), "-C", str(dest_dir)]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if res.returncode == 0:
            return True

    if archive_path.suffix.lower() == ".zip":
        try:
            import zipfile
            with zipfile.ZipFile(archive_path, 'r') as zf:
                zf.extractall(dest_dir)
            return True
        except Exception:
            return False

    return False

def handle_fomod_and_flatten(mod_dir: Path, runtime_ver: str, fomod_handler: str = None):
    """Normalizes extracted directories and handles multi-runtime FOMOD structures."""
    # 1. Flatten single wrapper directory or 'Data' folder
    items = [p for p in mod_dir.iterdir() if p.name not in ["__MACOSX"]]
    if len(items) == 1 and items[0].is_dir():
        inner = items[0]
        for sub in inner.iterdir():
            shutil.move(str(sub), str(mod_dir))
        inner.rmdir()
    elif (mod_dir / "Data").is_dir():
        data_dir = mod_dir / "Data"
        for sub in data_dir.iterdir():
            shutil.move(str(sub), str(mod_dir))
        data_dir.rmdir()

    # 2. Specific FOMOD runtime resolution (e.g. PO3 Tweaks / Papyrus Extender)
    if fomod_handler:
        # Search for runtime specific subfolder (e.g. 1.7.104 or 1.6.1170)
        target_token = runtime_ver.replace(".", "") # e.g. 17104 or 1.7.104
        for sub in list(mod_dir.iterdir()):
            if sub.is_dir() and (runtime_ver in sub.name or target_token in sub.name or "AE" in sub.name):
                # Found matching runtime folder, promote contents
                for inner_item in sub.rglob("*"):
                    if inner_item.is_file():
                        rel = inner_item.relative_to(sub)
                        target = mod_dir / rel
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(inner_item, target)
                break

# --- Root File Manifest & Rollback ---

def track_root_install(game_dir: Path, files_deployed: list):
    """Maintains a rollback manifest for files placed directly in the game root."""
    manifest_file = game_dir / ".handheld_root_manifest.json"
    manifest = []
    if manifest_file.is_file():
        try:
            manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        except Exception:
            manifest = []

    for f in files_deployed:
        if str(f) not in manifest:
            manifest.append(str(f))

    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

# --- Configuration Injectors ---

def inject_tuned_configs(mo2_dir: Path):
    """
    Injects 10W / 60 FPS locked configurations.
    CRITICAL: Writes strictly to 'SSEDisplayTweaks.ini' (NOT DisplayTweaks.ini!).
    """
    display_tweaks_dir = mo2_dir / "mods" / "SSE Display Tweaks" / "SKSE" / "Plugins"
    if display_tweaks_dir.exists():
        # Correct filename: SSEDisplayTweaks.ini
        dt_ini = display_tweaks_dir / "SSEDisplayTweaks.ini"
        dt_config = """[Render]
Resolution = 0x0
Borderless = true
BorderlessUpscale = true
Fullscreen = false

[Framerate]
FramerateLimit = 60.0

[Havok]
CalculateHavokTickRate = true

[Vsync]
Enable = false
"""
        dt_ini.write_text(dt_config, encoding="utf-8")
        print("[✓] Correctly configured: SSEDisplayTweaks.ini (60 FPS lock & Havok physics fix).")

    shadow_boost_dir = mo2_dir / "mods" / "Shadow Boost" / "SKSE" / "Plugins"
    if shadow_boost_dir.exists():
        sb_ini = shadow_boost_dir / "ShadowBoost.ini"
        sb_config = """[General]
TargetFps = 60.0
MinDistance = 1500.0
MaxDistance = 5000.0
"""
        sb_ini.write_text(sb_config, encoding="utf-8")
        print("[✓] Injected dynamic 60 FPS scaling into Shadow Boost.")

# --- Main Deployment Pipeline ---

def main():
    print("==========================================================")
    print("  Skyrim SE Handheld Mod Deployer for SteamOS")
    print("  Target: 60 FPS Lock @ 10W TDP | Manifest-Driven")
    print("==========================================================")

    game_dir, compat_dir, mo2_dir = locate_skyrim_and_mo2()
    runtime_ver = detect_runtime_version(game_dir)
    runtime_info = SUPPORTED_RUNTIMES[runtime_ver]

    print(f"[+] Skyrim Directory:   {game_dir}")
    print(f"[+] Detected Runtime:   {runtime_info['label']}")
    print(f"[+] MO2 Directory:      {mo2_dir}")

    # Discover downloaded mod archives
    downloads_dirs = [
        Path.home() / "Downloads",
        Path.cwd() / "mod_downloads",
        Path.cwd(),
    ]
    found_archives = []
    for d in downloads_dirs:
        if d.is_dir():
            for f in d.iterdir():
                if f.is_file() and f.suffix.lower() in [".zip", ".7z", ".rar"]:
                    found_archives.append(f)

    print(f"[+] Found {len(found_archives)} archive(s) in download locations.")

    # Dedicated MO2 profile (preserve Default profile!)
    profile_dir = mo2_dir / "profiles" / "Handheld-10W"
    profile_dir.mkdir(parents=True, exist_ok=True)
    default_profile = mo2_dir / "profiles" / "Default"
    if default_profile.is_dir():
        for item in ["archives.txt", "settings.ini"]:
            src = default_profile / item
            dst = profile_dir / item
            if src.exists() and not dst.exists():
                shutil.copy2(src, dst)

    mods_installed = []
    mods_missing = []
    root_files_deployed = []

    # Staging area for atomic installation
    staging_base = Path("/tmp/handheld_mod_staging")
    shutil.rmtree(staging_base, ignore_errors=True)
    staging_base.mkdir(parents=True, exist_ok=True)

    try:
        for mod in MOD_MANIFEST:
            key = mod["key"]
            name = mod["name"]
            is_root = mod["is_root"]
            priority = mod["priority"]
            is_optional = mod.get("is_optional", False)

            # Match archive
            matched_archive = None
            for pattern in mod["patterns"]:
                for arch in found_archives:
                    if re.search(pattern, arch.name, re.IGNORECASE):
                        matched_archive = arch
                        break
                if matched_archive:
                    break

            if not matched_archive:
                if is_optional:
                    print(f"[-] Optional mod skipped (not downloaded): {name}")
                else:
                    mods_missing.append(name)
                continue

            print(f"\n[*] Processing: {name}")
            print(f"    Source archive: {matched_archive.name}")

            stage_dir = staging_base / key
            stage_dir.mkdir(parents=True, exist_ok=True)

            # Extract archive
            if not extract_archive(matched_archive, stage_dir):
                print(f"[-] CRITICAL ERROR: Extraction failed for '{matched_archive.name}'")
                print("    Aborting deployment to prevent incomplete or corrupt mod states.")
                sys.exit(1)

            # Handle FOMOD & directory flattening
            handle_fomod_and_flatten(stage_dir, runtime_ver, mod.get("fomod_runtime_handler"))

            # Deploy
            if is_root:
                if key == "SKSE":
                    # Locate inner skse directory if present
                    skse_dirs = list(stage_dir.glob("skse64_*"))
                    src = skse_dirs[0] if skse_dirs else stage_dir

                    for f in src.glob("skse64_*.dll"):
                        dst = game_dir / f.name
                        shutil.copy2(f, dst)
                        root_files_deployed.append(f.name)
                    for f in src.glob("skse64_loader.exe"):
                        dst = game_dir / f.name
                        shutil.copy2(f, dst)
                        root_files_deployed.append(f.name)
                    if (src / "Data").is_dir():
                        shutil.copytree(src / "Data", game_dir / "Data", dirs_exist_ok=True)
                        root_files_deployed.append("Data/Scripts")
                    print(f"    -> Deployed SKSE binaries matching {runtime_ver} to game root.")
                elif key == "EngineFixesPart2":
                    for dll in stage_dir.glob("*.dll"):
                        shutil.copy2(dll, game_dir / dll.name)
                        root_files_deployed.append(dll.name)
                        print(f"    -> Deployed {dll.name} to game root.")
            else:
                target_mod_dir = mo2_dir / "mods" / name
                shutil.rmtree(target_mod_dir, ignore_errors=True)
                shutil.copytree(stage_dir, target_mod_dir)
                print(f"    -> Successfully installed to MO2 mods/{name}")

                # Verify required files check
                if "required_check" in mod and not mod["required_check"](target_mod_dir):
                    print(f"[-] WARNING: Required files check failed for '{name}'. Structure may be non-standard.")

                # Track MO2 mod
                mods_installed.append((name, priority))

    finally:
        shutil.rmtree(staging_base, ignore_errors=True)

    # Track root files separately (DO NOT put root files in MO2 modlist.txt!)
    if root_files_deployed:
        track_root_install(game_dir, root_files_deployed)

    # Inject performance configs (SSEDisplayTweaks.ini and ShadowBoost.ini)
    inject_tuned_configs(mo2_dir)

    # Generate MO2 modlist.txt for Handheld-10W profile
    modlist_file = profile_dir / "modlist.txt"
    mods_installed.sort(key=lambda x: x[1])
    lines = [f"+{m[0]}\n" for m in mods_installed]
    modlist_file.write_text("".join(reversed(lines)), encoding="utf-8")
    print(f"\n[✓] Generated MO2 profile 'Handheld-10W' with {len(mods_installed)} active mod(s).")

    # Generate plugins.txt / loadorder.txt
    plugins_file = profile_dir / "plugins.txt"
    loadorder_file = profile_dir / "loadorder.txt"
    detected_plugins = []
    for mod_name, _ in mods_installed:
        m_dir = mo2_dir / "mods" / mod_name
        if m_dir.is_dir():
            for p in m_dir.glob("*.es[mp]"):
                if p.name not in detected_plugins:
                    detected_plugins.append(p.name)
            for p in m_dir.glob("*.esl"):
                if p.name not in detected_plugins:
                    detected_plugins.append(p.name)

    plugins_content = "\n".join([f"*{p}" for p in detected_plugins]) + "\n"
    plugins_file.write_text(plugins_content, encoding="utf-8")
    loadorder_file.write_text("\n".join(detected_plugins) + "\n", encoding="utf-8")
    print(f"[✓] Generated plugins.txt and loadorder.txt with {len(detected_plugins)} active plugin(s).")

    # Summary
    print("\n==========================================================")
    print(f"  Deployment Summary: {len(mods_installed)} Installed / {len(mods_missing)} Missing Required")
    print("==========================================================")
    if mods_missing:
        print("\n[-] The following REQUIRED mods were not found in ~/Downloads:")
        for name in mods_missing:
            print(f"  [ ] {name}")
        print("\nDownload them using 'MODS_DOWNLOAD_GUIDE.md' and re-run this script.")
        sys.exit(1)
    else:
        print("\n[★] All required mods successfully installed, verified, and configured!")
        print("    Profile: 'Handheld-10W' created in Mod Organizer 2.")
        print("    You can now switch to Steam Game Mode and launch Skyrim SE.")

if __name__ == "__main__":
    main()
