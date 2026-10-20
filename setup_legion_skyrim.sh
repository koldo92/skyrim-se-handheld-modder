#!/usr/bin/env bash
# ==============================================================================
# setup_handheld_skyrim.sh
# Setup Script for Modding Skyrim SE on SteamOS Handheld PCs
# (Lenovo Legion Go / Go S, Steam Deck LCD/OLED, ASUS ROG Ally)
# Target: Skyrim SE (1.6.1170, non-AE), 60 FPS Lock @ 10W TDP
# ==============================================================================

set -e

echo "=========================================================="
echo "  Skyrim SE Handheld Modding Setup for SteamOS"
echo "  Target: Locked 60 FPS @ 10W TDP (Non-AE, No-MCO)"
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

# Check libraryfolders.vdf
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

# Check common MicroSD card mount points
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
echo "[✓] Installation paths verified."
echo ""

# 4. Check and Install SKSE64 (v2.2.6 for Skyrim SE 1.6.1170)
echo "----------------------------------------------------------"
echo "[*] Checking Skyrim Script Extender 64 (SKSE64)..."
SKSE_EXE="$GAME_DIR/skse64_loader.exe"

if [ -f "$SKSE_EXE" ]; then
    echo "[✓] SKSE64 loader is already present in the game directory."
else
    echo "[+] Downloading SKSE64 build 2.2.6 (for runtime 1.6.1170)..."
    TMP_DIR=$(mktemp -d)
    SKSE_URL="https://silverlock.org/download/skse/skse64_2_02_06.7z"

    EXTRACT_SUCCESS=0
    if curl -sSL --fail --connect-timeout 15 "$SKSE_URL" -o "$TMP_DIR/skse.7z"; then
        echo "[+] Extracting SKSE64..."
        mkdir -p "$TMP_DIR/extracted"

        if command -v 7z &> /dev/null; then
            7z x "$TMP_DIR/skse.7z" -o"$TMP_DIR/extracted" -y > /dev/null 2>&1 && EXTRACT_SUCCESS=1
        elif command -v 7za &> /dev/null; then
            7za x "$TMP_DIR/skse.7z" -o"$TMP_DIR/extracted" -y > /dev/null 2>&1 && EXTRACT_SUCCESS=1
        elif command -v bsdtar &> /dev/null; then
            bsdtar -xf "$TMP_DIR/skse.7z" -C "$TMP_DIR/extracted" > /dev/null 2>&1 && EXTRACT_SUCCESS=1
        fi

        if [ "$EXTRACT_SUCCESS" -eq 1 ]; then
            SKSE_INNER=$(find "$TMP_DIR/extracted" -type d -name "skse64_2_02_06" | head -n 1)
            [ -z "$SKSE_INNER" ] && SKSE_INNER="$TMP_DIR/extracted"

            cp -r "$SKSE_INNER"/skse64_*.dll "$GAME_DIR/" 2>/dev/null || true
            cp -r "$SKSE_INNER"/skse64_loader.exe "$GAME_DIR/" 2>/dev/null || true
            if [ -d "$SKSE_INNER/Data" ]; then
                mkdir -p "$GAME_DIR/Data"
                cp -r "$SKSE_INNER/Data/"* "$GAME_DIR/Data/" 2>/dev/null || true
            fi
            echo "[✓] SKSE64 successfully installed into $GAME_DIR."
        fi
    fi

    if [ "$EXTRACT_SUCCESS" -ne 1 ]; then
        echo "[!] Note: Could not auto-download or extract SKSE64."
        echo "    Please download 'skse64_2_02_06.7z' manually into ~/Downloads."
        echo "    deploy_mods.py will install it automatically."
    fi
    rm -rf "$TMP_DIR"
fi

# 5. Configure SkyrimCustom.ini for 10W TDP / 60 FPS in Proton Prefix
echo ""
echo "----------------------------------------------------------"
echo "[*] Configuring Skyrim INI for low-TDP efficiency..."

# Case-insensitive search for My Games directory in Proton prefix
DOCS_DIR=$(find "$PFX_DIR/drive_c/users" -maxdepth 3 -type d -iname "My Games" 2>/dev/null | head -n 1)
if [ -z "$DOCS_DIR" ]; then
    DOCS_DIR="$PFX_DIR/drive_c/users/steamuser/Documents/My Games"
fi

SKYRIM_DOCS="$DOCS_DIR/Skyrim Special Edition"
mkdir -p "$SKYRIM_DOCS"

CUSTOM_INI="$SKYRIM_DOCS/SkyrimCustom.ini"
cat << 'EOF' > "$CUSTOM_INI"
[Grass]
; Density optimized for 10W TDP lock with Cathedral Landscapes
iMinGrassSize = 65
iMaxGrassTypesPerTexure = 15

[Display]
; Save draw calls and bandwidth on handheld
bVolumetricLightingEnable = 0
fShadowDistance = 4000.0000

[General]
bPreemptivelyUnloadCells = 1
EOF

echo "[✓] Created optimized $CUSTOM_INI."

# 6. Check / Guide Mod Organizer 2 Linux Installer
echo ""
echo "----------------------------------------------------------"
echo "[*] Checking Mod Organizer 2 Installation..."

MO2_DIR="$COMPAT_DIR/pfx/drive_c/modorganizer2"
if [ -d "$MO2_DIR" ]; then
    echo "[✓] Mod Organizer 2 is already installed at: $MO2_DIR"
else
    echo "[+] Mod Organizer 2 is not yet installed in this Proton prefix."
    echo ""
    echo "    We recommend the automated community installer by rockerbacon:"
    echo "    https://github.com/rockerbacon/modorganizer2-linux-installer"
    echo ""
    read -p "    Would you like to run the rockerbacon MO2 installer now? [y/N]: " RUN_MO2
    if [[ "$RUN_MO2" =~ ^[Yy]$ ]]; then
        INSTALLER_TMP=$(mktemp -d)
        curl -sSL "https://raw.githubusercontent.com/rockerbacon/modorganizer2-linux-installer/master/mo2_installer.sh" -o "$INSTALLER_TMP/mo2_installer.sh"
        chmod +x "$INSTALLER_TMP/mo2_installer.sh"
        "$INSTALLER_TMP/mo2_installer.sh"
        rm -rf "$INSTALLER_TMP"
    else
        echo "    Skipped MO2 auto-install. You can run it whenever you're ready."
    fi
fi

echo ""
echo "=========================================================="
echo "  Foundation Setup Complete!"
echo "=========================================================="
echo "Next Steps:"
echo " 1. Open 'MODS_DOWNLOAD_GUIDE.md' and download the mod archives into ~/Downloads."
echo " 2. Run 'python3 deploy_mods.py' to unpack, organize, and activate all mods in MO2."
echo " 3. Launch the game in Steam Game Mode at 60 FPS!"
echo "=========================================================="
