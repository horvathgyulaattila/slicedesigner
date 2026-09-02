"""Tesztek a `combine`-hoz.

Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_EFFECT_PROCESSING.md.
"""

import sys
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parents[4])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

import pytest  # noqa: E402

from plugins.relief_generator.domain.effect_processing import combine  # noqa: E402
from plugins.relief_generator.domain.region_resolution import EffectSpec  # noqa: E402
from plugins.relief_generator.exceptions import (  # noqa: E402
    EffectProcessingConflictError,
)


class _ConstantMask:
    def __init__(self, value: bool = True) -> None:
        self._value = value

    def member(self, x: float, y: float) -> bool:
        return self._value


def test_no_active_spec_returns_zero() -> None:
    spec = EffectSpec(mask=_ConstantMask(False), elevation=0.5)

    assert combine((spec,), 0.0, 0.0) == 0.0


def test_single_active_spec_returns_its_elevation() -> None:
    spec = EffectSpec(mask=_ConstantMask(True), elevation=0.3)

    assert combine((spec,), 0.0, 0.0) == 0.3


def test_lineage_occlusion_excludes_ancestor() -> None:
    house = EffectSpec(mask=_ConstantMask(True), elevation=0.5)
    window = EffectSpec(mask=_ConstantMask(True), elevation=0.2, parent_ref=house)

    assert combine((house, window), 0.0, 0.0) == 0.2


def test_envelope_picks_largest_magnitude_same_direction() -> None:
    tree = EffectSpec(mask=_ConstantMask(True), elevation=0.4)
    house = EffectSpec(mask=_ConstantMask(True), elevation=0.7)

    assert combine((tree, house), 0.0, 0.0) == 0.7


def test_envelope_picks_largest_magnitude_negative_direction() -> None:
    a = EffectSpec(mask=_ConstantMask(True), elevation=-0.2)
    b = EffectSpec(mask=_ConstantMask(True), elevation=-0.6)

    assert combine((a, b), 0.0, 0.0) == -0.6


def test_opposite_direction_without_tie_break_priority_raises() -> None:
    branch = EffectSpec(mask=_ConstantMask(True), elevation=0.3)
    window = EffectSpec(mask=_ConstantMask(True), elevation=-0.2)

    with pytest.raises(EffectProcessingConflictError):
        combine((branch, window), 0.0, 0.0)


def test_opposite_direction_with_unique_max_priority_resolves() -> None:
    branch = EffectSpec(
        mask=_ConstantMask(True), elevation=0.3, tie_break_priority=1
    )
    window = EffectSpec(
        mask=_ConstantMask(True), elevation=-0.2, tie_break_priority=5
    )

    assert combine((branch, window), 0.0, 0.0) == -0.2


def test_opposite_direction_with_tied_max_priority_raises() -> None:
    a = EffectSpec(mask=_ConstantMask(True), elevation=0.3, tie_break_priority=5)
    b = EffectSpec(mask=_ConstantMask(True), elevation=-0.2, tie_break_priority=5)

    with pytest.raises(EffectProcessingConflictError):
        combine((a, b), 0.0, 0.0)


def test_zero_elevation_member_does_not_trigger_conflict() -> None:
    zero_spec = EffectSpec(mask=_ConstantMask(True), elevation=0.0)
    positive = EffectSpec(mask=_ConstantMask(True), elevation=0.4)

    assert combine((zero_spec, positive), 0.0, 0.0) == 0.4


def test_non_overlapping_masks_do_not_interact() -> None:
    def make_mask(active_x: float):
        class _Mask:
            def member(self, x: float, y: float) -> bool:
                return x == active_x

        return _Mask()

    a = EffectSpec(mask=make_mask(0.0), elevation=0.5)
    b = EffectSpec(mask=make_mask(1.0), elevation=-0.3)

    assert combine((a, b), 0.0, 0.0) == 0.5
    assert combine((a, b), 1.0, 0.0) == -0.3
