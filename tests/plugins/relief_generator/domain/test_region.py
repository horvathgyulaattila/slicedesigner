"""Tesztek a `Region`-hez.

Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_REGION_MODEL.md.
"""

import sys
from pathlib import Path

# A `plugins/` névtér PEP 420 namespace package (l. ADR-0016) — a repo
# gyökeret explicit módon a `sys.path` elejére kell tenni, mielőtt a
# `plugins.relief_generator` névtér először importálásra kerül (l. a
# meglévő tesztek, pl. test_height_field.py azonos mintája).
_REPO_ROOT = str(Path(__file__).resolve().parents[4])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

import pytest  # noqa: E402

from plugins.relief_generator.domain.region import (  # noqa: E402
    DepthBehavior,
    Region,
)
from plugins.relief_generator.exceptions import RegionValueError  # noqa: E402


class _ConstantMask:
    """Egyszerű, mindig ugyanazt visszaadó `Mask`-megvalósítás teszthez."""

    def __init__(self, value: bool) -> None:
        self._value = value

    def member(self, x: float, y: float) -> bool:
        return self._value


def test_valid_region_is_accepted() -> None:
    region = Region(
        mask=_ConstantMask(True),
        contribution=0.5,
        depth_behavior=DepthBehavior.RAISED,
    )

    assert region.contribution == 0.5
    assert region.depth_behavior == DepthBehavior.RAISED
    assert region.children == ()


def test_zero_contribution_is_accepted() -> None:
    region = Region(
        mask=_ConstantMask(True),
        contribution=0.0,
        depth_behavior=DepthBehavior.INHERIT,
    )

    assert region.contribution == 0.0


def test_negative_contribution_raises() -> None:
    with pytest.raises(RegionValueError):
        Region(
            mask=_ConstantMask(True),
            contribution=-0.1,
            depth_behavior=DepthBehavior.RECESSED,
        )


def test_children_can_be_nested_regions() -> None:
    child = Region(
        mask=_ConstantMask(True),
        contribution=0.3,
        depth_behavior=DepthBehavior.RECESSED,
    )
    parent = Region(
        mask=_ConstantMask(True),
        contribution=0.5,
        depth_behavior=DepthBehavior.RAISED,
        children=(child,),
    )

    assert parent.children == (child,)
    assert parent.children[0].contribution == 0.3


def test_mask_member_query_is_used_via_protocol() -> None:
    region = Region(
        mask=_ConstantMask(False),
        contribution=0.1,
        depth_behavior=DepthBehavior.INHERIT,
    )

    assert region.mask.member(10.0, 20.0) is False


@pytest.mark.parametrize(
    "depth_behavior",
    [DepthBehavior.RAISED, DepthBehavior.RECESSED, DepthBehavior.INHERIT],
)
def test_all_depth_behavior_values_are_accepted(
    depth_behavior: DepthBehavior,
) -> None:
    region = Region(
        mask=_ConstantMask(True),
        contribution=1.0,
        depth_behavior=depth_behavior,
    )

    assert region.depth_behavior is depth_behavior
