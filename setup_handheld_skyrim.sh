#!/usr/bin/env bash
# ==============================================================================
# setup_handheld_skyrim.sh
# Setup Script for Modding Skyrim SE on SteamOS Handheld PCs
# (Lenovo Legion Go / Go S, Steam Deck LCD/OLED, ASUS ROG Ally)
# Target: Current Steam Runtime (1.7.104 / SKSE 2.3.1)
# ==============================================================================

set -e

echo "=========================================================="
echo "  Skyrim SE Handheld Modding Setup for SteamOS"
echo "  Target: Current Steam Runtime (1.7.104 / SKSE 2.3.1)"
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

# 4. Detect and Validate SkyrimSE.exe Binary Runtime
echo ""
echo "----------------------------------------------------------"
echo "[*] Detecting SkyrimSE.exe runtime version..."

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
    echo "[!] Warning: Could not detect PE header version from SkyrimSE.exe."
    echo "    Assuming current Steam runtime: 1.7.104"
    DETECTED_VER="1.7.104"
fi

echo "[+] Detected Runtime:        $DETECTED_VER"

SKSE_TARGET_VER=""
SKSE_URL=""
SKSE_DLL_NAME=""

if [ "$DETECTED_VER" = "1.7.104" ]; then
    SKSE_TARGET_VER="2.3.1"
    SKSE_DLL_NAME="skse64_1_7_104.dll"
    SKSE_URL="https://silverlock.org/download/skse/skse64_2_03_01.7z"
elif [ "$DETECTED_VER" = "1.6.1170" ]; then
    SKSE_TARGET_VER="2.2.6"
    SKSE_DLL_NAME="skse64_1_6_1170.dll"
    SKSE_URL="https://silverlock.org/download/skse/skse64_2_02_06.7z"
else
    echo "[-] Error: Unsupported Skyrim SE runtime version detected: $DETECTED_VER"
    echo "    Supported runtimes: 1.7.104 (Current Steam) or 1.6.1170 (Legacy)."
    echo "    Please verify your game files on Steam."
    exit 1
fi

# 5. Check / Install Matching SKSE Version
echo ""
echo "----------------------------------------------------------"
echo "[*] Checking Skyrim Script Extender (Target: SKSE $SKSE_TARGET_VER for $DETECTED_VER)..."

SKSE_VALID=0
if [ -f "$GAME_DIR/$SKSE_DLL_NAME" ] && [ -f "$GAME_DIR/skse64_loader.exe" ]; then
    echo "[✓] Verified matching SKSE binary ($SKSE_DLL_NAME) already present in game directory."
    SKSE_VALID=1
fi

if [ "$SKSE_VALID" -eq 0 ]; then
    echo "[+] Downloading SKSE64 $SKSE_TARGET_VER for runtime $DETECTED_VER..."
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

            cp -f "$SKSE_INNER"/skse64_*.dll "$GAME_DIR/" 2>/dev/null || true
            cp -f "$SKSE_INNER"/skse64_loader.exe "$GAME_DIR/" 2>/dev/null || true
            if [ -d "$SKSE_INNER/Data" ]; then
                mkdir -p "$GAME_DIR/Data"
                cp -rf "$SKSE_INNER/Data/"* "$GAME_DIR/Data/" 2>/dev/null || true
            fi
            echo "[✓] SKSE64 $SKSE_TARGET_VER successfully deployed to $GAME_DIR."
        fi
    fi

    if [ "$EXTRACT_SUCCESS" -ne 1 ]; then
        echo "[!] Note: Could not auto-download or extract SKSE64."
        echo "    Please manually download the archive matching your version and put it in ~/Downloads."
        echo "    deploy_mods.py will install and verify it automatically."
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

# Append or create missing efficiency settings without destroying existing custom bindings
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
        # Check if key is present
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

echo ""
echo "=========================================================="
echo "  Setup Step Complete!"
echo "=========================================================="
echo "Next Steps:"
echo " 1. Consult 'MODS_DOWNLOAD_GUIDE.md' and download the required mods into ~/Downloads."
echo " 2. Run 'python3 deploy_mods.py' to unpack, organize, and activate the 'Handheld-10W' profile."
echo " 3. Launch Skyrim SE in Steam Game Mode!"
echo "=========================================================="
