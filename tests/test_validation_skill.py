"""Tests for the bundled 3ds Max validation skill."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

SKILL_DIR = Path(__file__).resolve().parents[1] / "src" / "dcc_mcp_3dsmax" / "skills" / "3dsmax-validation"


def _load_action(script_name: str):
    path = SKILL_DIR / script_name
    spec = importlib.util.spec_from_file_location(path.stem + "_test_module", str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Material:
    def __init__(self, name: str, texture_paths: list[str]) -> None:
        self.name = name
        self.texture_paths = texture_paths


class _FakeNode:
    def __init__(
        self,
        name: str,
        handle: int,
        *,
        material: _Material,
        good: bool,
    ) -> None:
        self.name = name
        self.handle = handle
        self.parent = None
        self.isHidden = False
        self.position = [0.0, 0.0, 0.0] if good else [2.0, 0.0, 0.0]
        self.rotation = [0.0, 0.0, 0.0] if good else [0.0, 15.0, 0.0]
        self.scale = [1.0, 1.0, 1.0] if good else [1.0, 2.0, 1.0]
        self.min = [0.0, 0.0, 0.0]
        self.max = [1.0, 1.0, 1.0]
        self.pivot = [0.5, 0.5, 0.5] if good else [0.0, 0.0, 0.0]
        self.open_edge_count = 0 if good else 2
        self.isolated_vertex_count = 0 if good else 1
        self.triangle_count = 2 if good else 6
        self.quad_count = 10 if good else 3
        self.ngon_count = 0 if good else 1
        self.smoothing_groups = {1: 1, 2: 1} if good else {1: 0, 2: 1}
        self.material = material
        self.uv_channels = [1, 2] if good else [2]
        self.uv_overlap_count = 0 if good else 3


class _FakeRuntime:
    def __init__(self, existing_texture: Path, missing_texture: Path) -> None:
        self.good = _FakeNode("Hero_01", 42, material=_Material("hero_mat", [str(existing_texture)]), good=True)
        self.bad = _FakeNode("bad name", 43, material=_Material("bad_mat", [str(missing_texture)]), good=False)
        self.objects = [self.good, self.bad]
        self.selection = [self.bad]

    def getNodeByName(self, name):  # noqa: N802 - mirrors pymxs runtime naming.
        for node in self.objects:
            if node.name == name:
                return node
        return None


def _install_fake_pymxs(monkeypatch, tmp_path: Path):
    existing_texture = tmp_path / "albedo.png"
    existing_texture.write_bytes(b"texture")
    runtime = _FakeRuntime(existing_texture, tmp_path / "missing.png")
    monkeypatch.setitem(sys.modules, "pymxs", types.SimpleNamespace(runtime=runtime))
    return runtime


def test_atomic_validation_tools_return_structured_pass_fail_and_warning(monkeypatch, tmp_path):
    _install_fake_pymxs(monkeypatch, tmp_path)

    naming = _load_action("action_validate_naming.py").main()
    transforms = _load_action("action_validate_transforms.py").main(use_selection=True)
    topology = _load_action("action_validate_mesh_topology.py").main(use_selection=True)
    smoothing = _load_action("action_validate_smoothing_groups.py").main(use_selection=True)
    texture_paths = _load_action("action_validate_texture_paths.py").main()
    uv_channels = _load_action("action_validate_uv_channels.py").main(use_selection=True, required_channels=[1, 2])
    uv_overlaps = _load_action("action_validate_uv_overlaps.py").main(use_selection=True)

    assert naming["data"]["summary"]["failed"] == 1
    assert transforms["data"]["checks"][0]["status"] == "failed"
    assert "position" in transforms["data"]["checks"][0]["details"]
    assert topology["data"]["checks"][0]["details"]["open_edges"] == 2
    assert smoothing["data"]["checks"][0]["details"]["missing_count"] == 1
    assert texture_paths["data"]["summary"]["failed"] == 1
    assert uv_channels["data"]["checks"][0]["details"]["missing"] == [1]
    assert uv_overlaps["data"]["checks"][0]["status"] == "failed"
    assert all("hint" in check for check in naming["data"]["checks"])


def test_material_and_pivot_validators_report_ready_nodes(monkeypatch, tmp_path):
    _install_fake_pymxs(monkeypatch, tmp_path)

    materials = _load_action("action_validate_material_assignments.py").main(node_names=["Hero_01"])
    pivots = _load_action("action_validate_pivots.py").main(node_names=["Hero_01"])

    assert materials["data"]["summary"]["status"] == "passed"
    assert materials["data"]["checks"][0]["details"]["material"] == "hero_mat"
    assert pivots["data"]["checks"][0]["status"] == "passed"


def test_asset_readiness_runner_aggregates_selected_validators(monkeypatch, tmp_path):
    _install_fake_pymxs(monkeypatch, tmp_path)

    from dcc_mcp_3dsmax._executor import run_skill_script

    result = run_skill_script(
        str(SKILL_DIR / "action_run_asset_readiness_checks.py"),
        {
            "node_names": ["bad name"],
            "validators": ["naming", "mesh_topology", "uv_channels"],
            "required_uv_channels": [1, 2],
        },
    )

    assert result["success"] is True
    assert result["data"]["summary"]["status"] == "failed"
    assert result["data"]["summary"]["failed"] == 3
    assert [row["validator"] for row in result["data"]["validators"]] == ["naming", "mesh_topology", "uv_channels"]
    assert len(result["data"]["checks"]) == 3


def test_validation_tools_report_target_and_runner_errors(monkeypatch, tmp_path):
    _install_fake_pymxs(monkeypatch, tmp_path)

    missing = _load_action("action_validate_naming.py").main(node_names=["missing"])
    unknown_validator = _load_action("action_run_asset_readiness_checks.py").main(validators=["not_real"])

    assert missing["success"] is False
    assert "could not be resolved" in missing["message"]
    assert unknown_validator["success"] is False
    assert unknown_validator["data"]["validators"] == ["not_real"]
