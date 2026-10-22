# Skyrim SE Handheld Modding Suite (Steam 1.7.104 / 10W Edition)

[![Platform](https://img.shields.io/badge/Platform-SteamOS%20%7C%20Linux%20%7C%20Bazzite-blue.svg)](#)
[![Game Runtime](https://img.shields.io/badge/Skyrim%20SE-1.7.104%20(Latest%20Steam)-brightgreen.svg)](#)
[![SKSE Version](https://img.shields.io/badge/SKSE64-2.3.1-orange.svg)](#)
[![Anniversary Upgrade](https://img.shields.io/badge/Paid%20AE%20Upgrade-Not%20Required-success.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An automated, battery-optimized modding toolkit for **The Elder Scrolls V: Skyrim Special Edition (Steam Version)** running on Linux handhelds (**Lenovo Legion Go / Go S**, **Steam Deck LCD/OLED**, and **ASUS ROG Ally** via SteamOS or Bazzite).

Delivers a **Tuxborn-like modernized action-RPG experience** targeting the current Steam runtime without requiring the paid Anniversary Edition upgrade, without needing a second Windows PC, and without running complex external animation behavior compilers.

> [!IMPORTANT]
> **Steam Edition Required (Runtime 1.7.104 / SKSE 2.3.1)**:  
> * This toolkit targets the current official **Steam runtime (v1.7.104)** with **SKSE v2.3.1**.  
> * **Terminology Clarification**: SKSE's *"Anniversary Edition build"* label refers purely to the modern executable runtime. Bethesda's paid *"Anniversary Upgrade"* is a separate bundle of 74 Creation Club DLCs. **This project does NOT require the paid upgrade.**  
> * The **GOG** (v1.6.1179), **Epic Games**, and **Xbox / Microsoft Store** editions are **not** supported by this automation.

---

## ⚡ Why This Exists

Most curated Wabbajack modlists (such as *Tuxborn*) enforce strict cryptographic hash matching against all 74 paid Creation Club DLCs from the \$20 Anniversary Edition upgrade. If you only own the base Skyrim Special Edition from Steam, **Wabbajack lists immediately fail to install**.

Furthermore, running Wabbajack natively on SteamOS is notoriously fragile, usually forcing players to mod the game on a Windows desktop and transfer 70+ GB over local networks.

This repository provides:
1. **Current Steam Runtime Target (1.7.104 / SKSE 2.3.1)**: Built specifically for the game version Steam installs today, with automatic binary version detection.
2. **Zero Paid AE Requirement**: Excludes mods and patches that require paid Creation Club files.
3. **Target 60 FPS @ 10W APU Profile**: Configured for extended handheld battery life (~3.0 to 4.0+ hours) with whisper-quiet fans.
4. **No Windows PC Required**: Complete automated deployment performed on-device in Desktop Mode.
5. **Native C++ DLL Combat Core**: Fluid modern combat (*Precision* + *Blade & Blunt* + *True Directional Movement*), avoiding Proton crash loops associated with Java/.NET animation compilers.
6. **Isolated Staging & Dedicated Profile**: Deploys to a dedicated MO2 profile (`Handheld-10W`) without overwriting your `Default` profile, with root files tracked separately in `.handheld_root_manifest.json`.

---

## 🎮 Features & Combat Feel

* **Modern Third-Person Combat**: Full 360° directional movement, responsive target lock-on reticle, physical Havok weapon hitboxes (*Precision*), and tactical combat AI aggression (*Blade & Blunt*).
* **Handheld-Tuned UI**: *Dear Diary Dark Mode* high-contrast interface scaled for 7–8" screens, *MCM Helper*, and *Auto Input Switch (1.7.104 edit)* for seamless trackpad/controller integration.
* **Low-TDP Visuals & Flora**: *Cathedral Landscapes* (which bakes grass textures into terrain meshes to run faster than vanilla grass), *Skyland Architecture 1K*, and *Community Shaders* (configured for Linux / DXVK).
* **Hardware Frame Pacing**: Injected *SSE Display Tweaks* (`SSEDisplayTweaks.ini`) and *Shadow Boost* profiles ensure physics remain stable at 60 FPS or 120 FPS without Havok bugs.

---

## 🚀 Quick Start (4 Steps)

### Step 0: Base Game Preparation
1. Install **Skyrim Special Edition** via Steam.
2. Launch the game **once** in Game Mode until you reach the main menu, then exit.  
   *(This triggers Proton to generate `compatdata/489830` and default graphics registries).*

### Step 1: Run Environment Setup
1. Switch to **Desktop Mode**.
2. Clone this repository:
   ```bash
   git clone https://github.com/koldo92/skyrim-se-handheld-modder.git
   cd skyrim-se-handheld-modder
   chmod +x setup_handheld_skyrim.sh deploy_mods.py
   ```
3. Run the setup script:
   ```bash
   ./setup_handheld_skyrim.sh
   ```
   *This detects your Steam library (SSD or MicroSD), validates your runtime (`1.7.104`), installs SKSE (`2.3.1`), safely merges low-TDP settings into `SkyrimCustom.ini` (with a `.bak` backup), and guides MO2 setup via the maintained [MO2-LINT](https://github.com/Furglitch/modorganizer2-linux-installer) installer.*

### Step 2: Download the Mod Archives
Open your browser in Desktop Mode and download the curated mods into your default `~/Downloads` folder.  
👉 **Follow the [Mod Download Guide (MODS_DOWNLOAD_GUIDE.md)](MODS_DOWNLOAD_GUIDE.md) for direct links and 1.7.104 audit notes.**

*(You only need a free Nexus account. Click **Manual Download** -> **Slow Download**).*

### Step 3: Run the Deploy Script
Once your downloads finish, run:
```bash
python3 deploy_mods.py
```
*The deployer will:*
* Verify runtime 1.7.104 directly from `SkyrimSE.exe`'s PE binary headers.
* Extract all archives to temporary staging, validate files, and select correct 1.7.104 binaries from FOMOD packages (*PO3 Tweaks*, *Papyrus Extender*).
* Deploy Engine Fixes Part 2 binaries to the game root and log them in `.handheld_root_manifest.json`.
* Inject 10W / 60 FPS locked configurations into `SSEDisplayTweaks.ini` and `ShadowBoost.ini`.
* Generate a dedicated MO2 profile (`Handheld-10W`) with pre-sorted, conflict-resolved `modlist.txt`, `plugins.txt`, and `loadorder.txt`.

### Step 4: Play in Game Mode
Return to SteamOS **Game Mode** and launch Skyrim Special Edition!

---

## 🔋 Recommended Power Profiles & Performance

The settings below configure an engineered profile designed to sustain 60 FPS while minimizing APU power consumption:

| Mode | Target Devices | APU TDP Limit | In-Game Resolution | SteamOS FSR | Target Framerate | Real-World Battery |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Eco / Battery Saver** | **All Handhelds** | **9W – 10W** | **800p (1280x800)** | On (Go / Ally)<br>Off (Deck) | **Target: 60 FPS**<br>*(or 45 FPS on Deck)* | **~3.0 – 4.0 Hours**<br>*(4.5+ on OLED / Ally X)* |
| **Balanced (Native)** | **All Handhelds** | **12W – 15W** | **Native Display**<br>(1200p / 1080p / 800p) | Off | **Target: 60 FPS** | **~2.0 – 2.8 Hours** |
| **High Refresh (Docked)** | **Legion Go S / Ally only** | **25W – 30W** | **Native 1200p / 1080p** | Off | **90 – 120 FPS (VRR)**<br>*(Requires INI tweak)* | Plugged into wall |

> [!NOTE]
> **Unlocking 120 FPS for Docked Play**: By default, `deploy_mods.py` configures `SSEDisplayTweaks.ini` with `FramerateLimit = 60.0` for thermal and battery consistency. When playing docked on a 120Hz device, open `mods/SSE Display Tweaks/SKSE/Plugins/SSEDisplayTweaks.ini` and set `FramerateLimit = 120.0`.
>
> **Steam Deck Note**: On the Steam Deck, 800p (1280x800) is the screen's native resolution, so SteamOS FSR should be left **Off**. For maximum battery on Steam Deck OLED, locking the refresh rate to **45Hz / 45 FPS** yields 4.5 to 5+ hours of gameplay.

---

## 📂 Repository Structure

```
├── setup_handheld_skyrim.sh   # Foundation setup, PE version detection, SKSE, INI merge
├── setup_legion_skyrim.sh     # Compatibility alias for Lenovo Legion Go
├── deploy_mods.py             # Manifest engine, FOMOD resolver, atomic deployer
├── MODS_DOWNLOAD_GUIDE.md     # Audited mod list for 1.7.104 with direct Nexus links
├── LICENSE                    # MIT License
└── README.md                  # Project documentation
```

---

## 🛠️ Troubleshooting & FAQ

#### Q: How does this handle Skyrim 1.7.104?
The setup and deployment scripts inspect `SkyrimSE.exe`'s PE binary headers directly. When runtime 1.7.104 is detected, the suite installs matching SKSE v2.3.1 binaries, selects 1.7.104 modules from FOMOD packages, and utilizes Address Library v13.

#### Q: Do I need an animation behavior tool (Nemesis / Pandora)?
**No, not for the core preset.** Full 360° directional movement, target lock-on (*TDM*), responsive camera (*SmoothCam*), and physical Havok weapon hitboxes (*Precision*) are handled entirely by native SKSE C++ DLLs. Optional procedural recoil flinching and headtracking corrections recommend Nemesis, but are omitted to keep the handheld preset 100% crash-free.

#### Q: Why are TrueHUD and Valhalla Combat marked optional?
On runtime 1.7.104, community users have reported startup crashes with TrueHUD and the unofficial Valhalla 1.7.104 port. To guarantee an out-of-the-box working game, they are omitted from the default mandatory preset. *Blade & Blunt + Precision + TDM* provides modern, balanced combat with 100% stability.

#### Q: Does this work with the GOG, Epic Games, or Game Pass editions?
**No.** 
* **GOG**: Uses a different executable version (`1.6.1179`) with different memory offsets, requiring GOG-specific SKSE builds and Heroic/Lutris custom prefixes.
* **Epic Games & PC Game Pass**: These versions have DRM-locked executables that cannot load SKSE64 or native DLL plugins.

---

## 📜 License & Credits

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

* Special thanks to the creators of **Mod Organizer 2**, the **MO2-LINT** team for the maintained Linux installer, **SimonMagus** for the Simonrim suite, **Loki / Ershin** for True Directional Movement, and **Erkeil / Dtry** for modern combat innovations.
