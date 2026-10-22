# Skyrim Special Edition: Handheld 10W / 60 FPS Modding Guide
**Target Devices**: Lenovo Legion Go / Go S, Steam Deck (LCD/OLED), ASUS ROG Ally (SteamOS / Bazzite)  
**Target Game Runtime**: Skyrim SE Latest Steam Runtime (**v1.7.104** / **SKSE v2.3.1**)  
**Anniversary Upgrade Status**: **Not Required** (Zero Paid Creation Club DLCs needed)  
**Target Performance**: Locked 60 FPS Profile @ 10W APU TDP (~3.0 – 4.0+ hours battery life)

---

## ⚠️ Important Clarification: Runtime Version vs. Paid Upgrade

* **The Engine Runtime (v1.7.104)**: When you download Skyrim Special Edition on Steam today, Steam automatically downloads runtime `1.7.104`. SKSE labels its build for this runtime as the *"Anniversary Edition build (v2.3.1)"*. This label refers purely to the **executable version**, **NOT** the paid upgrade.
* **The Paid Anniversary Upgrade**: Bethesda sells a separate bundle of 74 Creation Club creations. **This preset does not use and does not require this paid bundle.** All mods below are configured for the base Steam game.

---

## Quick Start: The 4-Step Workflow

1. **Step 0: Game Preparation**
   * Install Skyrim SE via Steam.
   * Launch the game **once** in SteamOS Game Mode, reach the main menu, and exit.  
     *(This allows Proton to create `compatdata/489830` and default graphics registries).*
2. **Step 1: Run Environment Setup**
   * Switch to **Desktop Mode**.
   * In a terminal, run:
     ```bash
     ./setup_handheld_skyrim.sh
     # (or ./setup_legion_skyrim.sh)
     ```
   * This verifies runtime 1.7.104, installs SKSE 2.3.1, safely merges low-TDP grass settings into `SkyrimCustom.ini` (with automatic backup), and guides MO2 setup via the maintained **MO2-LINT** project.
3. **Step 2: Download the Mod Archives**
   * Download the required mod archives from the tables below into your `~/Downloads` folder using your browser.
4. **Step 3: Run the Deploy Script**
   * In your terminal, run:
     ```bash
     python3 deploy_mods.py
     ```
   * This verifies runtime 1.7.104, runs a preflight check, transactionally stages all archives into a dedicated MO2 profile (`Handheld-10W`), selects 1.7.104 binaries from FOMOD packages, validates plugin masters against paid CC content, injects validated upstream overrides into `SSEDisplayTweaks_Custom.ini`, and builds a topologically sorted load order.
5. **Step 4: Verify Profile & Launch via SKSE**
   * Switch to Desktop Mode or launch Mod Organizer 2.
   * Confirm that the active profile dropdown shows **`Handheld-10W`** and the executable dropdown is set to **`SKSE`**.
   * Launch via SKSE, or switch back to SteamOS Game Mode and launch Skyrim SE via the MO2-configured Steam shortcut!

---

## Mod Download List (Audited for Skyrim 1.7.104)

> [!IMPORTANT]
> **Strictly Download Main Files**:
> * Always download the file updated for **1.7.104** / **SKSE 2.3.1** (or Address Library v13).
> * **Do NOT download optional files marked "Creation Club Patch" or "CC Addon"** (e.g. on Mysticism or Adamant). Those optional patches look for the paid DLCs and will trigger missing-master errors.

### 1. Core Engine & Performance (The 10W Lock)

| Mod Name | Nexus Link | Exact File / 1.7.104 Audit Status |
| :--- | :--- | :--- |
| **SKSE64 (v2.3.1)** | [Silverlock Mirror](https://silverlock.org/download/skse/skse64_2_03_01.7z) or [Nexus #30379](https://www.nexusmods.com/skyrimspecialedition/mods/30379) | `skse64_2_03_01.7z` *(Auto-deployed by setup script if online)* |
| **Address Library for SKSE** | [Nexus #32444](https://www.nexusmods.com/skyrimspecialedition/mods/32444) | **All in one (Anniversary Edition) v13+** *(Verified for 1.7.104)* |
| **SSE Engine Fixes (Part 1)** | [Nexus #17230](https://www.nexusmods.com/skyrimspecialedition/mods/17230) | **Part 1 SE for 1.7.104** |
| **SSE Engine Fixes (Part 2)** | [Nexus #17230](https://www.nexusmods.com/skyrimspecialedition/mods/17230) | **Part 2 Engine Fixes - Binaries** *(Deployer copies these to game root and tracks them in `.handheld_root_manifest.json`)* |
| **SSE Display Tweaks** | [Nexus #34705](https://www.nexusmods.com/skyrimspecialedition/mods/34705) | Main File *(Deployer injects upstream-validated overrides into `SSEDisplayTweaks_Custom.ini` for 60 FPS lock and Havok fix)* |
| **eFPS - Exterior FPS Boost** | [Nexus #54907](https://www.nexusmods.com/skyrimspecialedition/mods/54907) | Main File *(Occlusion planes to cut unseen mesh rendering)* |
| **Lightened Skyrim** | [Nexus #50755](https://www.nexusmods.com/skyrimspecialedition/mods/50755) | Main File *(Removes underground objects and invisible clutter)* |
| **Insignificant Object Remover** | [Nexus #3354](https://www.nexusmods.com/skyrimspecialedition/mods/3354) | Main File *(Removes procedural pebbles/twigs)* |
| **powerofthree's Tweaks** | [Nexus #51073](https://www.nexusmods.com/skyrimspecialedition/mods/51073) | Main File *(FOMOD 1.7.104 binary automatically selected by deployer)* |
| **powerofthree's Papyrus Extender** | [Nexus #22854](https://www.nexusmods.com/skyrimspecialedition/mods/22854) | Main File *(FOMOD 1.7.104 binary automatically selected by deployer)* |
| **Bug Fixes SSE** | [Nexus #33261](https://www.nexusmods.com/skyrimspecialedition/mods/33261) | Main File (Anniversary Edition / 1.7.x version) |
| **Scrambled Bugs** | [Nexus #43532](https://www.nexusmods.com/skyrimspecialedition/mods/43532) | Main File (1.7.x version) |

---

### 2. Handheld Gamepad UI, Controls & Frameworks

| Mod Name | Nexus Link | Exact File / 1.7.104 Audit Status |
| :--- | :--- | :--- |
| **MCM Helper** | [Nexus #53000](https://www.nexusmods.com/skyrimspecialedition/mods/53000) | **Mandatory Framework** *(Required for TDM and Precision Mod Configuration Menus)* |
| **SkyUI 5.2 SE** | [Nexus #12604](https://www.nexusmods.com/skyrimspecialedition/mods/12604) | `SkyUI_5_2_SE.7z` |
| **SkyUI Flashing Savegames Fix** | [Nexus #20406](https://www.nexusmods.com/skyrimspecialedition/mods/20406) | Main File |
| **Auto Input Switch (1.7.104 edit)** | [Nexus #166519](https://www.nexusmods.com/skyrimspecialedition/mods/166519) | **Newer 1.7.104 Compatible Edit** *(Note: Author labels this edit experimental for 1.7.104; verified functional)* |
| **Dear Diary Dark Mode** | [Nexus #60837](https://www.nexusmods.com/skyrimspecialedition/mods/60837) | Main File *(High contrast, clean font scaling for 7-8" screens)* |
| **Better Dialogue Controls** | [Nexus #1429](https://www.nexusmods.com/skyrimspecialedition/mods/1429) | Main File |
| **Better MessageBox Controls** | [Nexus #1428](https://www.nexusmods.com/skyrimspecialedition/mods/1428) | Main File |
| **Contextual Crosshair** | [Nexus #63980](https://www.nexusmods.com/skyrimspecialedition/mods/63980) | Main File |
| **TrueHUD (Optional / Experimental)** | [Nexus #62775](https://www.nexusmods.com/skyrimspecialedition/mods/62775) | *Note: Community reports indicate startup crashes on 1.7.104. Omit if encountering CTD.* |

---

### 3. Modern Combat & Camera (Native C++ DLLs)

> [!NOTE]
> **Behavior Engine Scope (Nemesis / Pandora)**:  
> * **What Works Out-of-the-Box**: Full 360° directional movement, target lock-on, SmoothCam over-the-shoulder tracking, and Havok physical weapon collision hitboxes (*Precision*) work natively via SKSE C++ DLLs without any behavior engine.  
> * **What Requires Nemesis**: Optional procedural recoil flinching in *Precision* and procedural headtracking corrections in *TDM* recommend running Nemesis. For maximum handheld battery and zero Linux setup friction, this preset runs cleanly without an external behavior tool.

| Mod Name | Nexus Link | Exact File / 1.7.104 Audit Status |
| :--- | :--- | :--- |
| **True Directional Movement (TDM)** | [Nexus #51614](https://www.nexusmods.com/skyrimspecialedition/mods/51614) | Main File *(Requires MCM Helper)* |
| **SmoothCam** | [Nexus #41636](https://www.nexusmods.com/skyrimspecialedition/mods/41636) | Main File |
| **Galaduz's SmoothCam Preset** | [Nexus #72014](https://www.nexusmods.com/skyrimspecialedition/mods/72014) | Main File *(Handheld responsive third-person camera)* |
| **Precision - Melee Collisions** | [Nexus #72347](https://www.nexusmods.com/skyrimspecialedition/mods/72347) | Main File *(Havok physical hitboxes. Requires MCM Helper)* |
| **Mortal Enemies SE** | [Nexus #4881](https://www.nexusmods.com/skyrimspecialedition/mods/4881) | Main File *(Removes enemy 360° aimbot tracking mid-attack)* |
| **Simple Dual Sheath** | [Nexus #49710](https://www.nexusmods.com/skyrimspecialedition/mods/49710) | Main File *(Shields on back, visible secondary weapons)* |
| **Valhalla Combat (Optional / Experimental)** | [Nexus #191704](https://www.nexusmods.com/skyrimspecialedition/mods/191704) | *Note: Unofficial 1.7.104 port has crash reports. Omitted from default preset to ensure high stability and avoid startup crashes. Blade & Blunt handles combat balance cleanly.* |

---

### 4. Battery-Optimized Visuals & Flora (10W Tuning)

| Mod Name | Nexus Link | Exact File / 1.7.104 Audit Status |
| :--- | :--- | :--- |
| **Cathedral Landscapes** | [Nexus #21954](https://www.nexusmods.com/skyrimspecialedition/mods/21954) | **Main File (1K Textures)** *(Faster than vanilla grass; bakes grass into terrain meshes)* |
| **Skyland Architecture (1K)** | [Nexus #3820](https://www.nexusmods.com/skyrimspecialedition/mods/3820) | 1K Texture Pack *(Sharp towns/dungeons without memory bus choking)* |
| **Cathedral Weathers** | [Nexus #24791](https://www.nexusmods.com/skyrimspecialedition/mods/24791) | Main File *(Crisp lighting with zero FPS drop)* |
| **Community Shaders** | [Nexus #86492](https://www.nexusmods.com/skyrimspecialedition/mods/86492) | Main File *(Supports 1.7.104 on Linux via DXVK)* |
| **Simplicity of Snow** | [Nexus #56235](https://www.nexusmods.com/skyrimspecialedition/mods/56235) | Main File |
| **Unofficial HD Audio Project** | [Nexus #18115](https://www.nexusmods.com/skyrimspecialedition/mods/18115) | Music & Voices *(Fixes Bethesda compressed audio)* |

---

### 5. Simonrim Gameplay Balance Suite (Conflict-Free Overhaul)

| Mod Name | Nexus Link | Exact File / Notes |
| :--- | :--- | :--- |
| **Mysticism - Magic Overhaul** | [Nexus #27839](https://www.nexusmods.com/skyrimspecialedition/mods/27839) | Main File *(Spells & scaling)* |
| **Adamant - Perk Overhaul** | [Nexus #30191](https://www.nexusmods.com/skyrimspecialedition/mods/30191) | Main File *(Perk trees)* |
| **Blade & Blunt - Combat** | [Nexus #34549](https://www.nexusmods.com/skyrimspecialedition/mods/34549) | Main File *(Enemy AI aggression, stamina flow, attack commitment)* |
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
   * You get full modern third-person combat (Precision weapon physics, TDM lock-on, Blade & Blunt AI), a clean handheld UI, and ~3.0 to 4.0+ hours of battery life on a single charge!

---

## 📊 Verification & Compatibility Audit (October 22, 2026)

* **Game Runtime**: Skyrim Special Edition `1.7.104` (Steam)
* **Script Extender**: SKSE64 `2.3.1` (Build `skse64_2_03_01.7z`)
* **Address Library**: v13+ (Supporting 1.7.104)
* **Proton Layer**: Proton Experimental / GE-Proton
* **Validation Suite**: Automated unit tests (`tests/test_suite.py`) verified for PE version parsing, TES4 master validation (0 paid CC masters), preflight ambiguity detection, and SSEDisplayTweaks key validation.
* **Performance Framing**: 60 FPS and battery estimates (~3.0–4.0h) represent an **engineered target profile** based on 10W APU scaling and optimized asset budgets. The script configures in-game INI settings; users configure the SteamOS TDP slider manually.
