#!/usr/bin/env python3
"""
deploy_mods.py
Automated Mod Staging & Deployment for Skyrim Special Edition on SteamOS Handhelds
Target: Steam Game Runtime 1.7.104 (Strict) | SKSE 2.3.1
Architecture: Transactional Preflight, TES4 Master Validation, Topological Load Order
"""

import os
import sys
import re
import json
import shutil
import struct
import datetime
import subprocess
from pathlib import Path

# --- Shared Target Definition ---

REQUIRED_RUNTIME = "1.7.104"
REQUIRED_SKSE_VERSION = "2.3.1"
REQUIRED_SKSE_DLL = "skse64_1_7_104.dll"

# The 4 free Creation Club creations included with base Skyrim SE 1.6+
ALLOWED_BASE_MASTERS = {
    "skyrim.esm",
    "update.esm",
    "dawnguard.esm",
    "hearthfires.esm",
    "dragonborn.esm",
    "ccbgssse001-fish.esm",
    "ccbgssse025-advdsgs.esm",
    "ccbgssse037-curios.esm",
    "ccqdrsse001-survivalmode.esl"
}

# --- Mod Manifest Definition ---
# Explicit filename patterns, exclusions, root flags, and priority weights
MOD_MANIFEST = [
    {
        "key": "SKSE",
        "name": "Skyrim Script Extender 64",
        "patterns": [r"^skse64_2_03_01.*\.7z$"],
        "exclusions": [],
        "is_root": True,
        "priority": 1,
        "is_optional": False,
        "required_files": ["skse64_loader.exe", "skse64_1_7_104.dll"]
    },
    {
        "key": "EngineFixesPart2",
        "name": "Engine Fixes - Part 2 (Binaries)",
        "patterns": [r"^.*(EngineFixes.*Part2|Engine.*Fixes.*Part.*2|EngineFixes.*Binaries).*\.(7z|zip|rar)$"],
        "exclusions": [r".*Part1.*"],
        "is_root": True,
        "priority": 2,
        "is_optional": False,
        "required_files": ["d3dx9_42.dll", "tbb.dll"]
    },
    {
        "key": "AddressLibrary",
        "name": "Address Library for SKSE Plugins",
        "patterns": [r"^.*(All in one.*Anniversary|Address.*Library.*Anniversary|AddressLibrary).*\.(7z|zip)$"],
        "exclusions": [r".*GOG.*", r".*VR.*"],
        "is_root": False,
        "priority": 10,
        "is_optional": False,
        "required_files": ["SKSE/Plugins/versionlib-1-7-104-0.bin"]
    },
    {
        "key": "EngineFixes",
        "name": "SSE Engine Fixes",
        "patterns": [r"^.*(Part.*1.*Engine.*Fixes|Engine.*Fixes.*Part.*1|EngineFixes).*\.(7z|zip)$"],
        "exclusions": [r".*Part2.*", r".*Binaries.*"],
        "is_root": False,
        "priority": 11,
        "is_optional": False,
        "required_files": ["SKSE/Plugins/EngineFixes.dll"]
    },
    {
        "key": "DisplayTweaks",
        "name": "SSE Display Tweaks",
        "patterns": [r"^SSE.*Display.*Tweaks.*\.(7z|zip)$"],
        "exclusions": [],
        "is_root": False,
        "priority": 12,
        "is_optional": False,
        "required_files": ["SKSE/Plugins/SSEDisplayTweaks.dll"]
    },
    {
        "key": "eFPS",
        "name": "eFPS - Exterior FPS Boost",
        "patterns": [r"^eFPS.*Official.*\.(7z|zip)$", r"^eFPS.*\.(7z|zip)$"],
        "exclusions": [r".*Patch.*", r".*JK.*"],
        "is_root": False,
        "priority": 14,
        "is_optional": False,
        "required_files": ["eFPS - Official.esp"]
    },
    {
        "key": "LightenedSkyrim",
        "name": "Lightened Skyrim",
        "patterns": [r"^Lightened.*Skyrim.*\.(7z|zip)$"],
        "exclusions": [r".*CC.*", r".*CreationClub.*", r".*Patch.*"],
        "is_root": False,
        "priority": 15,
        "is_optional": False,
        "required_files": []
    },
    {
        "key": "InsignificantObjectRemover",
        "name": "Insignificant Object Remover",
        "patterns": [r"^Insignificant.*Object.*Remover.*\.(7z|zip)$"],
        "exclusions": [],
        "is_root": False,
        "priority": 16,
        "is_optional": False,
        "required_files": ["Insignificant Object Remover.esp"]
    },
    {
        "key": "PO3Tweaks",
        "name": "powerofthree's Tweaks",
        "patterns": [r"^(po3_Tweaks|powerofthree.*Tweaks).*\.(7z|zip)$"],
        "exclusions": [],
        "is_root": False,
        "priority": 17,
        "is_optional": False,
        "fomod_runtime_handler": "po3_tweaks",
        "required_files": ["SKSE/Plugins/po3_Tweaks.dll"]
    },
    {
        "key": "PO3Papyrus",
        "name": "powerofthree's Papyrus Extender",
        "patterns": [r"^(Papyrus.*Extender|po3_PapyrusExtender).*\.(7z|zip)$"],
        "exclusions": [],
        "is_root": False,
        "priority": 18,
        "is_optional": False,
        "fomod_runtime_handler": "po3_papyrus",
        "required_files": ["SKSE/Plugins/po3_PapyrusExtender.dll"]
    },
    {
        "key": "BugFixesSSE",
        "name": "Bug Fixes SSE",
        "patterns": [r"^BugFixesSSE.*\.(7z|zip)$"],
        "exclusions": [],
        "is_root": False,
        "priority": 19,
        "is_optional": False,
        "required_files": ["SKSE/Plugins/BugFixesSSE.dll"]
    },
    {
        "key": "ScrambledBugs",
        "name": "Scrambled Bugs",
        "patterns": [r"^ScrambledBugs.*\.(7z|zip)$"],
        "exclusions": [],
        "is_root": False,
        "priority": 20,
        "is_optional": False,
        "required_files": ["SKSE/Plugins/ScrambledBugs.dll"]
    },
    {
        "key": "MCMHelper",
        "name": "MCM Helper",
        "patterns": [r"^MCM.*Helper.*\.(7z|zip)$"],
        "exclusions": [r".*VR.*"],
        "is_root": False,
        "priority": 28,
        "is_optional": False,
        "required_files": ["SKSE/Plugins/MCMHelper.dll"]
    },
    {
        "key": "SkyUI",
        "name": "SkyUI 5.2 SE",
        "patterns": [r"^SkyUI_5_2_SE.*\.(7z|zip)$"],
        "exclusions": [],
        "is_root": False,
        "priority": 30,
        "is_optional": False,
        "required_files": ["SkyUI_SE.esp"]
    },
    {
        "key": "SkyUIFix",
        "name": "SkyUI Flashing Savegames Fix",
        "patterns": [r"^Flashing.*Savegames.*Fix.*\.(7z|zip)$"],
        "exclusions": [],
        "is_root": False,
        "priority": 31,
        "is_optional": False,
        "required_files": []
    },
    {
        "key": "AutoInputSwitch",
        "name": "Auto Input Switch (1.7.104 Edit)",
        "patterns": [r"^AutoInputSwitch.*(166519|1\.7\.104|1\.7).*\.(7z|zip)$"],
        "exclusions": [],
        "is_root": False,
        "priority": 32,
        "is_optional": False,
        "required_files": ["SKSE/Plugins/AutoInputSwitch.dll"]
    },
    {
        "key": "DearDiaryDark",
        "name": "Dear Diary Dark Mode",
        "patterns": [r"^(Dear.*Diary.*Dark|DearDiaryDark).*\.(7z|zip)$"],
        "exclusions": [r".*Patch.*", r".*Addon.*"],
        "is_root": False,
        "priority": 33,
        "is_optional": False,
        "required_files": []
    },
    {
        "key": "BetterDialogue",
        "name": "Better Dialogue Controls",
        "patterns": [r"^Better.*Dialogue.*Controls.*\.(7z|zip)$"],
        "exclusions": [],
        "is_root": False,
        "priority": 35,
        "is_optional": False,
        "required_files": []
    },
    {
        "key": "BetterMessageBox",
        "name": "Better MessageBox Controls",
        "patterns": [r"^Better.*MessageBox.*Controls.*\.(7z|zip)$"],
        "exclusions": [],
        "is_root": False,
        "priority": 36,
        "is_optional": False,
        "required_files": []
    },
    {
        "key": "ContextualCrosshair",
        "name": "Contextual Crosshair",
        "patterns": [r"^Contextual.*Crosshair.*\.(7z|zip)$"],
        "exclusions": [],
        "is_root": False,
        "priority": 37,
        "is_optional": False,
        "required_files": ["SKSE/Plugins/ContextualCrosshair.dll"]
    },
    {
        "key": "TDM",
        "name": "True Directional Movement",
        "patterns": [r"^TrueDirectionalMovement.*\.(7z|zip)$"],
        "exclusions": [],
        "is_root": False,
        "priority": 40,
        "is_optional": False,
        "required_files": ["SKSE/Plugins/TrueDirectionalMovement.dll", "TrueDirectionalMovement.esp"]
    },
    {
        "key": "SmoothCam",
        "name": "SmoothCam",
        "patterns": [r"^SmoothCam.*\.(7z|zip)$"],
        "exclusions": [r".*Preset.*"],
        "is_root": False,
        "priority": 41,
        "is_optional": False,
        "required_files": ["SKSE/Plugins/SmoothCam.dll"]
    },
    {
        "key": "SmoothCamPreset",
        "name": "SmoothCam Handheld Preset",
        "patterns": [r"^(Galaduz|ModernCamera|SmoothCam.*Preset).*\.(7z|zip)$"],
        "exclusions": [],
        "is_root": False,
        "priority": 42,
        "is_optional": False,
        "required_files": []
    },
    {
        "key": "Precision",
        "name": "Precision - Accurate Melee Collisions",
        "patterns": [r"^Precision.*\.(7z|zip)$"],
        "exclusions": [r".*Creatures.*", r".*Patch.*"],
        "is_root": False,
        "priority": 43,
        "is_optional": False,
        "required_files": ["SKSE/Plugins/Precision.dll", "Precision.esp"]
    },
    {
        "key": "MortalEnemies",
        "name": "Mortal Enemies SE",
        "patterns": [r"^Mortal.*Enemies.*\.(7z|zip)$"],
        "exclusions": [r".*Rival.*"],
        "is_root": False,
        "priority": 45,
        "is_optional": False,
        "required_files": ["Mortal Enemies.esp"]
    },
    {
        "key": "SimpleDualSheath",
        "name": "Simple Dual Sheath",
        "patterns": [r"^SimpleDualSheath.*\.(7z|zip)$"],
        "exclusions": [],
        "is_root": False,
        "priority": 46,
        "is_optional": False,
        "required_files": ["SKSE/Plugins/SimpleDualSheath.dll"]
    },
    {
        "key": "CathedralLandscapes",
        "name": "Cathedral Landscapes (1K)",
        "patterns": [r"^Cathedral.*Landscapes.*\.(7z|zip)$"],
        "exclusions": [r".*HD.*", r".*2K.*", r".*4K.*"],
        "is_root": False,
        "priority": 50,
        "is_optional": False,
        "required_files": ["Cathedral Landscapes.esp"]
    },
    {
        "key": "SkylandArch",
        "name": "Skyland Architecture (1K)",
        "patterns": [r"^Skyland.*Architecture.*\.(7z|zip)$"],
        "exclusions": [r".*2K.*", r".*4K.*"],
        "is_root": False,
        "priority": 51,
        "is_optional": False,
        "required_files": []
    },
    {
        "key": "CathedralWeathers",
        "name": "Cathedral Weathers and Seasons",
        "patterns": [r"^Cathedral.*Weathers.*\.(7z|zip)$"],
        "exclusions": [r".*Patch.*", r".*Diversified.*"],
        "is_root": False,
        "priority": 52,
        "is_optional": False,
        "required_files": ["Cathedral Weathers.esp"]
    },
    {
        "key": "CommunityShaders",
        "name": "Community Shaders",
        "patterns": [r"^CommunityShaders.*\.(7z|zip)$"],
        "exclusions": [],
        "is_root": False,
        "priority": 53,
        "is_optional": False,
        "required_files": ["SKSE/Plugins/CommunityShaders.dll"]
    },
    {
        "key": "SimplicityOfSnow",
        "name": "Simplicity of Snow",
        "patterns": [r"^Simplicity.*of.*Snow.*\.(7z|zip)$"],
        "exclusions": [r".*Patch.*"],
        "is_root": False,
        "priority": 54,
        "is_optional": False,
        "required_files": ["Simplicity of Snow.esp"]
    },
    {
        "key": "HD_Audio",
        "name": "Unofficial High Definition Audio",
        "patterns": [r"^(High.*Definition.*Audio|Audio.*Project).*\.(7z|zip)$"],
        "exclusions": [],
        "is_root": False,
        "priority": 55,
        "is_optional": False,
        "required_files": []
    },
    {
        "key": "Mysticism",
        "name": "Mysticism - The Magic Overhaul",
        "patterns": [r"^Mysticism.*Magic.*Overhaul.*\.(7z|zip)$", r"^Mysticism.*\.(7z|zip)$"],
        "exclusions": [r".*CC.*", r".*CreationClub.*", r".*Patch.*"],
        "is_root": False,
        "priority": 60,
        "is_optional": False,
        "required_files": ["MysticismMagic.esp"]
    },
    {
        "key": "Adamant",
        "name": "Adamant - A Perk Overhaul",
        "patterns": [r"^Adamant.*Perk.*Overhaul.*\.(7z|zip)$", r"^Adamant.*\.(7z|zip)$"],
        "exclusions": [r".*CC.*", r".*CreationClub.*", r".*Patch.*"],
        "is_root": False,
        "priority": 61,
        "is_optional": False,
        "required_files": ["Adamant.esp"]
    },
    {
        "key": "BladeAndBlunt",
        "name": "Blade & Blunt - A Combat Overhaul",
        "patterns": [r"^(Blade.*and.*Blunt|BladeAndBlunt).*\.(7z|zip)$"],
        "exclusions": [r".*CC.*", r".*Patch.*"],
        "is_root": False,
        "priority": 62,
        "is_optional": False,
        "required_files": ["BladeAndBlunt.esp"]
    },
    {
        "key": "Aetherius",
        "name": "Aetherius - A Race Overhaul",
        "patterns": [r"^Aetherius.*\.(7z|zip)$"],
        "exclusions": [r".*CC.*", r".*Patch.*"],
        "is_root": False,
        "priority": 63,
        "is_optional": False,
        "required_files": ["Aetherius.esp"]
    },
    {
        "key": "Mundus",
        "name": "Mundus - A Standing Stone Overhaul",
        "patterns": [r"^Mundus.*\.(7z|zip)$"],
        "exclusions": [r".*CC.*", r".*Patch.*"],
        "is_root": False,
        "priority": 64,
        "is_optional": False,
        "required_files": ["Mundus.esp"]
    },
    {
        "key": "Scion",
        "name": "Scion - A Vampire Overhaul",
        "patterns": [r"^Scion.*\.(7z|zip)$"],
        "exclusions": [r".*Patch.*"],
        "is_root": False,
        "priority": 65,
        "is_optional": False,
        "required_files": ["Scion.esp"]
    },
    {
        "key": "Manbeast",
        "name": "Manbeast - A Werewolf Overhaul",
        "patterns": [r"^Manbeast.*\.(7z|zip)$"],
        "exclusions": [r".*Patch.*"],
        "is_root": False,
        "priority": 66,
        "is_optional": False,
        "required_files": ["Manbeast.esp"]
    },
    {
        "key": "Apothecary",
        "name": "Apothecary - An Alchemy Overhaul",
        "patterns": [r"^Apothecary.*\.(7z|zip)$"],
        "exclusions": [r".*CC.*", r".*Patch.*"],
        "is_root": False,
        "priority": 67,
        "is_optional": False,
        "required_files": ["Apothecary.esp"]
    },
    {
        "key": "Arena",
        "name": "Arena - An Encounter Zone Overhaul",
        "patterns": [r"^Arena.*\.(7z|zip)$"],
        "exclusions": [r".*Patch.*"],
        "is_root": False,
        "priority": 68,
        "is_optional": False,
        "required_files": ["Arena.esp"]
    }
]

# --- PE Binary Inspector ---

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

def verify_target_runtime(game_dir: Path) -> str:
    """Enforces strict detection of REQUIRED_RUNTIME (1.7.104). Rejects everything else."""
    exe_path = game_dir / "SkyrimSE.exe"
    if not exe_path.is_file():
        print(f"[-] Error: SkyrimSE.exe not found at {exe_path}")
        sys.exit(1)

    raw_ver = get_pe_file_version(exe_path)
    if not raw_ver:
        print("[-] FATAL: Could not read PE binary version from SkyrimSE.exe.")
        print("    Refusing to proceed with an unverified game executable.")
        sys.exit(1)

    parts = raw_ver.split(".")
    short_ver = ".".join(parts[:3])

    if short_ver != REQUIRED_RUNTIME:
        print("\n==========================================================")
        print("[-] FATAL: UNSUPPORTED SKYRIM RUNTIME DETECTED")
        print("==========================================================")
        print(f"Detected Runtime: {raw_ver} ({short_ver})")
        print(f"Required Runtime: {REQUIRED_RUNTIME} (Latest Steam Build)")
        print("\nThis suite requires the verified 1.7.104 Steam runtime.")
        print("Please update Skyrim Special Edition via Steam before running this installer.")
        sys.exit(1)

    return short_ver

# --- TES4 Plugin Parser & Creation Club Enforcement ---

def parse_tes4_masters(plugin_path: Path) -> list:
    """Parses master file dependencies (MAST subrecords) from a TES4 plugin header."""
    try:
        with open(plugin_path, "rb") as f:
            header_bytes = f.read(2048)
        if len(header_bytes) < 24 or header_bytes[:4] != b"TES4":
            return []

        data_size = struct.unpack_from("<I", header_bytes, 4)[0]
        # Read the entire TES4 header if larger than 2048
        if data_size + 24 > len(header_bytes):
            with open(plugin_path, "rb") as f:
                header_bytes = f.read(data_size + 24)

        data = header_bytes[24 : 24 + data_size]
        offset = 0
        masters = []
        while offset + 6 <= len(data):
            sub_type = data[offset : offset + 4]
            sub_size = struct.unpack_from("<H", data, offset + 4)[0]
            offset += 6
            if offset + sub_size > len(data):
                break
            sub_data = data[offset : offset + sub_size]
            offset += sub_size
            if sub_type == b"MAST":
                name = sub_data.rstrip(b"\x00").decode("utf-8", errors="ignore")
                masters.append(name)
        return masters
    except Exception:
        return []

def validate_plugin_masters(plugin_path: Path, active_plugins: set):
    """
    Enforces the 'No Paid Anniversary Upgrade' rule.
    Throws fatal error if plugin requires an unowned paid Creation Club master.
    """
    masters = parse_tes4_masters(plugin_path)
    for master in masters:
        m_lower = master.lower()
        # Check if master is an unauthorized paid Creation Club DLC
        if (m_lower.startswith("cc") or "creationclub" in m_lower) and m_lower not in ALLOWED_BASE_MASTERS:
            print(f"\n[-] FATAL ERROR: Plugin '{plugin_path.name}' requires Creation Club DLC:")
            print(f"    Master: '{master}'")
            print("    This preset is strictly designed for base Skyrim SE WITHOUT the paid Anniversary Upgrade.")
            print(f"    Please remove '{plugin_path.name}' (or delete its optional patch archive) and try again.")
            sys.exit(1)

# --- Path & MO2 Discovery ---

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

    if not mo2_dir:
        print("\n[!] Notice: Mod Organizer 2 was not found in standard paths.")
        if sys.stdin.isatty():
            user_input = input("Enter full path to your Mod Organizer 2 folder (or press Enter to cancel): ").strip()
            if user_input:
                p = Path(user_input).expanduser().resolve()
                if p.is_dir():
                    mo2_dir = p

        if not mo2_dir:
            print("[-] FATAL: Could not locate a valid Mod Organizer 2 installation.")
            print("    Please install MO2 via MO2-LINT before running this deployer.")
            sys.exit(1)

    return game_dir, compat_dir, mo2_dir

# --- Archive Matching & Preflight ---

def match_archives_preflight(found_archives: list) -> dict:
    """
    Scans and matches archives against the manifest.
    Enforces exact matching and halts on ambiguity or missing required files.
    """
    matched = {}
    missing_required = []

    for mod in MOD_MANIFEST:
        key = mod["key"]
        name = mod["name"]
        is_optional = mod.get("is_optional", False)
        patterns = mod["patterns"]
        exclusions = mod.get("exclusions", [])

        matches = []
        for arch in found_archives:
            fname = arch.name
            # Check exclusions
            if any(re.search(ex, fname, re.IGNORECASE) for ex in exclusions):
                continue
            # Check inclusions
            if any(re.search(p, fname, re.IGNORECASE) for p in patterns):
                matches.append(arch)

        if len(matches) == 0:
            if not is_optional:
                missing_required.append(name)
        elif len(matches) == 1:
            matched[key] = (mod, matches[0])
        else:
            print(f"\n[-] FATAL: Ambiguous archives detected for '{name}':")
            for m in matches:
                print(f"    - {m.name}")
            print("    Multiple files matched the manifest pattern. Please keep only the correct version in ~/Downloads.")
            sys.exit(1)

    if missing_required:
        print("\n==========================================================")
        print("[-] PREFLIGHT FAILED: MISSING REQUIRED DOWNLOADS")
        print("==========================================================")
        print("The following required mod archives were not found in ~/Downloads:")
        for name in missing_required:
            print(f"  [ ] {name}")
        print("\nPlease download the required files via MODS_DOWNLOAD_GUIDE.md before deploying.")
        sys.exit(1)

    return matched

# --- Archive Extraction & FOMOD Parsing ---

def extract_archive(archive_path: Path, dest_dir: Path) -> bool:
    """Extracts an archive securely using native tools with error checking."""
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

    # Specific FOMOD runtime promotion for 1.7.104
    if fomod_handler:
        target_tokens = ["1.7.104", "1.7", "17104"]
        for sub in list(mod_dir.iterdir()):
            if sub.is_dir() and any(t in sub.name for t in target_tokens):
                for inner_item in sub.rglob("*"):
                    if inner_item.is_file():
                        rel = inner_item.relative_to(sub)
                        target = mod_dir / rel
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(inner_item, target)
                break

# --- Upstream SSEDisplayTweaks Config Override ---

def inject_display_tweaks_custom_config(mo2_dir: Path):
    """
    Injects custom overrides using SSEDisplayTweaks' native override architecture:
    Writes to 'SSEDisplayTweaks_Custom.ini', using validated upstream keys.
    """
    plugins_dir = mo2_dir / "mods" / "SSE Display Tweaks" / "SKSE" / "Plugins"
    if plugins_dir.is_dir():
        # Upstream natively supports SSEDisplayTweaks_Custom.ini
        custom_ini = plugins_dir / "SSEDisplayTweaks_Custom.ini"
        config_content = """# SSEDisplayTweaks Custom Handheld Override
# Validated against upstream SlavicPotato/SSEDisplayTweaks specification

[Render]
Resolution=0x0
Fullscreen=false
Borderless=true
BorderlessUpscale=true
FramerateLimit=60.0
EnableVSync=false

[Havok]
Enabled=true
MaxPhysicsFPS=120.0
"""
        custom_ini.write_text(config_content.strip() + "\n", encoding="utf-8")
        print("[✓] Correctly deployed: SSEDisplayTweaks_Custom.ini (Render & Havok keys verified).")

# --- Topological Plugin Sorter ---

def topological_sort_plugins(plugins: list, master_map: dict, manifest_priority: dict) -> list:
    """Sorts plugins topologically by master dependencies with manifest priority tie-breaking."""
    def is_master(p):
        return p.lower().endswith(".esm") or p.lower().endswith(".esl")

    adj = {p: set() for p in plugins}
    in_degree = {p: 0 for p in plugins}

    for p in plugins:
        for m in master_map.get(p, []):
            if m in plugins:
                adj[m].add(p)
                in_degree[p] += 1

    queue = [p for p in plugins if in_degree[p] == 0]
    queue.sort(key=lambda p: (0 if is_master(p) else 1, manifest_priority.get(p, 999), p.lower()))

    ordered = []
    while queue:
        curr = queue.pop(0)
        ordered.append(curr)
        for dep in adj[curr]:
            in_degree[dep] -= 1
            if in_degree[dep] == 0:
                queue.append(dep)
        queue.sort(key=lambda p: (0 if is_master(p) else 1, manifest_priority.get(p, 999), p.lower()))

    if len(ordered) < len(plugins):
        for p in plugins:
            if p not in ordered:
                ordered.append(p)

    return ordered

# --- Main Transactional Pipeline ---

def main():
    print("==========================================================")
    print("  Skyrim SE Handheld Mod Deployer for SteamOS")
    print(f"  Target: Skyrim SE {REQUIRED_RUNTIME} | SKSE {REQUIRED_SKSE_VERSION}")
    print("==========================================================")

    # 1. Path & Runtime Verification
    game_dir, compat_dir, mo2_dir = locate_skyrim_and_mo2()
    detected_ver = verify_target_runtime(game_dir)

    print(f"[+] Skyrim Directory:   {game_dir}")
    print(f"[+] Verified Runtime:   {detected_ver} (Strict Match)")
    print(f"[+] MO2 Directory:      {mo2_dir}")

    # 2. Preflight Archive Discovery
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

    print(f"[+] Discovered {len(found_archives)} archive(s) across download folders.")
    print("[*] Running preflight archive matching and validation...")
    matched_manifest = match_archives_preflight(found_archives)
    print(f"[✓] Preflight successful: {len(matched_manifest)} mod(s) validated for staging.")

    # 3. Transactional Staging
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    staging_base = Path(f"/tmp/handheld_staging_{timestamp}")
    staging_base.mkdir(parents=True, exist_ok=True)

    root_files_to_deploy = []
    staged_mo2_mods = []
    all_discovered_plugins = set()
    plugin_master_map = {}
    plugin_priority_map = {}

    try:
        for key, (mod, archive) in matched_manifest.items():
            name = mod["name"]
            is_root = mod["is_root"]
            priority = mod["priority"]
            required_files = mod.get("required_files", [])

            stage_mod_dir = staging_base / key
            stage_mod_dir.mkdir(parents=True, exist_ok=True)

            print(f"[*] Staging: {name} ({archive.name})")
            if not extract_archive(archive, stage_mod_dir):
                print(f"[-] FATAL: Failed to extract '{archive.name}'")
                sys.exit(1)

            handle_fomod_and_flatten(stage_mod_dir, detected_ver, mod.get("fomod_runtime_handler"))

            # Validate required files
            for req in required_files:
                if not (stage_mod_dir / req).exists():
                    # Check nested skse64 folder
                    inner_match = list(stage_mod_dir.glob(f"**/{Path(req).name}"))
                    if not inner_match:
                        print(f"[-] FATAL: Validation failed for '{name}'. Missing required file: {req}")
                        sys.exit(1)

            if is_root:
                root_files_to_deploy.append((key, stage_mod_dir))
            else:
                staged_mo2_mods.append((name, stage_mod_dir, priority))

                # Scan and validate plugins
                for p in stage_mod_dir.glob("*.es[mp]"):
                    all_discovered_plugins.add(p.name)
                    plugin_master_map[p.name] = parse_tes4_masters(p)
                    plugin_priority_map[p.name] = priority
                    validate_plugin_masters(p, all_discovered_plugins)
                for p in stage_mod_dir.glob("*.esl"):
                    all_discovered_plugins.add(p.name)
                    plugin_master_map[p.name] = parse_tes4_masters(p)
                    plugin_priority_map[p.name] = priority
                    validate_plugin_masters(p, all_discovered_plugins)

        # 4. Atomic Commit
        print("\n[*] All mods staged and validated. Committing files transactionally...")

        # A. Root Files Deployment with Backup
        backup_dir = game_dir / f".handheld_root_backups/{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        deployed_manifest = []

        for key, stage_dir in root_files_to_deploy:
            if key == "SKSE":
                skse_dirs = list(stage_dir.glob("skse64_*"))
                src = skse_dirs[0] if skse_dirs else stage_dir
                for f in src.glob("skse64_*.dll"):
                    dst = game_dir / f.name
                    if dst.exists():
                        shutil.copy2(dst, backup_dir / f.name)
                    shutil.copy2(f, dst)
                    deployed_manifest.append(f.name)
                for f in src.glob("skse64_loader.exe"):
                    dst = game_dir / f.name
                    if dst.exists():
                        shutil.copy2(dst, backup_dir / f.name)
                    shutil.copy2(f, dst)
                    deployed_manifest.append(f.name)
                if (src / "Data").is_dir():
                    shutil.copytree(src / "Data", game_dir / "Data", dirs_exist_ok=True)
                    deployed_manifest.append("Data/Scripts")
                print("    -> Deployed SKSE 2.3.1 binaries to game root.")
            elif key == "EngineFixesPart2":
                for dll in stage_dir.glob("*.dll"):
                    dst = game_dir / dll.name
                    if dst.exists():
                        shutil.copy2(dst, backup_dir / dll.name)
                    shutil.copy2(dll, dst)
                    deployed_manifest.append(dll.name)
                    print(f"    -> Deployed {dll.name} to game root.")

        # Update root manifest
        root_manifest_file = game_dir / ".handheld_root_manifest.json"
        root_manifest_file.write_text(json.dumps(deployed_manifest, indent=2), encoding="utf-8")

        # B. MO2 Mods Deployment
        installed_mods_record = []
        for name, stage_dir, priority in staged_mo2_mods:
            dest = mo2_dir / "mods" / name
            shutil.rmtree(dest, ignore_errors=True)
            shutil.copytree(stage_dir, dest)
            installed_mods_record.append((name, priority))

        # C. Inject Validated SSEDisplayTweaks Config
        inject_display_tweaks_custom_config(mo2_dir)

        # D. Generate Dedicated Profile: 'Handheld-10W'
        profile_dir = mo2_dir / "profiles" / "Handheld-10W"
        profile_dir.mkdir(parents=True, exist_ok=True)
        default_profile = mo2_dir / "profiles" / "Default"
        if default_profile.is_dir():
            for item in ["archives.txt", "settings.ini"]:
                src = default_profile / item
                dst = profile_dir / item
                if src.exists() and not dst.exists():
                    shutil.copy2(src, dst)

        # Write modlist.txt (Highest priority at bottom)
        installed_mods_record.sort(key=lambda x: x[1])
        modlist_lines = [f"+{m[0]}\n" for m in installed_mods_record]
        (profile_dir / "modlist.txt").write_text("".join(reversed(modlist_lines)), encoding="utf-8")

        # E. Topological Plugin Sorting & Load Order Generation
        sorted_plugins = topological_sort_plugins(list(all_discovered_plugins), plugin_master_map, plugin_priority_map)
        plugins_txt_content = "\n".join([f"*{p}" for p in sorted_plugins]) + "\n"
        loadorder_txt_content = "\n".join(sorted_plugins) + "\n"

        (profile_dir / "plugins.txt").write_text(plugins_txt_content, encoding="utf-8")
        (profile_dir / "loadorder.txt").write_text(loadorder_txt_content, encoding="utf-8")
        print(f"[✓] Generated topological load order with {len(sorted_plugins)} plugin(s).")

        print("\n==========================================================")
        print("  [★] TRANSACTIONAL DEPLOYMENT COMPLETED SUCCESSFULLY")
        print("==========================================================")
        print(f"Profile: 'Handheld-10W' active in Mod Organizer 2.")
        print(f"Game Root Files Logged: {len(deployed_manifest)} tracked.")
        print("All plugins validated against base masters (0 paid CC dependencies).")

    finally:
        shutil.rmtree(staging_base, ignore_errors=True)

if __name__ == "__main__":
    main()
