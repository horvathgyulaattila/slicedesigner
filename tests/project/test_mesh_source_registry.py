"""Tesztek a MeshSource plugin discovery-hez (ADR-0017)."""

from typing import Any
from unittest.mock import MagicMock

import pytest

from slicedesigner.project.mesh_source_registry import (
    MeshSourceDescriptor,
    ParameterSpec,
    build_mesh,
    discover_mesh_sources,
)


def test_parameter_spec_item_schema_defaults_to_empty_tuple() -> None:
    spec = ParameterSpec(name="width", label="Szélesség", type="float", default=1.0)

    assert spec.item_schema == ()


def test_parameter_spec_list_type_carries_item_schema() -> None:
    item_schema = (
        ParameterSpec(name="x", label="X", type="float", default=0.0),
        ParameterSpec(name="y", label="Y", type="float", default=0.0),
    )

    spec = ParameterSpec(
        name="points", label="Pontok", type="list", default=[], item_schema=item_schema
    )

    assert spec.type == "list"
    assert spec.item_schema == item_schema


def _make_entry_point(name: str, factory: Any) -> MagicMock:
    entry_point = MagicMock()
    entry_point.name = name
    entry_point.load.return_value = factory
    return entry_point


def _make_descriptor(display_name: str = "Stub Source") -> MeshSourceDescriptor:
    return MeshSourceDescriptor(
        display_name=display_name,
        parameters=(
            ParameterSpec(name="width", label="Szélesség", type="float", default=1.0),
        ),
        build=lambda values: object(),
    )


def test_discover_mesh_sources_returns_empty_tuple_without_plugins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "slicedesigner.project.mesh_source_registry.entry_points",
        lambda group: [],
    )

    result = discover_mesh_sources()

    assert result == ()


def test_discover_mesh_sources_returns_descriptor_from_valid_entry_point(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    descriptor = _make_descriptor("Valid Source")
    entry_point = _make_entry_point("valid", lambda: descriptor)
    monkeypatch.setattr(
        "slicedesigner.project.mesh_source_registry.entry_points",
        lambda group: [entry_point],
    )

    result = discover_mesh_sources()

    assert result == (descriptor,)


def test_discover_mesh_sources_skips_entry_point_that_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    good_descriptor = _make_descriptor("Good Source")

    def _broken_factory() -> MeshSourceDescriptor:
        raise RuntimeError("boom")

    broken_entry_point = _make_entry_point("broken", _broken_factory)
    good_entry_point = _make_entry_point("good", lambda: good_descriptor)
    monkeypatch.setattr(
        "slicedesigner.project.mesh_source_registry.entry_points",
        lambda group: [broken_entry_point, good_entry_point],
    )

    result = discover_mesh_sources()

    assert result == (good_descriptor,)


def test_build_mesh_calls_build_then_get_mesh_with_values() -> None:
    mesh = object()
    mesh_source = MagicMock()
    mesh_source.get_mesh.return_value = mesh
    build_fn = MagicMock(return_value=mesh_source)
    descriptor = MeshSourceDescriptor(
        display_name="Stub Source",
        parameters=(
            ParameterSpec(name="width", label="Szélesség", type="float", default=1.0),
        ),
        build=build_fn,
    )
    values = {"width": 2.5}

    result = build_mesh(descriptor, values)

    build_fn.assert_called_once_with(values)
    mesh_source.get_mesh.assert_called_once_with()
    assert result is mesh


def test_build_mesh_propagates_exception_from_get_mesh() -> None:
    mesh_source = MagicMock()
    mesh_source.get_mesh.side_effect = RuntimeError("boom")
    descriptor = MeshSourceDescriptor(
        display_name="Stub Source",
        parameters=(),
        build=lambda values: mesh_source,
    )

    with pytest.raises(RuntimeError, match="boom"):
        build_mesh(descriptor, {})


def test_discover_mesh_sources_skips_entry_point_that_fails_to_load(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    good_descriptor = _make_descriptor("Good Source")

    broken_entry_point = MagicMock()
    broken_entry_point.name = "broken-load"
    broken_entry_point.load.side_effect = ImportError("no module")
    good_entry_point = _make_entry_point("good", lambda: good_descriptor)
    monkeypatch.setattr(
        "slicedesigner.project.mesh_source_registry.entry_points",
        lambda group: [broken_entry_point, good_entry_point],
    )

    result = discover_mesh_sources()

    assert result == (good_descriptor,)
