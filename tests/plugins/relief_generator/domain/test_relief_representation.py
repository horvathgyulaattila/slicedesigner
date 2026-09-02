"""Tesztek a `build_relief_representation`-höz.

Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_RELIEF_REPRESENTATION.md.
"""

import sys
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parents[4])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

import pytest  # noqa: E402

from plugins.relief_generator.domain.region_resolution import EffectSpec  # noqa: E402
from plugins.relief_generator.domain.relief_representation import (  # noqa: E402
    build_relief_representation,
)
from plugins.relief_generator.exceptions import (  # noqa: E402
    EffectProcessingConflictError,
)


class _ConstantMask:
    def __init__(self, value: bool = True) -> None:
        self._value = value

    def member(self, x: float, y: float) -> bool:
        return self._value


def test_empty_effect_specs_returns_zero_everywhere() -> None:
    relief = build_relief_representation(())

    assert relief(0.0, 0.0) == 0.0
    assert relief(5.0, -3.0) == 0.0


def test_no_active_spec_returns_zero() -> None:
    spec = EffectSpec(mask=_ConstantMask(False), elevation=0.5)
    relief = build_relief_representation((spec,))

    assert relief(0.0, 0.0) == 0.0


def test_single_active_spec_returns_its_elevation() -> None:
    spec = EffectSpec(mask=_ConstantMask(True), elevation=0.3)
    relief = build_relief_representation((spec,))

    assert relief(1.0, 2.0) == 0.3


def test_returned_function_is_reusable_across_points() -> None:
    def make_mask(active_x: float):
        class _Mask:
            def member(self, x: float, y: float) -> bool:
                return x == active_x

        return _Mask()

    a = EffectSpec(mask=make_mask(0.0), elevation=0.5)
    b = EffectSpec(mask=make_mask(1.0), elevation=-0.3)
    relief = build_relief_representation((a, b))

    assert relief(0.0, 0.0) == 0.5
    assert relief(1.0, 0.0) == -0.3
    assert relief(2.0, 0.0) == 0.0


def test_conflict_propagates_through_wrapper() -> None:
    branch = EffectSpec(mask=_ConstantMask(True), elevation=0.3)
    window = EffectSpec(mask=_ConstantMask(True), elevation=-0.2)
    relief = build_relief_representation((branch, window))

    with pytest.raises(EffectProcessingConflictError):
        relief(0.0, 0.0)


def test_two_builds_are_independent() -> None:
    spec_a = EffectSpec(mask=_ConstantMask(True), elevation=0.1)
    spec_b = EffectSpec(mask=_ConstantMask(True), elevation=0.9)
    relief_a = build_relief_representation((spec_a,))
    relief_b = build_relief_representation((spec_b,))

    assert relief_a(0.0, 0.0) == 0.1
    assert relief_b(0.0, 0.0) == 0.9
