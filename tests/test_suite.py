#!/usr/bin/env python3
"""
tests/test_suite.py
Automated Verification & Unit Tests for Skyrim SE Handheld Modder Suite
"""

import unittest
import struct
import tempfile
import shutil
from pathlib import Path

# Import functions from deploy_mods
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from deploy_mods import (
    get_pe_file_version,
    parse_tes4_masters,
    topological_sort_plugins,
    match_archives_preflight,
    ALLOWED_BASE_MASTERS,
    REQUIRED_RUNTIME,
    MOD_MANIFEST
)

class TestHandheldSuite(unittest.TestCase):

    def test_pe_header_version_detection(self):
        """Verifies accurate detection of Windows PE FileVersion."""
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

    def test_tes4_master_parsing_and_cc_validation(self):
        """Verifies extraction of plugin masters and detection of paid Creation Club DLCs."""
        # 1. Synthetic plugin with allowed base masters
        mast1 = b"Skyrim.esm\x00"
        sub1 = b"MAST" + struct.pack("<H", len(mast1)) + mast1
        mast2 = b"ccbgssse001-fish.esm\x00"
        sub2 = b"MAST" + struct.pack("<H", len(mast2)) + mast2
        data = sub1 + sub2
        header = b"TES4" + struct.pack("<I", len(data)) + (b"\x00" * 16)
        synth_plugin_valid = header + data

        with tempfile.NamedTemporaryFile(suffix=".esp", delete=False) as f:
            f.write(synth_plugin_valid)
            temp_valid = Path(f.name)

        try:
            masters = parse_tes4_masters(temp_valid)
            self.assertEqual(masters, ["Skyrim.esm", "ccbgssse001-fish.esm"])
            # Validate against allowed base masters (should all pass)
            for m in masters:
                self.assertIn(m.lower(), ALLOWED_BASE_MASTERS)
        finally:
            temp_valid.unlink()

        # 2. Synthetic plugin with unauthorized paid Creation Club master
        mast_paid = b"ccbgssse002-exoticpets.esl\x00"
        sub_paid = b"MAST" + struct.pack("<H", len(mast_paid)) + mast_paid
        header_paid = b"TES4" + struct.pack("<I", len(sub_paid)) + (b"\x00" * 16)
        synth_plugin_paid = header_paid + sub_paid

        with tempfile.NamedTemporaryFile(suffix=".esp", delete=False) as f:
            f.write(synth_plugin_paid)
            temp_paid = Path(f.name)

        try:
            masters_paid = parse_tes4_masters(temp_paid)
            self.assertEqual(masters_paid, ["ccbgssse002-exoticpets.esl"])
            # Ensure it is flagged as NOT in base masters
            for m in masters_paid:
                self.assertNotIn(m.lower(), ALLOWED_BASE_MASTERS)
        finally:
            temp_paid.unlink()

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
        """Verifies that SSEDisplayTweaks config uses validated upstream keys under [Render] and [Havok]."""
        from deploy_mods import inject_display_tweaks_custom_config
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_mo2 = Path(tmp_dir)
            target_dir = tmp_mo2 / "mods" / "SSE Display Tweaks" / "SKSE" / "Plugins"
            target_dir.mkdir(parents=True)
            inject_display_tweaks_custom_config(tmp_mo2)

            custom_ini = target_dir / "SSEDisplayTweaks_Custom.ini"
            self.assertTrue(custom_ini.is_file())
            content = custom_ini.read_text(encoding="utf-8")

            # Must contain upstream sections and keys
            self.assertIn("[Render]", content)
            self.assertIn("FramerateLimit=60.0", content)
            self.assertIn("EnableVSync=false", content)
            self.assertIn("[Havok]", content)
            self.assertIn("Enabled=true", content)
            self.assertIn("MaxPhysicsFPS=120.0", content)

            # Must NOT contain obsolete or invalid keys
            self.assertNotIn("[Framerate]", content)
            self.assertNotIn("CalculateHavokTickRate", content)

if __name__ == "__main__":
    unittest.main()
