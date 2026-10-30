import json
import os
import sys
import unittest
from pathlib import Path

from fonesi_edit.process import run_bounded


class LaunchTests(unittest.TestCase):
    def test_source_startup_smoke(self):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        script = Path(__file__).resolve().parents[1] / "scripts/frozen_entry.py"
        result = run_bounded([sys.executable, str(script), "--smoke-test"], timeout=30)
        self.assertEqual(result.status, "OK")
        evidence = json.loads(result.stdout)
        self.assertIs(evidence["frozen"], False)
        self.assertIs(evidence["passed"], True)
        self.assertEqual(len(evidence["checks"]), 6)
        self.assertTrue(all(value is True for value in evidence["checks"].values()))

    def test_unknown_option_rejected(self):
        script = Path(__file__).resolve().parents[1] / "scripts/frozen_entry.py"
        result = run_bounded(
            [sys.executable, str(script), "--unknown-option"], timeout=30
        )
        self.assertNotEqual(result.status, "OK")
