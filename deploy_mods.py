#!/usr/bin/env python3
"""
deploy_mods.py
Automated Mod Staging & Deployment for Skyrim SE on SteamOS Handheld PCs
(Lenovo Legion Go / Go S, Steam Deck LCD/OLED, ASUS ROG Ally)
Target: 60 FPS Lock @ 10W TDP (Non-AE, No-MCO)
"""

import os
import sys
import re
import shutil
import subprocess
from pathlib import Path

# --- Mod Definitions & Loading Rules ---

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

def find_steam_libraries():
    """Finds all Steam library folders across internal SSD and MicroSD cards."""
    home = Path.home()
    steam_candidates = [
        home / ".local/share/Steam",
        home / ".steam/steam",
        home / ".steam/root"
    ]
    primary_steam = None
    for cand in steam_candidates:
        if cand.is_dir():
            primary_steam = cand
            break

    if not primary_steam:
        print("[-] Error: Steam installation directory not found.")
        sys.exit(1)

    libraries = [primary_steam]

    # Parse libraryfolders.vdf for MicroSD / external storage
    vdf_path = primary_steam / "steamapps/libraryfolders.vdf"
    if vdf_path.is_file():
        try:
            content = vdf_path.read_text(encoding="utf-8", errors="ignore")
            matches = re.findall(r'"path"\s+"([^"]+)"', content)
            for m in matches:
                p = Path(m)
                if p.is_dir() and p not in libraries:
                    libraries.append(p)
        except Exception:
            pass

    # Check common SteamOS / Legion Go SD card mount points
    media_dir = Path("/run/media")
    if media_dir.is_dir():
        for sub in media_dir.glob("*/*"):
            if sub.is_dir() and (sub / "steamapps").is_dir() and sub not in libraries:
                libraries.append(sub)

    return primary_steam, libraries

def locate_skyrim_and_mo2():
    """Locates Skyrim SE game directory and Proton prefix across all libraries."""
    primary_steam, libraries = find_steam_libraries()

    game_dir = None
    compat_dir = None

    for lib in libraries:
        cand_game = lib / "steamapps/common/Skyrim Special Edition"
        if cand_game.is_dir():
            game_dir = cand_game
            break

    # Compatdata is typically in primary steam, but can be in library
    compat_candidates = [
        primary_steam / "steamapps/compatdata/489830",
    ]
    for lib in libraries:
        cand_pfx = lib / "steamapps/compatdata/489830"
        if cand_pfx not in compat_candidates:
            compat_candidates.append(cand_pfx)

    for cand in compat_candidates:
        if cand.is_dir():
            compat_dir = cand
            break

    if not game_dir:
        print("[-] Error: 'Skyrim Special Edition' not found in any Steam library.")
        print("    Libraries searched:")
        for lib in libraries:
            print(f"      - {lib}")
        sys.exit(1)

    if not compat_dir or not (compat_dir / "pfx").is_dir():
        print("[-] Error: Proton prefix (compatdata/489830) not found.")
        print("    Please launch Skyrim SE once in Game Mode to create the prefix.")
        sys.exit(1)

    # Locate MO2 directory
    mo2_candidates = [
        compat_dir / "pfx/drive_c/modorganizer2",
        compat_dir / "pfx/drive_c/ModOrganizer2",
        compat_dir / "pfx/drive_c/users/steamuser/AppData/Local/ModOrganizer",
        Path.home() / ".local/share/modorganizer2"
    ]
    mo2_dir = None
    for cand in mo2_candidates:
        if cand.is_dir():
            mo2_dir = cand
            break

    if not mo2_dir:
        mo2_dir = compat_dir / "pfx/drive_c/modorganizer2"
        mo2_dir.mkdir(parents=True, exist_ok=True)
        (mo2_dir / "mods").mkdir(exist_ok=True)
        (mo2_dir / "profiles/Default").mkdir(parents=True, exist_ok=True)

    return game_dir, compat_dir, mo2_dir

def extract_archive(archive_path: Path, dest_dir: Path):
    """Extracts an archive securely using native tools (7z, 7za, bsdtar, or zipfile)."""
    dest_dir.mkdir(parents=True, exist_ok=True)

    # 1. Try 7z / 7za
    for tool in ["7z", "7za"]:
        if shutil.which(tool):
            cmd = [tool, "x", str(archive_path), f"-o{dest_dir}", "-y"]
            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            if res.returncode == 0:
                return True

    # 2. Try bsdtar (pre-installed on SteamOS / Arch Linux via libarchive)
    if shutil.which("bsdtar"):
        cmd = ["bsdtar", "-xf", str(archive_path), "-C", str(dest_dir)]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if res.returncode == 0:
            return True

    # 3. Fallback for .zip files via standard library
    if archive_path.suffix.lower() == ".zip":
        try:
            import zipfile
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(dest_dir)
            return True
        except Exception as e:
            print(f"[-] Python zip extraction failed on {archive_path.name}: {e}")
            return False

    print(f"[-] Error: Could not extract '{archive_path.name}'. Please install 'p7zip' or ensure 'bsdtar' is available.")
    return False

def flatten_mod_directory(mod_dir: Path):
    """Ensures mod directories have Data contents (meshes, textures, scripts, plugins) at the root."""
    items = list(mod_dir.iterdir())
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

def deploy_tuned_configs(mo2_dir: Path):
    """Applies tuned INI settings for a locked 60 FPS @ 10W TDP."""
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
        dt_ini.write_text(dt_config, encoding="utf-8")
        print("[✓] Injected 60 FPS locked configuration into SSE Display Tweaks.")

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

def main():
    print("==========================================================")
    print("  Skyrim SE Handheld Mod Deployer for SteamOS")
    print("  Target: 60 FPS Lock @ 10W TDP")
    print("==========================================================")

    game_dir, compat_dir, mo2_dir = locate_skyrim_and_mo2()
    print(f"[+] Skyrim Directory:   {game_dir}")
    print(f"[+] Proton Prefix:      {compat_dir / 'pfx'}")
    print(f"[+] MO2 Directory:      {mo2_dir}")

    # Search locations for downloaded archives
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

    # Process each mod
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
            if key == "EngineFixesPart2":
                tmp_extract = Path("/tmp/engine_fixes_p2")
                if extract_archive(matched_archive, tmp_extract):
                    for dll in tmp_extract.glob("*.dll"):
                        shutil.copy(dll, game_dir)
                        print(f"    -> Deployed {dll.name} to {game_dir}")
                    shutil.rmtree(tmp_extract, ignore_errors=True)
            elif key == "SKSE":
                tmp_extract = Path("/tmp/skse_extract")
                if extract_archive(matched_archive, tmp_extract):
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
            mod_target_dir = mo2_dir / "mods" / name
            if extract_archive(matched_archive, mod_target_dir):
                flatten_mod_directory(mod_target_dir)
                print(f"    -> Installed to MO2 mods/{name}")

        mods_installed.append((name, priority))

    # Apply performance configs
    deploy_tuned_configs(mo2_dir)

    # Generate MO2 modlist.txt
    profile_dir = mo2_dir / "profiles/Default"
    profile_dir.mkdir(parents=True, exist_ok=True)
    modlist_file = profile_dir / "modlist.txt"

    mods_installed.sort(key=lambda x: x[1])
    lines = [f"+{m[0]}\n" for m in mods_installed]
    modlist_file.write_text("".join(reversed(lines)), encoding="utf-8")
    print(f"\n[✓] Generated MO2 modlist.txt with {len(mods_installed)} enabled mod(s).")

    # Generate plugins.txt / loadorder.txt
    plugins_file = profile_dir / "plugins.txt"
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

    plugins_content = "\n".join([f"*{p}" for p in detected_plugins])
    plugins_file.write_text(plugins_content + "\n", encoding="utf-8")
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
