#!/usr/bin/env bash
# ==============================================================================
# setup_legion_skyrim.sh
# Setup Script for Modding Skyrim SE on Lenovo Legion Go S (SteamOS)
# Target: Skyrim SE (1.6.1170, non-AE), 60 FPS Lock @ 10W TDP
# ==============================================================================

set -e

echo "=========================================================="
echo "  Skyrim SE Handheld Modding Setup for Legion Go S"
echo "  Target: Locked 60 FPS @ 10W TDP (Non-AE, No-MCO)"
echo "=========================================================="
echo ""

# 1. Detect Steam and Skyrim SE paths
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

GAME_DIR="$STEAM_DIR/steamapps/common/Skyrim Special Edition"
COMPAT_DIR="$STEAM_DIR/steamapps/compatdata/489830"
PFX_DIR="$COMPAT_DIR/pfx"

echo "[+] Steam Directory:   $STEAM_DIR"
echo "[+] Game Directory:    $GAME_DIR"
echo "[+] Proton Prefix:     $PFX_DIR"
echo ""

if [ ! -d "$GAME_DIR" ]; then
    echo "[-] Error: Skyrim Special Edition is not installed at:"
    echo "    $GAME_DIR"
    echo "    Please install the game via Steam before running this script."
    exit 1
fi

if [ ! -d "$PFX_DIR" ]; then
    echo "[-] Error: Proton prefix not found at $PFX_DIR."
    echo "    CRITICAL STEP: You must launch Skyrim SE in Steam Game Mode ONCE"
    echo "    until you reach the main menu, then exit. This generates the prefix."
    exit 1
fi

echo "[✓] Skyrim SE installation and Proton prefix verified."
echo ""

# 2. Check and Install SKSE64 (v2.2.6 for Skyrim SE 1.6.1170)
echo "----------------------------------------------------------"
echo "[*] Checking Skyrim Script Extender 64 (SKSE64)..."
SKSE_EXE="$GAME_DIR/skse64_loader.exe"

if [ -f "$SKSE_EXE" ]; then
    echo "[✓] SKSE64 loader already present in game directory."
else
    echo "[+] Downloading SKSE64 build 2.2.6 (for runtime 1.6.1170)..."
    TMP_DIR=$(mktemp -d)
    SKSE_URL="https://silverlock.org/download/skse/skse64_2_02_06.7z"
    
    # Try downloading from primary mirror, fallback to github release archive if needed
    if curl -sSL --fail "$SKSE_URL" -o "$TMP_DIR/skse.7z"; then
        echo "[+] Extracting SKSE64..."
        7z x "$TMP_DIR/skse.7z" -o"$TMP_DIR/extracted" > /dev/null
        
        SKSE_INNER=$(find "$TMP_DIR/extracted" -type d -name "skse64_2_02_06" | head -n 1)
        if [ -d "$SKSE_INNER" ]; then
            cp -r "$SKSE_INNER"/skse64_*.dll "$GAME_DIR/"
            cp -r "$SKSE_INNER"/skse64_loader.exe "$GAME_DIR/"
            mkdir -p "$GAME_DIR/Data"
            cp -r "$SKSE_INNER/Data/"* "$GAME_DIR/Data/"
            echo "[✓] SKSE64 installed successfully into $GAME_DIR."
        fi
    else
        echo "[!] Note: Could not auto-download SKSE64 from silverlock.org (network timeout or offline)."
        echo "    Please download 'skse64_2_02_06.7z' manually and put it into ~/Downloads."
        echo "    deploy_mods.py will install it automatically."
    fi
    rm -rf "$TMP_DIR"
fi

# 3. Configure SkyrimCustom.ini for 10W TDP / 60 FPS in Proton Prefix
echo ""
echo "----------------------------------------------------------"
echo "[*] Configuring Skyrim INI for low-TDP efficiency..."
MY_GAMES_DIR="$PFX_DIR/drive_c/users/steamuser/Documents/My Games/Skyrim Special Edition"
mkdir -p "$MY_GAMES_DIR"

CUSTOM_INI="$MY_GAMES_DIR/SkyrimCustom.ini"
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

# 4. Check / Guide Mod Organizer 2 Linux Installer
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
