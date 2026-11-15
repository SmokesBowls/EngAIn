from __future__ import annotations

import builtins
import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PREFLIGHT_PATH = REPO_ROOT / "gates" / "gate_engainos_system_health_preflight_v1.py"


def _load_preflight():
    module_name = "engainos_system_health_preflight_under_test"
    spec = importlib.util.spec_from_file_location(module_name, PREFLIGHT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_preflight_runtime_checks_do_not_import_mrlore(monkeypatch):
    preflight = _load_preflight()
    imported: list[str] = []
    original_import = builtins.__import__
    original_import_module = preflight.importlib.import_module

    def recording_import(name, *args, **kwargs):
        imported.append(name)
        if name == "mrlore" or name.startswith("mrlore."):
            raise AssertionError(f"MrLore import attempted: {name}")
        if name == "tier1.mrlore" or name.startswith("tier1.mrlore."):
            raise AssertionError(f"MrLore import attempted: {name}")
        return original_import(name, *args, **kwargs)

    def blocked_import_module(name, *args, **kwargs):
        imported.append(name)
        if name == "mrlore" or name.startswith("mrlore."):
            raise AssertionError(f"MrLore import attempted: {name}")
        if name == "tier1.mrlore" or name.startswith("tier1.mrlore."):
            raise AssertionError(f"MrLore import attempted: {name}")
        return original_import_module(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", recording_import)
    monkeypatch.setattr(preflight.importlib, "import_module", blocked_import_module)

    systems_result = preflight.gate_systems_reachable()
    runtime_result = preflight.gate_engainos_runtime_requirements()

    assert systems_result.passed is True
    assert runtime_result.passed is True
    assert "mrlore" not in systems_result.details
    assert not any(name == "tier1.mrlore" or name.startswith("tier1.mrlore.") for name in imported)


def test_runtime_requirements_describe_current_engainos_dependencies():
    preflight = _load_preflight()

    result = preflight.gate_engainos_runtime_requirements()

    assert result.passed is True
    assert result.gate_name == "GATE_ENGAINOS_RUNTIME_REQUIREMENTS"
    assert set(result.details["modules"]) == {
        "ap_engine",
        "ap_runtime",
        "engainos_facade",
        "launch_engine",
        "scene_loader",
        "scene_server",
    }
    assert set(result.details["paths"]) == {
        "mettaext_passroom_output",
        "mettaext_scene_packet_index",
        "mettaext_stageroom",
    }
    assert all(item["importable"] for item in result.details["modules"].values())
    assert all(item["exists"] for item in result.details["paths"].values())


def test_runtime_requirements_fail_when_an_active_module_is_missing(monkeypatch):
    preflight = _load_preflight()
    monkeypatch.setattr(
        preflight,
        "ENGAINOS_RUNTIME_MODULES",
        {"missing_runtime_module": "tier1.engainos.__missing_runtime_module__"},
    )

    result = preflight.gate_engainos_runtime_requirements()

    assert result.passed is False
    assert result.details["modules"]["missing_runtime_module"]["importable"] is False
    assert "error" in result.details["modules"]["missing_runtime_module"]


def test_runtime_requirements_fail_when_stageroom_is_missing(tmp_path):
    preflight = _load_preflight()

    result = preflight.gate_engainos_runtime_requirements(root=tmp_path)

    assert result.passed is False
    assert result.details["paths"]["mettaext_stageroom"] == {
        "exists": False,
        "path": str(tmp_path / "tier3" / "mettaext" / "stageroom"),
        "type": "directory",
    }


def test_runtime_requirements_fail_when_stageroom_indexes_are_missing(tmp_path):
    preflight = _load_preflight()
    (tmp_path / "tier3" / "mettaext" / "stageroom").mkdir(parents=True)

    result = preflight.gate_engainos_runtime_requirements(root=tmp_path)

    assert result.passed is False
    assert result.details["paths"]["mettaext_stageroom"]["exists"] is True
    assert result.details["paths"]["mettaext_scene_packet_index"]["exists"] is False
    assert result.details["paths"]["mettaext_passroom_output"]["exists"] is False


def test_boot_acceptance_reason_names_runtime_requirements():
    preflight = _load_preflight()
    result = preflight.GateResult(True, "GATE_TEST", "ok", {})

    decision = preflight.build_boot_decision([result])

    assert decision["boot_allowed"] is True
    assert decision["reason"] == "All core systems and EngAInOS runtime requirements are reachable."


def test_active_engainos_dependency_files_do_not_name_mrlore():
    active_files = [
        PREFLIGHT_PATH,
        REPO_ROOT / "tier1" / "engainos" / "engainos_control_center.py",
        REPO_ROOT / "tier1" / "engainos" / "gates" / "MINIMAL_TEST_PACKET",
    ]

    for path in active_files:
        assert "mrlore" not in path.read_text(encoding="utf-8").lower(), path


def test_removing_stale_fixture_preserves_ap_gate_count():
    from tier1.engainos.engainos_control_center import MINIMAL_TEST_PACKET

    packet_fixture = (
        REPO_ROOT / "tier1" / "engainos" / "gates" / "MINIMAL_TEST_PACKET"
    ).read_text(encoding="utf-8")

    assert MINIMAL_TEST_PACKET["ap_validation"]["gate_count"] == 3
    assert '"gate_count": 3' in packet_fixture
