"""Tesztek a Gap Engine-hez (GAP_SYSTEM_SPEC.md)."""

import logging

import pytest
import trimesh

from slicedesigner.engines.dowel_engine import apply_dowels
from slicedesigner.engines.exceptions import InvalidGapError
from slicedesigner.engines.gap_engine import apply_gap
from slicedesigner.engines.mesh_import import BoundingBox, Mesh
from slicedesigner.engines.slice_engine import (
    Contour,
    Slice,
    SliceSet,
    create_slice_set,
)


def _mesh_from_trimesh(tm: trimesh.Trimesh, source_path: str = "test.stl") -> Mesh:
    bounds = tm.bounds
    bounding_box = BoundingBox(
        min=(float(bounds[0][0]), float(bounds[0][1]), float(bounds[0][2])),
        max=(float(bounds[1][0]), float(bounds[1][1]), float(bounds[1][2])),
    )
    return Mesh(
        vertices=tuple(tuple(float(c) for c in v) for v in tm.vertices),
        triangles=tuple(tuple(int(i) for i in f) for f in tm.faces),
        source_path=source_path,
        bounding_box=bounding_box,
        is_valid=True,
        warnings=(),
    )


def _make_box_slice_set(
    extents: tuple[float, float, float], slice_thickness_mm: float, gap_mm: float = 0.0
) -> SliceSet:
    box = trimesh.creation.box(extents=extents)
    mesh = _mesh_from_trimesh(box)
    return create_slice_set(mesh, slice_thickness_mm=slice_thickness_mm, gap_mm=gap_mm)


def _rect_contour(x_min: float, x_max: float, y_min: float, y_max: float) -> Contour:
    return Contour(
        points=(
            (x_min, y_min),
            (x_max, y_min),
            (x_max, y_max),
            (x_min, y_max),
        )
    )


def _make_hand_slice_set(
    slices_islands: list[list[tuple[float, float, float, float]]],
    thickness_mm: float = 2.0,
    gap_mm: float = 1.0,
) -> SliceSet:
    """Kézzel épített, tetszőleges (téglalap alakú) szigetlistával rendelkező
    SliceSet — több szeletet és/vagy szeletenként több szigetet igénylő
    esetekhez (pl. Gap-enkénti `region_id` teszteléséhez)."""
    slices = [
        Slice(
            thickness_mm=thickness_mm,
            contours=tuple(_rect_contour(*r) for r in islands),
            position_mm=(i - 0.5) * thickness_mm,
            index=i,
        )
        for i, islands in enumerate(slices_islands, start=1)
    ]
    all_x = [v for islands in slices_islands for r in islands for v in (r[0], r[1])]
    all_y = [v for islands in slices_islands for r in islands for v in (r[2], r[3])]
    bounding_box = BoundingBox(
        min=(min(all_x), min(all_y), 0.0),
        max=(max(all_x), max(all_y), len(slices_islands) * thickness_mm),
    )
    mesh = Mesh(
        vertices=((0.0, 0.0, 0.0),),
        triangles=(),
        source_path="hand-built.stl",
        bounding_box=bounding_box,
        is_valid=True,
        warnings=(),
    )
    return SliceSet(
        source_mesh=mesh,
        gap_mm=gap_mm,
        slices=tuple(slices),
        slice_count=len(slices_islands),
    )


def test_apply_gap_zero_gap_returns_empty() -> None:
    slice_set = _make_box_slice_set(
        extents=(30.0, 30.0, 15.0), slice_thickness_mm=3.0, gap_mm=0.0
    )

    result_slice_set, spacers = apply_gap(slice_set, spacer_diameter_mm=3.0)

    assert spacers == ()
    assert result_slice_set is slice_set


def test_apply_gap_places_default_count_without_dowels() -> None:
    slice_set = _make_box_slice_set(
        extents=(30.0, 30.0, 14.0), slice_thickness_mm=2.0, gap_mm=1.0
    )

    _slice_set, spacers = apply_gap(slice_set, spacer_diameter_mm=3.0)

    assert len(spacers) == 12  # 5 szelet -> 4 Gap, egyenként 3 (alapértelmezett cél)
    start_indices = {s.start_slice_index for s in spacers}
    assert start_indices == {1, 2, 3, 4}
    for spacer in spacers:
        assert spacer.diameter_mm == 3.0
        assert spacer.thickness_mm == 1.0
        assert spacer.shape == "cylinder"


def test_apply_gap_reuses_dowel_position_despite_hole() -> None:
    slice_set = _make_box_slice_set(
        extents=(30.0, 30.0, 14.0), slice_thickness_mm=2.0, gap_mm=1.0
    )
    slice_set, dowel_positions = apply_dowels(
        slice_set, dowel_diameter_mm=3.0, dowel_count_per_region=1
    )

    assert len(dowel_positions) == 1
    dowel = dowel_positions[0]
    assert dowel.start_slice_index == 1
    assert dowel.end_slice_index == 5

    _final_slice_set, spacers = apply_gap(
        slice_set,
        spacer_diameter_mm=3.0,
        dowel_positions=dowel_positions,
        spacer_count_per_gap=1,
        min_spacers_per_region=1,
    )

    assert len(spacers) == 4  # 5 szelet -> 4 Gap
    for spacer in spacers:
        assert spacer.x_mm == pytest.approx(dowel.x_mm)
        assert spacer.y_mm == pytest.approx(dowel.y_mm)
        assert spacer.diameter_mm == 3.0
        assert spacer.thickness_mm == 1.0
    start_indices = sorted(s.start_slice_index for s in spacers)
    assert start_indices == [1, 2, 3, 4]


def test_apply_gap_insufficient_region_raises() -> None:
    slice_set = _make_box_slice_set(
        extents=(2.0, 2.0, 14.0), slice_thickness_mm=2.0, gap_mm=1.0
    )

    with pytest.raises(InvalidGapError):
        apply_gap(slice_set, spacer_diameter_mm=10.0)


def test_apply_gap_invalid_diameter_raises() -> None:
    slice_set = _make_box_slice_set(
        extents=(30.0, 30.0, 14.0), slice_thickness_mm=2.0, gap_mm=1.0
    )

    with pytest.raises(InvalidGapError):
        apply_gap(slice_set, spacer_diameter_mm=0.0)


def test_apply_gap_invalid_count_per_gap_raises() -> None:
    slice_set = _make_box_slice_set(
        extents=(30.0, 30.0, 14.0), slice_thickness_mm=2.0, gap_mm=1.0
    )

    with pytest.raises(InvalidGapError):
        apply_gap(slice_set, spacer_diameter_mm=3.0, spacer_count_per_gap=0)


def test_apply_gap_min_greater_than_count_raises() -> None:
    slice_set = _make_box_slice_set(
        extents=(30.0, 30.0, 14.0), slice_thickness_mm=2.0, gap_mm=1.0
    )

    with pytest.raises(InvalidGapError):
        apply_gap(
            slice_set,
            spacer_diameter_mm=3.0,
            spacer_count_per_gap=2,
            min_spacers_per_region=3,
        )


def test_apply_gap_region_id_restarts_per_gap() -> None:
    """GAP_SYSTEM_SPEC.md 4. szakasz: a `region_id` minden Gap-en belül
    `1`-től induljon újra, ne a teljes Slice Set-en át folyamatosan
    növekedjen.

    A fixture 3 szeletet tartalmaz (-> 2 Gap), mindegyiken 2, egymástól
    távol eső (nem átfedő) szigettel — ez Gap-enként 2-2, egymástól
    független metszet-régiót eredményez. Ha a `region_id` folyamatosan
    növekedne, a 2. Gap régiói `{3, 4}` lennének `{1, 2}` helyett."""
    islands = [(0.0, 20.0, 0.0, 20.0), (100.0, 120.0, 0.0, 20.0)]
    slice_set = _make_hand_slice_set(
        [islands, islands, islands], thickness_mm=2.0, gap_mm=1.0
    )

    _slice_set, spacers = apply_gap(slice_set, spacer_diameter_mm=3.0)

    region_ids_by_gap: dict[int, set[int]] = {}
    for spacer in spacers:
        region_ids_by_gap.setdefault(spacer.start_slice_index, set()).add(
            spacer.region_id
        )

    assert set(region_ids_by_gap.keys()) == {1, 2}  # 3 szelet -> 2 Gap
    assert region_ids_by_gap[1] == {1, 2}
    assert region_ids_by_gap[2] == {1, 2}


def test_apply_gap_min_zero_allows_empty_region(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """GAP_SYSTEM_SPEC.md 5. és 7. szakasz: `min_spacers_per_region=0`
    esetén egy olyan (mesterségesen apró) régió, ahol egyetlen Spacer sem
    fér el, NEM dob hibát — a régióra nulla Spacer kerül a listába,
    figyelmeztetéssel.

    Ugyanaz a fixture, mint `test_apply_gap_insufficient_region_raises`
    (2x2 mm keresztmetszet, 10 mm átmérőjű Spacer — sosem fér el), de itt
    `min_spacers_per_region=0` mellett."""
    slice_set = _make_box_slice_set(
        extents=(2.0, 2.0, 14.0), slice_thickness_mm=2.0, gap_mm=1.0
    )

    with caplog.at_level(logging.WARNING):
        _slice_set, spacers = apply_gap(
            slice_set, spacer_diameter_mm=10.0, min_spacers_per_region=0
        )

    assert spacers == ()
    assert any("csak 0 Spacer" in record.getMessage() for record in caplog.records)
