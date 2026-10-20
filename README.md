# Skyrim SE Handheld Modding Suite (Non-AE / 10W Edition)

[![Platform](https://img.shields.io/badge/Platform-SteamOS%20%7C%20Linux%20%7C%20Bazzite-blue.svg)](#)
[![Game Version](https://img.shields.io/badge/Skyrim%20SE-1.6.1170%20(Steam)-brightgreen.svg)](#)
[![Target Performance](https://img.shields.io/badge/Target-60%20FPS%20%40%2010W%20TDP-orange.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An automated, battery-optimized modding toolkit for **The Elder Scrolls V: Skyrim Special Edition** running on Linux handhelds (**Lenovo Legion Go / Go S**, **Steam Deck LCD/OLED**, and **ASUS ROG Ally** via SteamOS or Bazzite).

Delivers a **Tuxborn-like modernized action-RPG experience** without requiring the paid Anniversary Edition upgrade, without needing a second Windows PC, and without running complex external animation behavior compilers.

---

## ⚡ Why This Exists

Most curated Wabbajack modlists (such as *Tuxborn*) enforce strict cryptographic hash matching against all 74 paid Creation Club DLCs from the \$20 Anniversary Edition upgrade. If you only own the base Skyrim Special Edition from Steam (which includes the free 1.6.x update and 4 free CC creations), **Wabbajack lists immediately fail to install**.

Furthermore, running Wabbajack natively on SteamOS is notoriously difficult, usually forcing players to mod the game on a Windows desktop and transfer 70+ GB over local networks.

This repository provides:
1. **Zero Paid AE Requirement**: Built specifically for standard Skyrim SE (Steam version `1.6.1170`).
2. **Locked 60 FPS @ 10W APU TDP**: Delivers **3.5 to 4.5+ hours of battery life** with whisper-quiet fans on Z1 Extreme / Van Gogh APUs.
3. **No Windows PC Required**: Perform the entire installation on-device in Desktop Mode.
4. **No External Behavior Tools (No MCO / Nemesis)**: Uses 100% native SKSE C++ DLLs for modern combat (*Valhalla Combat* + *Precision* + *True Directional Movement*), eliminating Proton crash risks associated with Java/.NET animation generators.
5. **One-Command Auto-Staging**: Download mod archives into `~/Downloads`, run `deploy_mods.py`, and your Mod Organizer 2 profile, plugins, load order, and low-TDP INIs are configured automatically.

---

## 🎮 Features & Combat Feel

* **Modern Third-Person Combat**: Full 360° directional movement, responsive target lock-on reticle, physical Havok weapon hitboxes (*Precision*), timed parrying, poise/stagger meters, and execution finishers (*Valhalla Combat*).
* **Handheld-Tuned UI**: *Dear Diary Dark Mode* high-contrast interface scaled for 7–8" screens, *TrueHUD* floating boss/enemy health bars, and *Auto Input Switch* for seamless trackpad/controller integration.
* **Low-TDP Visuals & Flora**: *Cathedral Landscapes* (which bakes grass textures into terrain meshes to run faster than vanilla grass), *Skyland Architecture 1K*, and *Community Shaders* (replaces battery-draining ENB).
* **Hardware Frame Pacing**: Injected *SSE Display Tweaks* and *Shadow Boost* profiles ensure physics remain stable at 60 FPS or 120 FPS without Havok bugs.

---

## 🚀 Quick Start (4 Steps)

### Step 0: Base Game Preparation
1. Install **Skyrim Special Edition** via Steam.
2. Launch the game **once** in Game Mode until you reach the main menu, then exit.  
   *(This triggers Proton to generate `compatdata/489830` and default graphics registries).*

### Step 1: Run the Environment Setup
1. Switch to **Desktop Mode**.
2. Clone this repository or download the scripts:
   ```bash
   git clone https://github.com/YOUR_USERNAME/skyrim-se-handheld-modder.git
   cd skyrim-se-handheld-modder
   chmod +x setup_handheld_skyrim.sh deploy_mods.py
   ```
3. Run the setup script:
   ```bash
   ./setup_handheld_skyrim.sh
   ```
   *This automatically detects Steam paths, verifies the Proton prefix, installs SKSE64 (v2.2.6), applies low-power grass and shadow settings to `SkyrimCustom.ini`, and sets up Mod Organizer 2 via the Linux installer.*

### Step 2: Download the Mod Archives
Open your browser in Desktop Mode and download the 35 curated mods into your default `~/Downloads` folder.  
👉 **Follow the [Mod Download Guide (MODS_DOWNLOAD_GUIDE.md)](MODS_DOWNLOAD_GUIDE.md) for direct links and exact file selections.**

*(You only need a free Nexus account. Click **Manual Download** -> **Slow Download**).*

### Step 3: Run the Deploy Script
Once your downloads finish, run:
```bash
python3 deploy_mods.py
```
*The deployer will:*
* Automatically detect and extract all archives into MO2.
* Copy Engine Fixes Part 2 binaries directly to the game root.
* Inject 10W / 60 FPS locked configurations into `DisplayTweaks.ini` and `ShadowBoost.ini`.
* Generate pre-sorted, conflict-resolved `modlist.txt` and `plugins.txt`.

### Step 4: Play in Game Mode
Return to SteamOS **Game Mode** and launch Skyrim Special Edition!

---

## 🔋 Recommended Power Profiles

| Mode | TDP Limit | In-Game Resolution | SteamOS FSR | Framerate Target | Expected Battery Life |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Eco / Handheld Mode** | **10 Watts** | 800p (1280x800) / 900p | Sharpness: 2 or 3 | **Locked 60 FPS** | **~3.5 – 4.5+ Hours** |
| **Balanced Mode** | **15 Watts** | Native 1080p / 1200p | Off / Minimal | **Locked 60 FPS** | **~2.5 – 3.0 Hours** |
| **Docked / 120Hz High-Refresh** | **25W – 30W** | Native 1080p / 1200p | Off | **90 – 120 FPS (VRR)** | Plugged into wall |

---

## 📂 Repository Structure

```
├── setup_handheld_skyrim.sh   # Foundation setup, path detection, SKSE64, INI tuning
├── setup_legion_skyrim.sh     # Compatibility alias for Lenovo Legion Go
├── deploy_mods.py             # Archive parser, MO2 unpacker, load order builder
├── MODS_DOWNLOAD_GUIDE.md     # Complete mod list with direct Nexus download links
├── LICENSE                    # MIT License
└── README.md                  # Project documentation
```

---

## 🛠️ Troubleshooting & FAQ

#### Q: Do I need Nexus Premium?
**No.** All mods can be downloaded with a standard free Nexus account. `deploy_mods.py` takes the raw archives from your `~/Downloads` folder and handles the extraction, folder restructuring, and load ordering for you.

#### Q: Will this break my vanilla save?
We recommend starting a new playthrough. The Simonrim gameplay overhauls (*Adamant*, *Mysticism*, *Blade & Blunt*) modernize perk trees, spells, and standing stones from level 1.

#### Q: Can I run this at 120 FPS on my Legion Go S?
Yes! `SSE Display Tweaks` dynamically calculates Havok physics per frame. If you are plugged into power and set your TDP to 25W–30W, the game will run smoothly up to 120 FPS.

---

## 📜 License & Credits

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

* Special thanks to the creators of **Mod Organizer 2**, **rockerbacon** for the Linux MO2 wrapper, **SimonMagus** for the Simonrim suite, **Loki / Ershin** for True Directional Movement and TrueHUD, and **Dtry** for Valhalla Combat.
