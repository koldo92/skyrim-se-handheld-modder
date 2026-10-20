#!/usr/bin/env python3
"""
deploy_mods.py
Automated Mod Staging & Deployment for Skyrim SE on Lenovo Legion Go S (SteamOS)
Target: 60 FPS Lock @ 10W TDP (Non-AE, No-MCO)
"""

import os
import sys
import re
import shutil
import subprocess
from pathlib import Path

# --- Configuration & Mod Rules ---

# Expected mod specifications: (Short Key, Display Name, Regex Matcher for Archives, IsRootInstall, Priority)
MOD_DEFINITIONS = [
    # Core Engine & Fixes (Highest loading priority)
    ("SKSE", "Skyrim Script Extender 64", r"skse64_.*\.7z", True, 1),
    ("EngineFixesPart2", "Engine Fixes - Part 2 (Binaries)", r"(EngineFixes.*Part2|Engine.*Fixes.*Part.*2).*\.(7z|zip|rar)", True, 2),
    ("AddressLibrary", "Address Library for SKSE Plugins", r"(All in one.*Anniversary|Address.*Library).*\.(7z|zip)", False, 10),
    ("EngineFixes", "SSE Engine Fixes", r"(Part.*1.*Engine.*Fixes|Engine.*Fixes.*Part.*1).*\.(7z|zip)", False, 11),
    ("DisplayTweaks", "SSE Display Tweaks", r"SSE.*Display.*Tweaks.*\.(7z|zip)", False, 12),
    ("ShadowBoost", "Shadow Boost", r"ShadowBoost.*\.(7z|zip)", False, 13),
    ("eFPS", "eFPS - Exterior FPS Boost", r"eFPS.*\.(7z|zip)", False, 14),
    ("LightenedSkyrim", "Lightened Skyrim", r"Lightened.*Skyrim.*\.(7z|zip)", False, 15),
    ("InsignificantObjectRemover", "Insignificant Object Remover", r"Insignificant.*Object.*Remover.*\.(7z|zip)", False, 16),
    ("PO3Tweaks", "powerofthree's Tweaks", r"powerofthree.*Tweaks.*\.(7z|zip)", False, 17),
    ("PO3Papyrus", "powerofthree's Papyrus Extender", r"Papyrus.*Extender.*\.(7z|zip)", False, 18),
    ("BugFixesSSE", "Bug Fixes SSE", r"BugFixesSSE.*\.(7z|zip)", False, 19),
    ("ScrambledBugs", "Scrambled Bugs", r"ScrambledBugs.*\.(7z|zip)", False, 20),

    # UI & Handheld Gamepad
    ("SkyUI", "SkyUI 5.2 SE", r"SkyUI_5_2_SE.*\.(7z|zip)", False, 30),
    ("SkyUIFix", "SkyUI Flashing Savegames Fix", r"Flashing.*Savegames.*Fix.*\.(7z|zip)", False, 31),
    ("AutoInputSwitch", "Auto Input Switch", r"AutoInputSwitch.*\.(7z|zip)", False, 32),
    ("DearDiaryDark", "Dear Diary Dark Mode", r"(Dear.*Diary.*Dark|DearDiaryDark).*\.(7z|zip)", False, 33),
    ("TrueHUD", "TrueHUD - HUD Additions", r"TrueHUD.*\.(7z|zip)", False, 34),
    ("BetterDialogue", "Better Dialogue Controls", r"Better.*Dialogue.*Controls.*\.(7z|zip)", False, 35),
    ("BetterMessageBox", "Better MessageBox Controls", r"Better.*MessageBox.*Controls.*\.(7z|zip)", False, 36),
    ("ContextualCrosshair", "Contextual Crosshair", r"Contextual.*Crosshair.*\.(7z|zip)", False, 37),

    # Combat & Camera
    ("TDM", "True Directional Movement", r"TrueDirectionalMovement.*\.(7z|zip)", False, 40),
    ("SmoothCam", "SmoothCam", r"SmoothCam.*\.(7z|zip)", False, 41),
    ("SmoothCamPreset", "SmoothCam Handheld Preset", r"(Galaduz|ModernCamera|SmoothCam.*Preset).*\.(7z|zip)", False, 42),
    ("Precision", "Precision - Accurate Melee Collisions", r"Precision.*\.(7z|zip)", False, 43),
    ("ValhallaCombat", "Valhalla Combat", r"Valhalla.*Combat.*\.(7z|zip)", False, 44),
    ("MortalEnemies", "Mortal Enemies SE", r"Mortal.*Enemies.*\.(7z|zip)", False, 45),
    ("SimpleDualSheath", "Simple Dual Sheath", r"SimpleDualSheath.*\.(7z|zip)", False, 46),

    # Visuals & Environment (10W Battery Optimized)
    ("CathedralLandscapes", "Cathedral Landscapes (1K)", r"Cathedral.*Landscapes.*\.(7z|zip)", False, 50),
    ("SkylandArch", "Skyland Architecture (1K)", r"Skyland.*Architecture.*\.(7z|zip)", False, 51),
    ("CathedralWeathers", "Cathedral Weathers and Seasons", r"Cathedral.*Weathers.*\.(7z|zip)", False, 52),
    ("CommunityShaders", "Community Shaders", r"CommunityShaders.*\.(7z|zip)", False, 53),
    ("SimplicityOfSnow", "Simplicity of Snow", r"Simplicity.*of.*Snow.*\.(7z|zip)", False, 54),
    ("HD_Audio", "Unofficial High Definition Audio", r"(High.*Definition.*Audio|Audio.*Project).*\.(7z|zip)", False, 55),

    # Simonrim Gameplay Balance Suite
    ("Mysticism", "Mysticism - The Magic Overhaul", r"Mysticism.*\.(7z|zip)", False, 60),
    ("Adamant", "Adamant - A Perk Overhaul", r"Adamant.*\.(7z|zip)", False, 61),
    ("BladeAndBlunt", "Blade & Blunt - A Combat Overhaul", r"(Blade.*and.*Blunt|BladeAndBlunt).*\.(7z|zip)", False, 62),
    ("Aetherius", "Aetherius - A Race Overhaul", r"Aetherius.*\.(7z|zip)", False, 63),
    ("Mundus", "Mundus - A Standing Stone Overhaul", r"Mundus.*\.(7z|zip)", False, 64),
    ("Scion", "Scion - A Vampire Overhaul", r"Scion.*\.(7z|zip)", False, 65),
    ("Manbeast", "Manbeast - A Werewolf Overhaul", r"Manbeast.*\.(7z|zip)", False, 66),
    ("Apothecary", "Apothecary - An Alchemy Overhaul", r"Apothecary.*\.(7z|zip)", False, 67),
    ("Arena", "Arena - An Encounter Zone Overhaul", r"Arena.*\.(7z|zip)", False, 68),
]

def find_steam_and_mo2():
    home = Path.home()
    steam_candidates = [
        home / ".local/share/Steam",
        home / ".steam/steam",
        home / ".steam/root"
    ]
    steam_dir = None
    for cand in steam_candidates:
        if cand.is_dir():
            steam_dir = cand
            break
            
    if not steam_dir:
        print("[-] Error: Steam directory not found.")
        sys.exit(1)

    game_dir = steam_dir / "steamapps/common/Skyrim Special Edition"
    compat_dir = steam_dir / "steamapps/compatdata/489830"
    
    # MO2 can be inside Proton prefix drive_c or standard path
    mo2_candidates = [
        compat_dir / "pfx/drive_c/modorganizer2",
        compat_dir / "pfx/drive_c/ModOrganizer2",
        compat_dir / "pfx/drive_c/users/steamuser/AppData/Local/ModOrganizer",
        home / ".local/share/modorganizer2"
    ]
    mo2_dir = None
    for cand in mo2_candidates:
        if cand.is_dir():
            mo2_dir = cand
            break

    # If rockerbacon installed MO2 in standard location or customized:
    if not mo2_dir:
        # Fallback: create default mo2_dir in prefix
        mo2_dir = compat_dir / "pfx/drive_c/modorganizer2"
        mo2_dir.mkdir(parents=True, exist_ok=True)
        (mo2_dir / "mods").mkdir(exist_ok=True)
        (mo2_dir / "profiles/Default").mkdir(parents=True, exist_ok=True)

    return steam_dir, game_dir, mo2_dir

def extract_archive(archive_path: Path, dest_dir: Path):
    dest_dir.mkdir(parents=True, exist_ok=True)
    # Prefer 7z if available
    if shutil.which("7z"):
        cmd = ["7z", "x", str(archive_path), f"-o{dest_dir}", "-y"]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        return res.returncode == 0
    else:
        # Fallback to python shutil for zip
        try:
            shutil.unpack_archive(str(archive_path), str(dest_dir))
            return True
        except Exception as e:
            print(f"[-] Extraction error on {archive_path.name}: {e}")
            return False

def flatten_mod_directory(mod_dir: Path):
    """If archive extracts to a single nested folder or Data folder, normalize it."""
    items = list(mod_dir.iterdir())
    if len(items) == 1 and items[0].is_dir():
        inner = items[0]
        # If inner is 'Data' or the mod title
        for sub in inner.iterdir():
            shutil.move(str(sub), str(mod_dir))
        inner.rmdir()
    elif (mod_dir / "Data").is_dir():
        data_dir = mod_dir / "Data"
        for sub in data_dir.iterdir():
            shutil.move(str(sub), str(mod_dir))
        data_dir.rmdir()

def deploy_tuned_configs(mo2_dir: Path):
    """Injects 60 FPS / 10W TDP optimized INIs into DisplayTweaks and ShadowBoost."""
    display_tweaks_dir = mo2_dir / "mods" / "SSE Display Tweaks" / "SKSE" / "Plugins"
    if display_tweaks_dir.exists():
        dt_ini = display_tweaks_dir / "DisplayTweaks.ini"
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
        dt_ini.write_text(dt_config)
        print("[✓] Injected 60 FPS locked configuration into SSE Display Tweaks.")

    shadow_boost_dir = mo2_dir / "mods" / "Shadow Boost" / "SKSE" / "Plugins"
    if shadow_boost_dir.exists():
        sb_ini = shadow_boost_dir / "ShadowBoost.ini"
        sb_config = """[General]
TargetFps = 60.0
MinDistance = 1500.0
MaxDistance = 5000.0
"""
        sb_ini.write_text(sb_config)
        print("[✓] Injected dynamic 60 FPS scaling into Shadow Boost.")

def main():
    print("==========================================================")
    print("  Skyrim SE Handheld Mod Deployer for Legion Go S")
    print("  Target: 60 FPS Lock @ 10W TDP")
    print("==========================================================")

    steam_dir, game_dir, mo2_dir = find_steam_and_mo2()
    print(f"[+] Skyrim Directory:   {game_dir}")
    print(f"[+] MO2 Directory:      {mo2_dir}")

    # Search directories for downloaded mod archives
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

    print(f"[+] Found {len(found_archives)} archive(s) in download folders.")

    mods_installed = []
    mods_missing = []

    # Process definitions
    for key, name, pattern, is_root, priority in MOD_DEFINITIONS:
        matched_archive = None
        for arch in found_archives:
            if re.search(pattern, arch.name, re.IGNORECASE):
                matched_archive = arch
                break
        
        if not matched_archive:
            mods_missing.append((name, pattern))
            continue

        print(f"\n[*] Processing: {name} ({matched_archive.name})")

        if is_root:
            # Special case for root installs like Engine Fixes Part 2 or SKSE
            if key == "EngineFixesPart2":
                tmp_extract = Path("/tmp/engine_fixes_p2")
                extract_archive(matched_archive, tmp_extract)
                # Copy DLLs directly into game root
                for dll in tmp_extract.glob("*.dll"):
                    shutil.copy(dll, game_dir)
                    print(f"    -> Deployed {dll.name} to {game_dir}")
                shutil.rmtree(tmp_extract, ignore_errors=True)
            elif key == "SKSE":
                tmp_extract = Path("/tmp/skse_extract")
                extract_archive(matched_archive, tmp_extract)
                skse_inner = list(tmp_extract.glob("skse64_*"))
                src = skse_inner[0] if skse_inner else tmp_extract
                for f in src.glob("skse64_*.dll"):
                    shutil.copy(f, game_dir)
                for f in src.glob("skse64_loader.exe"):
                    shutil.copy(f, game_dir)
                if (src / "Data").is_dir():
                    shutil.copytree(src / "Data", game_dir / "Data", dirs_exist_ok=True)
                shutil.rmtree(tmp_extract, ignore_errors=True)
                print(f"    -> Deployed SKSE binaries to {game_dir}")
        else:
            # Standard MO2 mod extraction
            mod_target_dir = mo2_dir / "mods" / name
            if extract_archive(matched_archive, mod_target_dir):
                flatten_mod_directory(mod_target_dir)
                print(f"    -> Installed to MO2 mods/{name}")

        mods_installed.append((name, priority))

    # Apply performance INI overrides
    deploy_tuned_configs(mo2_dir)

    # Generate MO2 modlist.txt (sorted by priority)
    profile_dir = mo2_dir / "profiles/Default"
    profile_dir.mkdir(parents=True, exist_ok=True)
    modlist_file = profile_dir / "modlist.txt"

    # Sort installed mods by priority
    mods_installed.sort(key=lambda x: x[1])
    
    # In MO2 modlist.txt: lowest priority on top, highest priority at bottom, enabled with '+'
    lines = [f"+{m[0]}\n" for m in mods_installed]
    modlist_file.write_text("".join(reversed(lines)))
    print(f"\n[✓] Generated MO2 modlist.txt with {len(mods_installed)} enabled mod(s).")

    # Generate plugins.txt / loadorder.txt
    plugins_file = profile_dir / "plugins.txt"
    detected_plugins = []
    for mod_name, _ in mods_installed:
        m_dir = mo2_dir / "mods" / mod_name
        if m_dir.is_dir():
            for p in m_dir.glob("*.es[mp]"):
                detected_plugins.append(p.name)
            for p in m_dir.glob("*.esl"):
                detected_plugins.append(p.name)

    plugins_content = "\n".join([f"*{p}" for p in detected_plugins])
    plugins_file.write_text(plugins_content + "\n")
    print(f"[✓] Generated plugins.txt with {len(detected_plugins)} active plugin(s).")

    # Summary
    print("\n==========================================================")
    print(f"  Deployment Summary: {len(mods_installed)} Installed / {len(mods_missing)} Missing")
    print("==========================================================")
    if mods_missing:
        print("\nThe following mods have not yet been downloaded into ~/Downloads:")
        for name, _ in mods_missing:
            print(f"  [ ] {name}")
        print("\nRefer to 'MODS_DOWNLOAD_GUIDE.md' to download them, then re-run this script!")
    else:
        print("\n[★] All mods are installed, ordered, and tuned!")
        print("    You can now boot into Steam Game Mode and launch Skyrim SE.")

if __name__ == "__main__":
    main()
