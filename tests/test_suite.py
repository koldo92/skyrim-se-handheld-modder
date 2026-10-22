#!/usr/bin/env python3
"""
tests/test_suite.py
Automated Verification & Unit Tests for Skyrim SE Handheld Modder Suite
Target: Steam Game Runtime 1.7.104 | SKSE 2.3.1
"""

import unittest
import struct
import tempfile
import shutil
from pathlib import Path

# Import functions and definitions from deploy_mods
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from deploy_mods import (
    get_pe_file_version,
    parse_tes4_masters,
    validate_plugin_masters,
    topological_sort_plugins,
    match_archives_preflight,
    activate_mo2_profile,
    inject_display_tweaks_custom_config,
    tune_engine_fixes_config,
    handle_fomod_and_flatten,
    prune_old_backups,
    freeze_steam_manifest,
    check_steam_manifest_frozen,
    create_direct_launch_wrapper,
    ALLOWED_BASE_MASTERS,
    REQUIRED_RUNTIME,
    REQUIRED_SKSE_DLL,
    MOD_MANIFEST
)

class TestHandheldSuite(unittest.TestCase):

    def test_pe_header_version_detection(self):
        """Verifies accurate extraction of Windows PE FileVersion from VS_FIXEDFILEINFO."""
        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as f:
            # Build synthetic VS_FIXEDFILEINFO (magic: 0xFEEF04BD, major: 1, minor: 7, build: 104, rev: 0)
            magic = 0xFEEF04BD
            struc = 0x00010000
            fv_ms = (1 << 16) | 7
            fv_ls = (104 << 16) | 0
            binary = b"\x00" * 128 + struct.pack("<IIII", magic, struc, fv_ms, fv_ls) + b"\x00" * 64
            f.write(binary)
            temp_path = Path(f.name)

        try:
            ver = get_pe_file_version(temp_path)
            self.assertEqual(ver, "1.7.104.0")
        finally:
            temp_path.unlink()

    def test_tes4_master_parsing(self):
        """Verifies binary extraction of plugin masters (MAST subrecords) from a TES4 header."""
        mast1 = b"Skyrim.esm\x00"
        sub1 = b"MAST" + struct.pack("<H", len(mast1)) + mast1
        mast2 = b"ccbgssse001-fish.esm\x00"
        sub2 = b"MAST" + struct.pack("<H", len(mast2)) + mast2
        data = sub1 + sub2
        header = b"TES4" + struct.pack("<I", len(data)) + (b"\x00" * 16)
        synth_plugin = header + data

        with tempfile.NamedTemporaryFile(suffix=".esp", delete=False) as f:
            f.write(synth_plugin)
            temp_path = Path(f.name)

        try:
            masters = parse_tes4_masters(temp_path)
            self.assertEqual(masters, ["Skyrim.esm", "ccbgssse001-fish.esm"])
            for m in masters:
                self.assertIn(m.lower(), ALLOWED_BASE_MASTERS)
        finally:
            temp_path.unlink()

    def test_validate_plugin_masters_enforcement(self):
        """Verifies that validate_plugin_masters rejects unowned CC DLCs and missing ordinary masters."""
        # Case A: Plugin requiring unauthorized paid Creation Club DLC
        mast_paid = b"ccbgssse002-exoticpets.esl\x00"
        sub_paid = b"MAST" + struct.pack("<H", len(mast_paid)) + mast_paid
        header_paid = b"TES4" + struct.pack("<I", len(sub_paid)) + (b"\x00" * 16)

        with tempfile.NamedTemporaryFile(suffix=".esp", delete=False) as f:
            f.write(header_paid + sub_paid)
            temp_paid = Path(f.name)

        try:
            # Must abort on paid CC master
            with self.assertRaises(SystemExit):
                validate_plugin_masters(temp_paid, {"SkyUI_SE.esp"})
        finally:
            temp_paid.unlink()

        # Case B: Plugin requiring an ordinary master that is missing from active plugins
        mast_missing = b"MissingRequiredMaster.esm\x00"
        sub_missing = b"MAST" + struct.pack("<H", len(mast_missing)) + mast_missing
        header_missing = b"TES4" + struct.pack("<I", len(sub_missing)) + (b"\x00" * 16)

        with tempfile.NamedTemporaryFile(suffix=".esp", delete=False) as f:
            f.write(header_missing + sub_missing)
            temp_missing = Path(f.name)

        try:
            # Must abort on missing master
            with self.assertRaises(SystemExit):
                validate_plugin_masters(temp_missing, {"SkyUI_SE.esp"})
        finally:
            temp_missing.unlink()

        # Case C: Plugin requiring base game master and an active mod -> must succeed
        mast_ok1 = b"Skyrim.esm\x00"
        sub_ok1 = b"MAST" + struct.pack("<H", len(mast_ok1)) + mast_ok1
        mast_ok2 = b"SkyUI_SE.esp\x00"
        sub_ok2 = b"MAST" + struct.pack("<H", len(mast_ok2)) + mast_ok2
        data_ok = sub_ok1 + sub_ok2
        header_ok = b"TES4" + struct.pack("<I", len(data_ok)) + (b"\x00" * 16)

        with tempfile.NamedTemporaryFile(suffix=".esp", delete=False) as f:
            f.write(header_ok + data_ok)
            temp_ok = Path(f.name)

        try:
            # Should not raise
            validate_plugin_masters(temp_ok, {"SkyUI_SE.esp"})
        finally:
            temp_ok.unlink()

    def test_topological_sort_preserves_master_order(self):
        """Verifies that topological sort guarantees masters precede dependent plugins."""
        plugins = ["Adamant.esp", "SkyUI_SE.esp", "eFPS - Official.esp", "Mundus.esp"]
        master_map = {
            "Adamant.esp": ["SkyUI_SE.esp"],
            "Mundus.esp": ["Adamant.esp"]
        }
        priority_map = {
            "SkyUI_SE.esp": 30,
            "Adamant.esp": 61,
            "eFPS - Official.esp": 14,
            "Mundus.esp": 64
        }
        sorted_order = topological_sort_plugins(plugins, master_map, priority_map)
        
        # SkyUI must precede Adamant
        self.assertLess(sorted_order.index("SkyUI_SE.esp"), sorted_order.index("Adamant.esp"))
        # Adamant must precede Mundus
        self.assertLess(sorted_order.index("Adamant.esp"), sorted_order.index("Mundus.esp"))

    def test_archive_ambiguity_detection(self):
        """Verifies that preflight rejects ambiguous duplicate archives for a mod."""
        archive1 = Path("SkyUI_5_2_SE.7z")
        archive2 = Path("SkyUI_5_2_SE_backup.7z")

        with self.assertRaises(SystemExit):
            match_archives_preflight([archive1, archive2])

    def test_display_tweaks_upstream_keys(self):
        """Verifies that SSEDisplayTweaks config strictly uses validated upstream keys."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_mo2 = Path(tmp_dir)
            target_dir = tmp_mo2 / "mods" / "SSE Display Tweaks" / "SKSE" / "Plugins"
            target_dir.mkdir(parents=True)
            inject_display_tweaks_custom_config(tmp_mo2)

            custom_ini = target_dir / "SSEDisplayTweaks_Custom.ini"
            self.assertTrue(custom_ini.is_file())
            content = custom_ini.read_text(encoding="utf-8")

            # Must contain upstream sections and verified keys
            self.assertIn("[Render]", content)
            self.assertIn("FramerateLimit=60.0", content)
            self.assertIn("EnableVSync=false", content)
            self.assertIn("EnableTearing=true", content)
            self.assertIn("SwapEffect=flip_discard", content)
            self.assertIn("[Havok]", content)
            self.assertIn("Enabled=true", content)
            self.assertIn("DynamicMaxTimeScaling=true", content)
            self.assertIn("MaximumFramerate=120.0", content)

            # Must NOT contain obsolete or invalid keys
            self.assertNotIn("MaxPhysicsFPS", content)
            self.assertNotIn("[Framerate]", content)
            self.assertNotIn("CalculateHavokTickRate", content)

    def test_activate_mo2_profile(self):
        """Verifies that activate_mo2_profile reliably updates selected_profile in ModOrganizer.ini."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            mo2_path = Path(tmp_dir)
            ini_file = mo2_path / "ModOrganizer.ini"
            ini_file.write_text("[General]\ngameName = Skyrim Special Edition\nselected_profile = Default\n", encoding="utf-8")

            activate_mo2_profile(mo2_path, "Handheld-10W")

            updated = ini_file.read_text(encoding="utf-8")
            self.assertIn("selected_profile = Handheld-10W", updated)
            self.assertIn("selected_executable = 1", updated)
            self.assertNotIn("selected_profile = Default", updated)

    def test_create_direct_launch_wrapper(self):
        """Verifies generation of launch_skse_direct.sh with correct moshortcut argument."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            game_dir = tmp_path / "game"
            mo2_dir = tmp_path / "mo2"
            game_dir.mkdir()
            mo2_dir.mkdir()

            create_direct_launch_wrapper(game_dir, mo2_dir)

            wrapper = game_dir / "launch_skse_direct.sh"
            self.assertTrue(wrapper.is_file())
            content = wrapper.read_text(encoding="utf-8")
            self.assertIn("moshortcut://:SKSE", content)
            self.assertTrue(bool(wrapper.stat().st_mode & 0o111))

    def test_freeze_steam_manifest(self):
        """Verifies that freeze_steam_manifest locks appmanifest_489830.acf to read-only."""
        import os
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            # Create synthetic steamapps structure: tmp_path / "steamapps" / "common" / "Skyrim Special Edition"
            steamapps = tmp_path / "steamapps"
            game_dir = steamapps / "common" / "Skyrim Special Edition"
            game_dir.mkdir(parents=True)
            manifest = steamapps / "appmanifest_489830.acf"
            manifest.write_text('"AppState" { "appid" "489830" }', encoding="utf-8")

            # Initially writable
            self.assertFalse(check_steam_manifest_frozen(game_dir))

            # Freeze manifest
            success = freeze_steam_manifest(game_dir)
            self.assertTrue(success)
            self.assertTrue(check_steam_manifest_frozen(game_dir))

            # Clean up permissions so tempfile can delete directory on exit
            manifest.chmod(0o644)

    def test_tune_engine_fixes_config(self):
        """Verifies that EngineFixes.toml is properly tuned for handheld performance."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            mod_path = Path(tmp_dir)
            plugins_dir = mod_path / "SKSE" / "Plugins"
            plugins_dir.mkdir(parents=True)
            toml_file = plugins_dir / "EngineFixes.toml"
            initial_toml = """[Patches]
EnableAchievementsWithMods = false
MemoryManager = true
SaveScreenshots = true
"""
            toml_file.write_text(initial_toml, encoding="utf-8")

            tune_engine_fixes_config(mod_path)

            tuned = toml_file.read_text(encoding="utf-8")
            self.assertIn("SaveScreenshots = false", tuned)
            self.assertIn("MemoryManager = false", tuned)
            self.assertIn("EnableAchievementsWithMods = true", tuned)

    def test_fomod_runtime_disambiguation(self):
        """Verifies that handle_fomod_and_flatten extracts 1.7.104 binary over 1.6.1170."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            mod_path = Path(tmp_dir)
            old_dir = mod_path / "01 - 1.6.1170" / "SKSE" / "Plugins"
            old_dir.mkdir(parents=True)
            (old_dir / "po3_Tweaks.dll").write_text("OLD_1170_BINARY", encoding="utf-8")

            new_dir = mod_path / "02 - 1.7.104" / "SKSE" / "Plugins"
            new_dir.mkdir(parents=True)
            (new_dir / "po3_Tweaks.dll").write_text("NEW_17104_BINARY", encoding="utf-8")

            handle_fomod_and_flatten(mod_path, "1.7.104", fomod_handler="po3_tweaks")

            target_dll = mod_path / "SKSE" / "Plugins" / "po3_Tweaks.dll"
            self.assertTrue(target_dll.is_file())
            self.assertEqual(target_dll.read_text(encoding="utf-8"), "NEW_17104_BINARY")

    def test_prune_old_backups(self):
        """Verifies that prune_old_backups keeps only the max_keep most recent backups."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            backup_root = Path(tmp_dir)
            (backup_root / "20261020_000000").mkdir()
            (backup_root / "20261021_000000").mkdir()
            (backup_root / "20261022_100000").mkdir()
            (backup_root / "20261022_120000").mkdir()

            prune_old_backups(backup_root, max_keep=2)

            remaining = [d.name for d in backup_root.iterdir() if d.is_dir()]
            self.assertEqual(len(remaining), 2)
            self.assertIn("20261022_100000", remaining)
            self.assertIn("20261022_120000", remaining)
            self.assertNotIn("20261020_000000", remaining)

if __name__ == "__main__":
    unittest.main()
