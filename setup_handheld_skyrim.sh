#!/usr/bin/env bash
# ==============================================================================
# setup_handheld_skyrim.sh
# Setup Script for Modding Skyrim SE on SteamOS Handheld PCs
# (Lenovo Legion Go / Go S, Steam Deck LCD/OLED, ASUS ROG Ally)
# Target: Current Steam Runtime (1.7.104 Strictly) | SKSE 2.3.1
# ==============================================================================

set -e

REQUIRED_RUNTIME="1.7.104"
REQUIRED_SKSE_VER="2.3.1"
REQUIRED_SKSE_DLL="skse64_1_7_104.dll"
SKSE_URL="https://silverlock.org/download/skse/skse64_2_03_01.7z"

echo "=========================================================="
echo "  Skyrim SE Handheld Modding Setup for SteamOS"
echo "  Target: Steam Runtime $REQUIRED_RUNTIME | SKSE $REQUIRED_SKSE_VER"
echo "=========================================================="
echo ""

# 1. Detect Primary Steam Installation
STEAM_DIR=""
for candidate in "$HOME/.local/share/Steam" "$HOME/.steam/steam" "$HOME/.steam/root"; do
    if [ -d "$candidate" ]; then
        STEAM_DIR="$candidate"
        break
    fi
done

if [ -z "$STEAM_DIR" ]; then
    echo "[-] Error: Steam directory not found. Are you running this on SteamOS?"
    exit 1
fi

echo "[+] Primary Steam Directory: $STEAM_DIR"

# 2. Detect All Steam Libraries (Internal SSD + MicroSD Cards)
LIBRARIES=("$STEAM_DIR")
VDF_FILE="$STEAM_DIR/steamapps/libraryfolders.vdf"
if [ -f "$VDF_FILE" ]; then
    while IFS= read -r line; do
        if [[ "$line" =~ \"path\"[[:space:]]+\"([^\"]+)\" ]]; then
            LIB_PATH="${BASH_REMATCH[1]}"
            if [ -d "$LIB_PATH" ] && [[ ! " ${LIBRARIES[*]} " =~ " ${LIB_PATH} " ]]; then
                LIBRARIES+=("$LIB_PATH")
            fi
        fi
    done < "$VDF_FILE"
fi

if [ -d "/run/media" ]; then
    for sub in /run/media/*/*; do
        if [ -d "$sub/steamapps" ] && [[ ! " ${LIBRARIES[*]} " =~ " ${sub} " ]]; then
            LIBRARIES+=("$sub")
        fi
    done
fi

# 3. Locate Game Directory and Proton Prefix
GAME_DIR=""
for lib in "${LIBRARIES[@]}"; do
    if [ -d "$lib/steamapps/common/Skyrim Special Edition" ]; then
        GAME_DIR="$lib/steamapps/common/Skyrim Special Edition"
        break
    fi
done

COMPAT_DIR=""
for lib in "${LIBRARIES[@]}"; do
    if [ -d "$lib/steamapps/compatdata/489830" ]; then
        COMPAT_DIR="$lib/steamapps/compatdata/489830"
        break
    fi
done

if [ -z "$GAME_DIR" ]; then
    echo "[-] Error: 'Skyrim Special Edition' was not found in any Steam library."
    echo "    Libraries checked:"
    for lib in "${LIBRARIES[@]}"; do
        echo "      - $lib"
    done
    echo "    Please verify Skyrim SE is installed via Steam."
    exit 1
fi

if [ -z "$COMPAT_DIR" ] || [ ! -d "$COMPAT_DIR/pfx" ]; then
    echo "[-] Error: Proton prefix not found (compatdata/489830)."
    echo "    CRITICAL STEP: You must launch Skyrim SE in Steam Game Mode ONCE"
    echo "    until you reach the main menu, then exit. This generates the prefix."
    exit 1
fi

PFX_DIR="$COMPAT_DIR/pfx"
echo "[+] Game Directory:          $GAME_DIR"
echo "[+] Proton Prefix:           $PFX_DIR"

# 4. Strictly Detect and Validate SkyrimSE.exe Binary Runtime
echo ""
echo "----------------------------------------------------------"
echo "[*] Verifying SkyrimSE.exe binary runtime..."

DETECTED_VER=$(python3 -c '
import sys, struct
from pathlib import Path
exe = Path(sys.argv[1])
if exe.is_file():
    with open(exe, "rb") as f:
        content = f.read()
    magic = b"\xbd\x04\xef\xfe"
    idx = content.find(magic)
    if idx != -1:
        sig, struc, fv_ms, fv_ls = struct.unpack_from("<IIII", content, idx)
        print(f"{fv_ms >> 16}.{fv_ms & 0xFFFF}.{fv_ls >> 16}")
' "$GAME_DIR/SkyrimSE.exe" 2>/dev/null || true)

if [ -z "$DETECTED_VER" ]; then
    echo "[-] FATAL: Could not read PE version header from SkyrimSE.exe."
    echo "    Refusing to proceed with an unverified game executable."
    exit 1
fi

echo "[+] Detected Runtime:        $DETECTED_VER"

if [ "$DETECTED_VER" != "$REQUIRED_RUNTIME" ]; then
    echo "[-] FATAL: Unsupported Skyrim SE runtime version detected: $DETECTED_VER"
    echo "    This suite strictly targets the current Steam runtime: $REQUIRED_RUNTIME (SKSE $REQUIRED_SKSE_VER)."
    echo "    Please update Skyrim Special Edition via Steam."
    exit 1
fi

# 5. Check / Install Matching SKSE Version
echo ""
echo "----------------------------------------------------------"
echo "[*] Checking Skyrim Script Extender (Target: SKSE $REQUIRED_SKSE_VER for $REQUIRED_RUNTIME)..."

SKSE_VALID=0
if [ -f "$GAME_DIR/$REQUIRED_SKSE_DLL" ] && [ -f "$GAME_DIR/skse64_loader.exe" ]; then
    echo "[✓] Verified matching SKSE binary ($REQUIRED_SKSE_DLL) present in game directory."
    SKSE_VALID=1
fi

if [ "$SKSE_VALID" -eq 0 ]; then
    echo "[+] Downloading SKSE64 $REQUIRED_SKSE_VER for runtime $REQUIRED_RUNTIME..."
    TMP_DIR=$(mktemp -d)
    EXTRACT_SUCCESS=0

    if curl -sSL --fail --connect-timeout 15 "$SKSE_URL" -o "$TMP_DIR/skse.7z"; then
        mkdir -p "$TMP_DIR/extracted"
        if command -v 7z &> /dev/null; then
            7z x "$TMP_DIR/skse.7z" -o"$TMP_DIR/extracted" -y > /dev/null 2>&1 && EXTRACT_SUCCESS=1
        elif command -v 7za &> /dev/null; then
            7za x "$TMP_DIR/skse.7z" -o"$TMP_DIR/extracted" -y > /dev/null 2>&1 && EXTRACT_SUCCESS=1
        elif command -v bsdtar &> /dev/null; then
            bsdtar -xf "$TMP_DIR/skse.7z" -C "$TMP_DIR/extracted" > /dev/null 2>&1 && EXTRACT_SUCCESS=1
        fi

        if [ "$EXTRACT_SUCCESS" -eq 1 ]; then
            SKSE_INNER=$(find "$TMP_DIR/extracted" -type d -name "skse64_*" | head -n 1)
            [ -z "$SKSE_INNER" ] && SKSE_INNER="$TMP_DIR/extracted"

            if cp -f "$SKSE_INNER"/skse64_*.dll "$GAME_DIR/" && cp -f "$SKSE_INNER"/skse64_loader.exe "$GAME_DIR/"; then
                if [ -d "$SKSE_INNER/Data" ]; then
                    mkdir -p "$GAME_DIR/Data"
                    cp -rf "$SKSE_INNER/Data/"* "$GAME_DIR/Data/" || true
                fi
                if [ -f "$GAME_DIR/$REQUIRED_SKSE_DLL" ] && [ -f "$GAME_DIR/skse64_loader.exe" ]; then
                    echo "[✓] SKSE64 $REQUIRED_SKSE_VER successfully deployed and verified in $GAME_DIR."
                    SKSE_VALID=1
                else
                    echo "[-] Warning: SKSE copy completed but expected binary files ($REQUIRED_SKSE_DLL, skse64_loader.exe) were not found."
                fi
            else
                echo "[-] Warning: Failed to copy SKSE files to $GAME_DIR. Check directory permissions."
            fi
        fi
    fi

    if [ "$SKSE_VALID" -ne 1 ]; then
        echo "[!] Note: SKSE64 auto-install was not completed or verified."
        echo "    Please manually download 'skse64_2_03_01.7z' into ~/Downloads."
        echo "    deploy_mods.py will install and verify it during staging."
    fi
    rm -rf "$TMP_DIR"
fi

# 6. Safely Merge / Configure SkyrimCustom.ini (With Backup)
echo ""
echo "----------------------------------------------------------"
echo "[*] Configuring SkyrimCustom.ini for low-TDP efficiency..."

DOCS_DIR=$(find "$PFX_DIR/drive_c/users" -maxdepth 3 -type d -iname "My Games" 2>/dev/null | head -n 1)
if [ -z "$DOCS_DIR" ]; then
    DOCS_DIR="$PFX_DIR/drive_c/users/steamuser/Documents/My Games"
fi

SKYRIM_DOCS="$DOCS_DIR/Skyrim Special Edition"
mkdir -p "$SKYRIM_DOCS"
CUSTOM_INI="$SKYRIM_DOCS/SkyrimCustom.ini"

if [ -f "$CUSTOM_INI" ]; then
    cp "$CUSTOM_INI" "$CUSTOM_INI.bak"
    echo "[+] Backed up existing SkyrimCustom.ini to SkyrimCustom.ini.bak"
fi

python3 -c '
import sys
from pathlib import Path

ini_path = Path(sys.argv[1])
lines = []
if ini_path.is_file():
    lines = ini_path.read_text(encoding="utf-8", errors="ignore").splitlines()

content = "\n".join(lines)

def ensure_section_key(content, section, key, value):
    sec_header = f"[{section}]"
    if sec_header not in content:
        content += f"\n\n{sec_header}\n{key} = {value}"
    else:
        lines = content.splitlines()
        new_lines = []
        in_sec = False
        key_found = False
        for line in lines:
            if line.strip() == sec_header:
                in_sec = True
            elif in_sec and line.strip().startswith("["):
                if not key_found:
                    new_lines.append(f"{key} = {value}")
                    key_found = True
                in_sec = False
            elif in_sec and line.strip().startswith(key):
                line = f"{key} = {value}"
                key_found = True
            new_lines.append(line)
        if in_sec and not key_found:
            new_lines.append(f"{key} = {value}")
        content = "\n".join(new_lines)
    return content

content = ensure_section_key(content, "Grass", "iMinGrassSize", "65")
content = ensure_section_key(content, "Grass", "iMaxGrassTypesPerTexure", "15")
content = ensure_section_key(content, "Display", "bVolumetricLightingEnable", "0")
content = ensure_section_key(content, "Display", "fShadowDistance", "4000.0000")
content = ensure_section_key(content, "General", "bPreemptivelyUnloadCells", "1")

ini_path.write_text(content.strip() + "\n", encoding="utf-8")
' "$CUSTOM_INI"

echo "[✓] Merged efficiency configurations into $CUSTOM_INI."

# 7. Check / Guide MO2 Installation (MO2-LINT Upstream)
echo ""
echo "----------------------------------------------------------"
echo "[*] Checking Mod Organizer 2 Installation..."

MO2_DIR="$COMPAT_DIR/pfx/drive_c/modorganizer2"
if [ -d "$MO2_DIR" ] && [ -f "$MO2_DIR/ModOrganizer.exe" ]; then
    echo "[✓] Mod Organizer 2 is already installed at: $MO2_DIR"
else
    echo "[+] Mod Organizer 2 not detected in Proton prefix."
    echo ""
    echo "    We recommend installing via the maintained MO2-LINT project:"
    echo "    https://github.com/Furglitch/modorganizer2-linux-installer"
    echo ""
    read -p "    Would you like to run the MO2-LINT installer now? [y/N]: " RUN_MO2
    if [[ "$RUN_MO2" =~ ^[Yy]$ ]]; then
        INSTALLER_TMP=$(mktemp -d)
        LINT_URL="https://raw.githubusercontent.com/Furglitch/modorganizer2-linux-installer/master/mo2_installer.sh"
        if curl -sSL --fail "$LINT_URL" -o "$INSTALLER_TMP/mo2_installer.sh"; then
            chmod +x "$INSTALLER_TMP/mo2_installer.sh"
            "$INSTALLER_TMP/mo2_installer.sh"
        else
            echo "[-] Error: Failed to download MO2-LINT installer script."
            echo "    Please visit https://github.com/Furglitch/modorganizer2-linux-installer directly."
        fi
        rm -rf "$INSTALLER_TMP"
    else
        echo "    Skipped MO2 auto-install. You can run it whenever you are ready."
    fi
fi

# 8. Bethesda Patch Freeze Safeguard
echo ""
echo "----------------------------------------------------------"
echo "[*] Bethesda Update Safeguard..."
MANIFEST_FILE=""
for lib in "${LIBRARIES[@]}"; do
    if [ -f "$lib/steamapps/appmanifest_489830.acf" ]; then
        MANIFEST_FILE="$lib/steamapps/appmanifest_489830.acf"
        break
    fi
done

if [ -n "$MANIFEST_FILE" ]; then
    echo "[+] Found Steam AppManifest: $MANIFEST_FILE"
    if [ ! -w "$MANIFEST_FILE" ]; then
        echo "[✓] Manifest is ALREADY write-protected (Read-only). Steam auto-updates are frozen."
    else
        ORIG_PERMS=$(stat -c "%a" "$MANIFEST_FILE" 2>/dev/null || stat -f "%Lp" "$MANIFEST_FILE" 2>/dev/null || echo "644")
        echo "    Bethesda has announced an upcoming Skyrim SE update on Steam."
        echo "    To freeze your working installation on runtime $REQUIRED_RUNTIME and prevent breaking SKSE:"
        echo "    (Note: Locking to read-only stops automatic updates, but Steam may display a"
        echo "     'Disk write error' or paused state when queued. Manual verify will bypass this)."
        read -p "    Lock appmanifest_489830.acf to read-only now? [Y/n]: " FREEZE_CHOICE
        FREEZE_CHOICE="${FREEZE_CHOICE:-Y}"
        if [[ "$FREEZE_CHOICE" =~ ^[Yy]$ ]]; then
            echo "$ORIG_PERMS" > "${MANIFEST_FILE}.orig_mode" 2>/dev/null || true
            chmod 444 "$MANIFEST_FILE"
            echo "[✓] Locked $MANIFEST_FILE (Read-only; original mode: $ORIG_PERMS)."
            echo "    (To unlock and restore permissions later, run: chmod $ORIG_PERMS \"$MANIFEST_FILE\")"
        fi
    fi
fi

# 9. Direct SKSE Auto-Launch (One-Click Play in Game Mode)
echo ""
echo "----------------------------------------------------------"
echo "[*] Direct SKSE Auto-Launch Setup (Bypass MO2 GUI in Game Mode)..."
echo "    To launch directly into Skyrim SE + SKSE when pressing 'Play' in Game Mode:"
echo "    1. In Steam Game Mode: Skyrim Special Edition -> Properties -> General."
echo "    2. Set Launch Options to:"
echo "       %command% \"moshortcut://:SKSE\""
echo "    (When launched, MO2 mounts all mods, boots SKSE, and hides the manager GUI)."

echo ""
echo "=========================================================="
echo "  Setup Step Complete!"
echo "=========================================================="
echo ""
read -p "Do you have a Nexus Mods Premium account? [y/N]: " HAS_PREMIUM
if [[ "$HAS_PREMIUM" =~ ^[Yy]$ ]]; then
    echo ""
    echo "  You can get your Personal API Key from:"
    echo "  https://www.nexusmods.com/users/myaccount?tab=api"
    echo ""
    read -s -p "  Enter your Nexus Personal API Key (input hidden): " USER_NEXUS_KEY
    echo ""
    if [ -n "$USER_NEXUS_KEY" ]; then
        echo ""
        echo "[*] Launching 100% automated Nexus Premium download & deployment..."
        NEXUS_API_KEY="$USER_NEXUS_KEY" python3 deploy_mods.py
        unset USER_NEXUS_KEY
        exit 0
    fi
fi

echo "Next Steps (Free Nexus Account):"
echo " 1. Consult 'MODS_DOWNLOAD_GUIDE.md' and download the required mods into ~/Downloads."
echo " 2. Run 'python3 deploy_mods.py' to unpack, organize, and activate the 'Handheld-10W' profile."
echo " 3. Set the Launch Option above and launch Skyrim SE directly from Steam Game Mode!"
echo "=========================================================="
