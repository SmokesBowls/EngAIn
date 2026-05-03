#!/usr/bin/env python3
from pathlib import Path
import json
import re
import urllib.request
import urllib.error

ENGAIN_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")
NEW_VAULT_ROOT = Path("/run/media/mytruelove/storage1/pop/obsidian/obsidianburdenNov25")
NEW_MANIFEST = NEW_VAULT_ROOT / "vault.manifest.json"

CONFIG_PATH = ENGAIN_ROOT / "godotsim" / ".engain_config.json"
VAULTCLIENT_GD = ENGAIN_ROOT / "godotroot" / "zonjrender" / "autoload" / "VaultClient.gd"
TESTSCENE_GD = ENGAIN_ROOT / "godotroot" / "zonjrender" / "scenes" / "EngAInTestScene.gd"

def backup(path: Path) -> None:
    bak = path.with_name(path.name + ".bak_vault_recovery")
    if not bak.exists() and path.exists():
        bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

def patch_text_file(path: Path, replacements: list[tuple[str, str]]) -> bool:
    if not path.exists():
        print(f"[MISS] {path}")
        return False

    original = path.read_text(encoding="utf-8")
    updated = original

    for pattern, replacement in replacements:
        updated = re.sub(pattern, replacement, updated, flags=re.MULTILINE)

    if updated != original:
        backup(path)
        path.write_text(updated, encoding="utf-8")
        print(f"[PATCHED] {path}")
        return True

    print(f"[OK] No change needed: {path}")
    return False

def write_runtime_config() -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if CONFIG_PATH.exists():
        backup(CONFIG_PATH)

    cfg = {
        "vault_root": str(NEW_VAULT_ROOT),
        "manifest_path": str(NEW_MANIFEST),
    }
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    print(f"[WROTE] {CONFIG_PATH}")

def load_manifest() -> dict:
    if not NEW_MANIFEST.exists():
        raise FileNotFoundError(f"Manifest not found: {NEW_MANIFEST}")
    return json.loads(NEW_MANIFEST.read_text(encoding="utf-8"))

def relink_runtime() -> None:
    manifest = load_manifest()
    payload = json.dumps({
        "vault_root": str(NEW_VAULT_ROOT),
        "manifest": manifest,
    }).encode("utf-8")

    req = urllib.request.Request(
        "http://127.0.0.1:8080/vault/link",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            print("[RELINKED] Runtime /vault/link response:")
            print(body)
    except urllib.error.URLError as e:
        print(f"[WARN] Could not POST /vault/link right now: {e}")
        print("[WARN] Restart godotsim after this so auto-relink uses the new .engain_config.json")

def main() -> None:
    if not NEW_VAULT_ROOT.is_dir():
        raise SystemExit(f"Vault root missing: {NEW_VAULT_ROOT}")

    if not NEW_MANIFEST.is_file():
        raise SystemExit(f"vault.manifest.json missing: {NEW_MANIFEST}")

    write_runtime_config()

    patch_text_file(
        VAULTCLIENT_GD,
        [
            (
                r'^@export var default_vault_root: String = ".*"$',
                f'@export var default_vault_root: String = "{NEW_VAULT_ROOT}"',
            ),
            (
                r'^@export var default_manifest_path: String = ".*"$',
                '@export var default_manifest_path: String = "vault.manifest.json"',
            ),
        ],
    )

    patch_text_file(
        TESTSCENE_GD,
        [
            (
                r'^@export var vault_root: String = ".*"$',
                f'@export var vault_root: String = "{NEW_VAULT_ROOT}"',
            ),
            (
                r'^@export var manifest_path: String = ".*"$',
                f'@export var manifest_path: String = "{NEW_MANIFEST}"',
            ),
        ],
    )

    relink_runtime()

    print("\nDone.")
    print("If Godot was already open, close and reopen the zonjrender project.")

if __name__ == "__main__":
    main()
