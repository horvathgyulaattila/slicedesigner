"""Tesztek a `resolve_regions`-hez.

Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_REGION_RESOLUTION.md.
"""

import sys
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parents[4])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

import pytest  # noqa: E402

from plugins.relief_generator.domain.region import (  # noqa: E402
    DepthBehavior,
    Region,
)
from plugins.relief_generator.domain.region_resolution import (  # noqa: E402
    resolve_regions,
)
from plugins.relief_generator.exceptions import RegionResolutionError  # noqa: E402


class _ConstantMask:
    def __init__(self, value: bool = True) -> None:
        self._value = value

    def member(self, x: float, y: float) -> bool:
        return self._value


def test_single_top_level_region_baseline_elevation() -> None:
    region = Region(
        mask=_ConstantMask(),
        contribution=0.5,
        depth_behavior=DepthBehavior.RAISED,
    )

    specs = resolve_regions((region,))

    assert len(specs) == 1
    assert specs[0].elevation == 0.5
    assert specs[0].parent_ref is None
    assert specs[0].tie_break_priority is None


def test_recessed_top_level_region_has_negative_elevation() -> None:
    region = Region(
        mask=_ConstantMask(),
        contribution=0.3,
        depth_behavior=DepthBehavior.RECESSED,
    )

    specs = resolve_regions((region,))

    assert specs[0].elevation == -0.3


def test_top_level_inherit_raises() -> None:
    region = Region(
        mask=_ConstantMask(),
        contribution=0.1,
        depth_behavior=DepthBehavior.INHERIT,
    )

    with pytest.raises(RegionResolutionError):
        resolve_regions((region,))


def test_house_window_example_from_planning_doc() -> None:
    window = Region(
        mask=_ConstantMask(),
        contribution=0.3,
        depth_behavior=DepthBehavior.RECESSED,
    )
    house = Region(
        mask=_ConstantMask(),
        contribution=0.5,
        depth_behavior=DepthBehavior.RAISED,
        children=(window,),
    )

    specs = resolve_regions((house,))

    assert len(specs) == 2
    house_spec, window_spec = specs
    assert house_spec.elevation == 0.5
    assert window_spec.elevation == pytest.approx(0.2)


def test_child_inherit_uses_parent_effective_depth_behavior() -> None:
    child = Region(
        mask=_ConstantMask(),
        contribution=0.2,
        depth_behavior=DepthBehavior.INHERIT,
    )
    parent = Region(
        mask=_ConstantMask(),
        contribution=0.4,
        depth_behavior=DepthBehavior.RECESSED,
        children=(child,),
    )

    specs = resolve_regions((parent,))

    parent_spec, child_spec = specs
    assert parent_spec.elevation == -0.4
    assert child_spec.elevation == pytest.approx(-0.6)


def test_multi_level_inherit_chain_resolves() -> None:
    grandchild = Region(
        mask=_ConstantMask(),
        contribution=0.1,
        depth_behavior=DepthBehavior.INHERIT,
    )
    child = Region(
        mask=_ConstantMask(),
        contribution=0.1,
        depth_behavior=DepthBehavior.INHERIT,
        children=(grandchild,),
    )
    root = Region(
        mask=_ConstantMask(),
        contribution=0.5,
        depth_behavior=DepthBehavior.RAISED,
        children=(child,),
    )

    specs = resolve_regions((root,))

    assert len(specs) == 3
    root_spec, child_spec, grandchild_spec = specs
    assert root_spec.elevation == pytest.approx(0.5)
    assert child_spec.elevation == pytest.approx(0.6)
    assert grandchild_spec.elevation == pytest.approx(0.7)


def test_parent_ref_points_to_parent_effect_spec() -> None:
    child = Region(
        mask=_ConstantMask(),
        contribution=0.1,
        depth_behavior=DepthBehavior.RAISED,
    )
    parent = Region(
        mask=_ConstantMask(),
        contribution=0.5,
        depth_behavior=DepthBehavior.RAISED,
        children=(child,),
    )

    specs = resolve_regions((parent,))

    parent_spec, child_spec = specs
    assert child_spec.parent_ref is parent_spec


def test_forest_roots_are_independent() -> None:
    root_a = Region(
        mask=_ConstantMask(),
        contribution=0.2,
        depth_behavior=DepthBehavior.RAISED,
    )
    root_b = Region(
        mask=_ConstantMask(),
        contribution=0.3,
        depth_behavior=DepthBehavior.RECESSED,
    )

    specs = resolve_regions((root_a, root_b))

    assert len(specs) == 2
    assert specs[0].elevation == 0.2
    assert specs[1].elevation == -0.3
    assert specs[0].parent_ref is None
    assert specs[1].parent_ref is None


def test_effect_spec_count_matches_region_count_in_deep_tree() -> None:
    leaf1 = Region(mask=_ConstantMask(), contribution=0.1, depth_behavior=DepthBehavior.RAISED)
    leaf2 = Region(mask=_ConstantMask(), contribution=0.1, depth_behavior=DepthBehavior.RAISED)
    branch = Region(
        mask=_ConstantMask(),
        contribution=0.2,
        depth_behavior=DepthBehavior.RAISED,
        children=(leaf1, leaf2),
    )
    root = Region(
        mask=_ConstantMask(),
        contribution=0.5,
        depth_behavior=DepthBehavior.RAISED,
        children=(branch,),
    )

    specs = resolve_regions((root,))

    assert len(specs) == 4


def test_mask_is_passed_through_unchanged() -> None:
    mask = _ConstantMask(True)
    region = Region(
        mask=mask,
        contribution=0.1,
        depth_behavior=DepthBehavior.RAISED,
    )

    specs = resolve_regions((region,))

    assert specs[0].mask is mask
