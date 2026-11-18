"""Tier 1 active-vault resolution: active.vault is authority, legacy active_vault is cross-checked."""

import json
import tempfile
import unittest
from pathlib import Path

from tier1.engainos.tools.vault_discovery import resolve_active_vault
from tier1.engainos.tools.chapter_discovery import _vault_from_manifest


class VaultResolutionTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.vault = self.tmp / "vaultA"
        self.vault.mkdir()
        (self.vault / "vault.manifest.json").write_text("{}", encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def _manifest(self, data):
        p = self.tmp / "engain_manifest.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        return p

    def _base(self, **extra):
        data = {"active": {"vault": "vaultA"},
                "vaults": {"vaultA": {"root": str(self.vault),
                                      "manifest": str(self.vault / "vault.manifest.json")}}}
        data.update(extra)
        return data

    def test_ok_with_matching_legacy_field(self):
        r = resolve_active_vault(self._manifest(self._base(active_vault=str(self.vault))))
        self.assertEqual(r["status"], "ok", r["problems"])
        self.assertEqual((r["vault_id"], r["root"]), ("vaultA", str(self.vault)))

    def test_ok_without_legacy_field(self):
        self.assertEqual(resolve_active_vault(self._manifest(self._base()))["status"], "ok")

    def test_legacy_disagreement_is_reported_not_guessed(self):
        r = resolve_active_vault(self._manifest(self._base(active_vault=str(self.tmp / "other"))))
        self.assertEqual(r["status"], "error")
        self.assertIn("disagrees", " ".join(r["problems"]))

    def test_missing_active_vault_does_not_fall_back_to_legacy(self):
        r = resolve_active_vault(self._manifest({"active_vault": str(self.vault)}))
        self.assertEqual(r["status"], "error")
        self.assertIsNone(r["root"])

    def test_unknown_vault_id(self):
        data = self._base()
        data["active"]["vault"] = "nope"
        self.assertEqual(resolve_active_vault(self._manifest(data))["status"], "error")

    def test_missing_root_and_vault_manifest(self):
        data = self._base()
        data["vaults"]["vaultA"] = {"root": str(self.tmp / "gone")}
        r = resolve_active_vault(self._manifest(data))
        self.assertEqual(r["status"], "error")
        self.assertEqual(len(r["problems"]), 2)

    def test_missing_or_bad_manifest_file(self):
        self.assertEqual(resolve_active_vault(self.tmp / "absent.json")["status"], "error")
        bad = self.tmp / "bad.json"
        bad.write_text("{", encoding="utf-8")
        self.assertEqual(resolve_active_vault(bad)["status"], "error")

    def test_chapter_discovery_uses_resolver(self):
        self.assertEqual(_vault_from_manifest(self._manifest(self._base())), self.vault)
        self.assertIsNone(_vault_from_manifest(self._manifest({"active_vault": str(self.vault)})))


if __name__ == "__main__":
    unittest.main()
