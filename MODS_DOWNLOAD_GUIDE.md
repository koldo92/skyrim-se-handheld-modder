# Skyrim Special Edition: Handheld 10W / 60 FPS Modding Guide
**Target Devices**: Lenovo Legion Go / Go S, Steam Deck (LCD/OLED), ASUS ROG Ally (SteamOS / Bazzite)  
**Game Version**: Fresh Skyrim SE from Steam (v1.6.1170, Non-AE / No Paid DLCs)  
**Target Performance**: Locked 60 FPS @ 10W TDP (~3.0 – 4.0+ hours battery life, quiet fans)

---

## Quick Start: The 4-Step Workflow

1. **Step 0: Game Preparation**
   * Download Skyrim SE on Steam.
   * Launch it once in SteamOS Game Mode, reach the main menu, and exit. (This creates the Proton prefix `compatdata/489830`).
2. **Step 1: Run Setup Script**
   * Switch to Desktop Mode.
   * Open a terminal in this directory and run:
     ```bash
     ./setup_handheld_skyrim.sh
     # (or ./setup_legion_skyrim.sh)
     ```
   * This configures your low-TDP INIs, verifies paths, installs SKSE64, and prompts to set up Mod Organizer 2 via the Linux installer.
3. **Step 2: Download the Mod Archives**
   * Use the links in the table below to download the mod archives into your `~/Downloads` folder.
   * *(You only need a standard free Nexus account. Click **Manual Download** -> **Slow Download**).*
4. **Step 3: Run the Deploy Script**
   * In your terminal, run:
     ```bash
     python3 deploy_mods.py
     ```
   * This scans `~/Downloads`, extracts all mods into MO2, activates them, generates the load order (`plugins.txt`), and injects 60 FPS / 10W configurations into `DisplayTweaks.ini` and `ShadowBoost.ini`.
5. **Step 4: Play in Game Mode**
   * Return to SteamOS Game Mode and press **Play** on Skyrim SE.

---

## Mod Download List (All Non-AE Compatible)

> [!IMPORTANT]
> **Stick to Main Files Only**:
> * When downloading from Nexus, choose files built for **Skyrim SE 1.6.1170 / Anniversary Edition (Free update)**. None of these mods require the paid Anniversary Edition DLC upgrade.
> * **Do NOT download Optional Files marked "Creation Club Patch" or "CC Addon"** (e.g., on *Mysticism*, *Adamant*, or *Lightened Skyrim*). Those optional patches look for the paid DLCs and will cause missing master errors. Always stick to the **Main Files**.

### 1. Core Engine & Performance (The 10W Lock)

| Mod Name | Nexus Link | Exact File / Notes |
| :--- | :--- | :--- |
| **SKSE64 (v2.2.6)** | [Silverlock Mirror](https://silverlock.org/download/skse/skse64_2_02_06.7z) or [Nexus](https://www.nexusmods.com/skyrimspecialedition/mods/30379) | `skse64_2_02_06.7z` *(Auto-installed by script if connected)* |
| **Address Library for SKSE** | [Nexus #32444](https://www.nexusmods.com/skyrimspecialedition/mods/32444) | **All in one (Anniversary Edition)** |
| **SSE Engine Fixes (Part 1)** | [Nexus #17230](https://www.nexusmods.com/skyrimspecialedition/mods/17230) | **Part 1 SE for 1.6.1170** |
| **SSE Engine Fixes (Part 2)** | [Nexus #17230](https://www.nexusmods.com/skyrimspecialedition/mods/17230) | **Part 2 Engine Fixes - Binaries** *(Deploy script copies these to game root)* |
| **SSE Display Tweaks** | [Nexus #34705](https://www.nexusmods.com/skyrimspecialedition/mods/34705) | Main File *(Pre-configured for 60 FPS lock)* |
| **Shadow Boost** | [Nexus #73133](https://www.nexusmods.com/skyrimspecialedition/mods/73133) | Main File *(Dynamically drops shadow draw calls during load spikes)* |
| **eFPS - Exterior FPS Boost** | [Nexus #54907](https://www.nexusmods.com/skyrimspecialedition/mods/54907) | Main File *(Occlusion planes to cut unseen mesh rendering)* |
| **Lightened Skyrim** | [Nexus #50755](https://www.nexusmods.com/skyrimspecialedition/mods/50755) | Main File *(Removes underground objects and invisible clutter)* |
| **Insignificant Object Remover** | [Nexus #3354](https://www.nexusmods.com/skyrimspecialedition/mods/3354) | Main File *(Removes procedural pebbles/twigs)* |
| **powerofthree's Tweaks** | [Nexus #51073](https://www.nexusmods.com/skyrimspecialedition/mods/51073) | Main File (for 1.6.1170) |
| **powerofthree's Papyrus Extender** | [Nexus #22854](https://www.nexusmods.com/skyrimspecialedition/mods/22854) | Main File (for 1.6.1170) |
| **Bug Fixes SSE** | [Nexus #33261](https://www.nexusmods.com/skyrimspecialedition/mods/33261) | Main File (Anniversary Edition version) |
| **Scrambled Bugs** | [Nexus #43532](https://www.nexusmods.com/skyrimspecialedition/mods/43532) | Main File (for 1.6.1170) |

---

### 2. Handheld Gamepad UI & Quality of Life

| Mod Name | Nexus Link | Exact File / Notes |
| :--- | :--- | :--- |
| **SkyUI 5.2 SE** | [Nexus #12604](https://www.nexusmods.com/skyrimspecialedition/mods/12604) | `SkyUI_5_2_SE.7z` |
| **SkyUI Flashing Savegames Fix** | [Nexus #20406](https://www.nexusmods.com/skyrimspecialedition/mods/20406) | Main File |
| **Auto Input Switch** | [Nexus #54309](https://www.nexusmods.com/skyrimspecialedition/mods/54309) | Main File *(Legion Go trackpad + controller auto-switching)* |
| **Dear Diary Dark Mode** | [Nexus #60837](https://www.nexusmods.com/skyrimspecialedition/mods/60837) | Main File *(High contrast, clean font scaling for 8" screen)* |
| **TrueHUD - HUD Additions** | [Nexus #62775](https://www.nexusmods.com/skyrimspecialedition/mods/62775) | Main File *(Target health bars, boss bars, lock-on)* |
| **Better Dialogue Controls** | [Nexus #1429](https://www.nexusmods.com/skyrimspecialedition/mods/1429) | Main File |
| **Better MessageBox Controls** | [Nexus #1428](https://www.nexusmods.com/skyrimspecialedition/mods/1428) | Main File |
| **Contextual Crosshair** | [Nexus #63980](https://www.nexusmods.com/skyrimspecialedition/mods/63980) | Main File |

---

### 3. Modern Combat & Camera (No MCO / Zero Behavior Tooling)

| Mod Name | Nexus Link | Exact File / Notes |
| :--- | :--- | :--- |
| **True Directional Movement (TDM)** | [Nexus #51614](https://www.nexusmods.com/skyrimspecialedition/mods/51614) | Main File *(360 movement, target lock-on, projectile aim)* |
| **SmoothCam** | [Nexus #41636](https://www.nexusmods.com/skyrimspecialedition/mods/41636) | Main File |
| **Galaduz's SmoothCam Preset** | [Nexus #72014](https://www.nexusmods.com/skyrimspecialedition/mods/72014) | Main File *(Handheld over-the-shoulder responsive camera)* |
| **Precision** | [Nexus #72347](https://www.nexusmods.com/skyrimspecialedition/mods/72347) | Main File *(Physical weapon hitboxes, hit-stop recoil)* |
| **Valhalla Combat** | [Nexus #64741](https://www.nexusmods.com/skyrimspecialedition/mods/64741) | Main File *(Timed parries, poise meter, executions. In-game MCM Tip: under the Stamina tab, you can toggle whether Valhalla or Blade & Blunt controls your stamina)* |
| **Mortal Enemies SE** | [Nexus #4881](https://www.nexusmods.com/skyrimspecialedition/mods/4881) | Main File *(Removes enemy aimbot tracking mid-attack)* |
| **Simple Dual Sheath** | [Nexus #49710](https://www.nexusmods.com/skyrimspecialedition/mods/49710) | Main File *(Shields on back, visible secondary weapons)* |

---

### 4. Battery-Optimized Visuals & Flora (10W Tuning)

| Mod Name | Nexus Link | Exact File / Notes |
| :--- | :--- | :--- |
| **Cathedral Landscapes** | [Nexus #21954](https://www.nexusmods.com/skyrimspecialedition/mods/21954) | **Main File (1K Textures)** *(Faster than vanilla grass!)* |
| **Skyland Architecture (1K)** | [Nexus #3820](https://www.nexusmods.com/skyrimspecialedition/mods/3820) | 1K Texture Pack *(Sharp towns/dungeons without bus choking)* |
| **Cathedral Weathers** | [Nexus #24791](https://www.nexusmods.com/skyrimspecialedition/mods/24791) | Main File *(Crisp lighting with zero FPS drop)* |
| **Community Shaders** | [Nexus #86492](https://www.nexusmods.com/skyrimspecialedition/mods/86492) | Main File *(Replaces battery-draining ENB)* |
| **Simplicity of Snow** | [Nexus #56235](https://www.nexusmods.com/skyrimspecialedition/mods/56235) | Main File |
| **Unofficial HD Audio Project** | [Nexus #18115](https://www.nexusmods.com/skyrimspecialedition/mods/18115) | Music & Voices *(Fixes Bethesda compressed audio)* |

---

### 5. Simonrim Gameplay Balance Suite (Tuxborn Core)

| Mod Name | Nexus Link | Exact File / Notes |
| :--- | :--- | :--- |
| **Mysticism - Magic Overhaul** | [Nexus #27839](https://www.nexusmods.com/skyrimspecialedition/mods/27839) | Main File |
| **Adamant - Perk Overhaul** | [Nexus #30191](https://www.nexusmods.com/skyrimspecialedition/mods/30191) | Main File |
| **Blade & Blunt - Combat** | [Nexus #34549](https://www.nexusmods.com/skyrimspecialedition/mods/34549) | Main File *(AI aggression + stamina flow)* |
| **Aetherius - Race Overhaul** | [Nexus #26686](https://www.nexusmods.com/skyrimspecialedition/mods/26686) | Main File |
| **Mundus - Standing Stones** | [Nexus #33411](https://www.nexusmods.com/skyrimspecialedition/mods/33411) | Main File |
| **Scion - Vampire Overhaul** | [Nexus #41639](https://www.nexusmods.com/skyrimspecialedition/mods/41639) | Main File |
| **Manbeast - Werewolf Overhaul** | [Nexus #44746](https://www.nexusmods.com/skyrimspecialedition/mods/44746) | Main File |
| **Apothecary - Alchemy Overhaul** | [Nexus #52130](https://www.nexusmods.com/skyrimspecialedition/mods/52130) | Main File |
| **Arena - Encounter Zones** | [Nexus #33403](https://www.nexusmods.com/skyrimspecialedition/mods/33403) | Main File |

---

## SteamOS Handheld Settings Checklist

To ensure your Legion Go S stays locked at **60 FPS** at **10W TDP**:

1. **Quick Access Menu (Three-dot button / Legion button)**:
   * **TDP Limit**: Set to **10 Watts**.
   * **Scaling Filter**: Set to **FSR** (Sharpness: **2** or **3**).
   * **Screen Refresh Rate**: Set to **120Hz** or **60Hz**.
2. **In-Game Settings**:
   * Set resolution to **1280x800** (or **1440x900**). SteamOS FSR will upscale it to full native resolution cleanly.
   * Turn Godrays to **Low/Off**.
3. **Enjoy Skyrim**:
   * You get full modern third-person combat (Valhalla parries, Precision weapon physics, TDM lock-on), a clean handheld UI, and ~3.0 to 4.0+ hours of battery life on a single charge!
