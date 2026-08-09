"""Tesztek a Nesting Engine 1. köréhez (NESTING_SPEC.md 6. szakasz, 1-5. lépés)."""

import pytest
import trimesh

from slicedesigner.engines.backplate_engine import BackplateNormalAxis
from slicedesigner.engines.exceptions import InvalidNestingError
from slicedesigner.engines.gap_engine import Spacer
from slicedesigner.engines.mesh_import import BoundingBox, Mesh
from slicedesigner.engines.nesting_engine import (
    MaterialDefinition,
    NestingRotationMode,
    PartKind,
    _build_text_strokes_rect,
    _spacer_to_discs,
    create_nests,
    prepare_nesting_parts,
)
from slicedesigner.engines.numbering_engine import (
    NumberingDirectionSign,
    apply_numbering,
)
from slicedesigner.engines.slice_engine import SliceSet, create_slice_set, is_ccw


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


def _numbered_box(
    extents: tuple[float, float, float], slice_thickness_mm: float, gap_mm: float = 0.0
) -> SliceSet:
    slice_set = _make_box_slice_set(extents, slice_thickness_mm, gap_mm)
    return apply_numbering(
        slice_set,
        numbering_normal_axis=BackplateNormalAxis.PLUS_Y,
        numbering_direction_axis_sign=NumberingDirectionSign.POSITIVE,
        numbering_height_mm=2.0,
    )


def test_prepare_nesting_parts_simple_grouping() -> None:
    numbered = _numbered_box(extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0)
    materials = (
        MaterialDefinition(
            material_id="wood3",
            thickness_mm=3.0,
            sheet_width_mm=1000.0,
            sheet_height_mm=1000.0,
            kerf_mm=0.2,
        ),
    )

    grouped = prepare_nesting_parts(
        numbered, materials, slice_material_id="wood3", seam_marking_height_mm=5.0
    )

    assert set(grouped.keys()) == {"wood3"}
    assert len(grouped["wood3"]) == 5
    assert all(p.reference.kind == PartKind.SLICE_ISLAND for p in grouped["wood3"])


def test_prepare_nesting_parts_splits_oversized_island() -> None:
    numbered = _numbered_box(extents=(250.0, 30.0, 15.0), slice_thickness_mm=3.0)
    materials = (
        MaterialDefinition(
            material_id="wood3",
            thickness_mm=3.0,
            sheet_width_mm=100.0,
            sheet_height_mm=100.0,
            kerf_mm=0.2,
        ),
    )

    grouped = prepare_nesting_parts(
        numbered, materials, slice_material_id="wood3", seam_marking_height_mm=2.0
    )

    assert len(grouped["wood3"]) == 15  # 5 szelet x 3 darab (ceil(250/100)=3)
    first_slice_parts = [p for p in grouped["wood3"] if p.reference.slice_index == 1]
    assert len(first_slice_parts) == 3
    texts = sorted(p.numbering_marks[0].text for p in first_slice_parts)
    assert texts == ["1-1", "1-2", "1-3"]


def test_prepare_nesting_parts_spacer_disc_count() -> None:
    numbered = _numbered_box(
        extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0, gap_mm=1.0
    )
    spacer = Spacer(
        shape="cylinder",
        x_mm=0.0,
        y_mm=0.0,
        diameter_mm=5.0,
        thickness_mm=1.0,
        start_slice_index=1,
        region_id=1,
    )
    materials = (
        MaterialDefinition(
            material_id="wood3",
            thickness_mm=3.0,
            sheet_width_mm=1000.0,
            sheet_height_mm=1000.0,
            kerf_mm=0.2,
        ),
        MaterialDefinition(
            material_id="wood_thin",
            thickness_mm=0.4,
            sheet_width_mm=1000.0,
            sheet_height_mm=1000.0,
            kerf_mm=0.2,
        ),
    )

    grouped = prepare_nesting_parts(
        numbered,
        materials,
        slice_material_id="wood3",
        seam_marking_height_mm=2.0,
        spacers=(spacer,),
        spacer_material_id="wood_thin",
    )

    disc_parts = [
        p for p in grouped["wood_thin"] if p.reference.kind == PartKind.SPACER_DISC
    ]
    assert len(disc_parts) == 3  # ceil(1.0 / 0.4) = 3


def test_spacer_to_discs_dowel_based_gets_hole_contour_on_every_disc() -> None:
    """GAP_SYSTEM_SPEC.md 6. szakasz 4/a. pont / NESTING_SPEC.md 6. szakasz
    2. pont: egy Dowel-re fűzött Spacer (`dowel_diameter_mm` kitöltve)
    minden korongja 2 kontúrt kap — egy CCW külső kontúrt (változatlan
    méret) és egy CW furat-kontúrt, `dowel_diameter_mm / 2` sugárral, a
    korong középpontjával megegyező középponttal. `thickness_mm=1.0` és
    `spacer_material.thickness_mm=0.4` mellett `ceil(1.0 / 0.4) = 3`
    korong keletkezik — mindegyiket ellenőrizzük, hogy a furat ne csak
    az elsőn legyen helyes."""
    spacer = Spacer(
        shape="cylinder",
        x_mm=12.0,
        y_mm=-4.0,
        diameter_mm=5.0,
        thickness_mm=1.0,
        start_slice_index=1,
        region_id=1,
        dowel_diameter_mm=2.0,
    )
    material = MaterialDefinition(
        material_id="wood_thin",
        thickness_mm=0.4,
        sheet_width_mm=1000.0,
        sheet_height_mm=1000.0,
        kerf_mm=0.2,
    )

    discs = _spacer_to_discs(spacer, spacer_index=0, spacer_material=material)

    assert len(discs) == 3  # ceil(1.0 / 0.4) = 3
    for disc in discs:
        assert len(disc.contours) == 2
        outer, hole = disc.contours
        assert is_ccw(outer.points)
        assert not is_ccw(hole.points)

        outer_xs = [p[0] for p in outer.points]
        outer_ys = [p[1] for p in outer.points]
        assert (max(outer_xs) - min(outer_xs)) / 2 == pytest.approx(2.5, abs=1e-6)
        assert (min(outer_xs) + max(outer_xs)) / 2 == pytest.approx(12.0, abs=1e-6)
        assert (min(outer_ys) + max(outer_ys)) / 2 == pytest.approx(-4.0, abs=1e-6)

        hole_xs = [p[0] for p in hole.points]
        hole_ys = [p[1] for p in hole.points]
        assert min(hole_xs) == pytest.approx(11.0, abs=1e-6)  # 12.0 - 2.0/2
        assert max(hole_xs) == pytest.approx(13.0, abs=1e-6)  # 12.0 + 2.0/2
        assert min(hole_ys) == pytest.approx(-5.0, abs=1e-6)  # -4.0 - 2.0/2
        assert max(hole_ys) == pytest.approx(-3.0, abs=1e-6)  # -4.0 + 2.0/2
        assert hole.hole_kind is None
        assert hole.depth_mm is None


def test_spacer_to_discs_standalone_spacer_stays_single_contour() -> None:
    """Regresszió: egy önálló (nem Dowel-re fűzött, `dowel_diameter_mm=None`)
    Spacer korongja továbbra is EGYETLEN, kizárólag CCW kontúrt kap —
    a meglévő (furat előtti) viselkedés nem változik."""
    spacer = Spacer(
        shape="cylinder",
        x_mm=0.0,
        y_mm=0.0,
        diameter_mm=5.0,
        thickness_mm=1.0,
        start_slice_index=1,
        region_id=1,
    )
    material = MaterialDefinition(
        material_id="wood_thin",
        thickness_mm=0.4,
        sheet_width_mm=1000.0,
        sheet_height_mm=1000.0,
        kerf_mm=0.2,
    )

    discs = _spacer_to_discs(spacer, spacer_index=0, spacer_material=material)

    assert len(discs) == 3
    for disc in discs:
        assert len(disc.contours) == 1
        assert is_ccw(disc.contours[0].points)


def test_prepare_nesting_parts_missing_backplate_material_id_raises() -> None:
    numbered = _numbered_box(extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0)
    materials = (
        MaterialDefinition(
            material_id="wood3",
            thickness_mm=3.0,
            sheet_width_mm=1000.0,
            sheet_height_mm=1000.0,
            kerf_mm=0.2,
        ),
    )

    class _FakeBackplate:
        contours = ()
        thickness_mm = 3.0
        material_reference = None
        numbering_marks = ()

    with pytest.raises(InvalidNestingError):
        prepare_nesting_parts(
            numbered,
            materials,
            slice_material_id="wood3",
            seam_marking_height_mm=2.0,
            backplate=_FakeBackplate(),  # type: ignore[arg-type]
        )


def test_prepare_nesting_parts_missing_spacer_material_id_raises() -> None:
    numbered = _numbered_box(
        extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0, gap_mm=1.0
    )
    spacer = Spacer(
        shape="cylinder",
        x_mm=0.0,
        y_mm=0.0,
        diameter_mm=5.0,
        thickness_mm=1.0,
        start_slice_index=1,
        region_id=1,
    )
    materials = (
        MaterialDefinition(
            material_id="wood3",
            thickness_mm=3.0,
            sheet_width_mm=1000.0,
            sheet_height_mm=1000.0,
            kerf_mm=0.2,
        ),
    )

    with pytest.raises(InvalidNestingError):
        prepare_nesting_parts(
            numbered,
            materials,
            slice_material_id="wood3",
            seam_marking_height_mm=2.0,
            spacers=(spacer,),
        )


def test_prepare_nesting_parts_thickness_mismatch_raises() -> None:
    numbered = _numbered_box(extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0)
    materials = (
        MaterialDefinition(
            material_id="wood3",
            thickness_mm=5.0,
            sheet_width_mm=1000.0,
            sheet_height_mm=1000.0,
            kerf_mm=0.2,
        ),
    )

    with pytest.raises(InvalidNestingError):
        prepare_nesting_parts(
            numbered, materials, slice_material_id="wood3", seam_marking_height_mm=2.0
        )


def test_prepare_nesting_parts_negative_kerf_raises() -> None:
    numbered = _numbered_box(extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0)
    materials = (
        MaterialDefinition(
            material_id="wood3",
            thickness_mm=3.0,
            sheet_width_mm=1000.0,
            sheet_height_mm=1000.0,
            kerf_mm=-0.1,
        ),
    )

    with pytest.raises(InvalidNestingError):
        prepare_nesting_parts(
            numbered, materials, slice_material_id="wood3", seam_marking_height_mm=2.0
        )


def test_prepare_nesting_parts_invalid_seam_height_raises() -> None:
    numbered = _numbered_box(extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0)
    materials = (
        MaterialDefinition(
            material_id="wood3",
            thickness_mm=3.0,
            sheet_width_mm=1000.0,
            sheet_height_mm=1000.0,
            kerf_mm=0.2,
        ),
    )

    with pytest.raises(InvalidNestingError):
        prepare_nesting_parts(
            numbered, materials, slice_material_id="wood3", seam_marking_height_mm=0.0
        )


def test_prepare_nesting_parts_invalid_seam_min_height_raises() -> None:
    numbered = _numbered_box(extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0)
    materials = (
        MaterialDefinition(
            material_id="wood3",
            thickness_mm=3.0,
            sheet_width_mm=1000.0,
            sheet_height_mm=1000.0,
            kerf_mm=0.2,
        ),
    )

    with pytest.raises(InvalidNestingError):
        prepare_nesting_parts(
            numbered,
            materials,
            slice_material_id="wood3",
            seam_marking_height_mm=2.0,
            seam_marking_min_height_mm=5.0,
        )


def test_prepare_nesting_parts_negative_margin_raises() -> None:
    numbered = _numbered_box(extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0)
    materials = (
        MaterialDefinition(
            material_id="wood3",
            thickness_mm=3.0,
            sheet_width_mm=1000.0,
            sheet_height_mm=1000.0,
            kerf_mm=0.2,
        ),
    )

    with pytest.raises(InvalidNestingError):
        prepare_nesting_parts(
            numbered,
            materials,
            slice_material_id="wood3",
            seam_marking_height_mm=2.0,
            seam_marking_margin_mm=-1.0,
        )


def test_create_nests_simple_packing() -> None:
    numbered = _numbered_box(extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0)
    materials = (
        MaterialDefinition(
            material_id="wood3",
            thickness_mm=3.0,
            sheet_width_mm=1000.0,
            sheet_height_mm=1000.0,
            kerf_mm=0.2,
        ),
    )
    grouped = prepare_nesting_parts(
        numbered, materials, slice_material_id="wood3", seam_marking_height_mm=5.0
    )

    nests = create_nests(grouped, materials)

    assert len(nests) == 1
    nest = nests[0]
    assert nest.material_id == "wood3"
    assert nest.sheet_count == 1
    assert len(nest.placed_parts) == 5
    assert len(nest.seams) == 0
    assert nest.placed_parts[0].position == (0.0, 0.0)


def test_create_nests_uses_multiple_sheets_when_needed() -> None:
    numbered = _numbered_box(extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0)
    materials = (
        MaterialDefinition(
            material_id="wood3",
            thickness_mm=3.0,
            sheet_width_mm=32.0,
            sheet_height_mm=22.0,
            kerf_mm=0.2,
        ),
    )
    grouped = prepare_nesting_parts(
        numbered, materials, slice_material_id="wood3", seam_marking_height_mm=5.0
    )

    nests = create_nests(grouped, materials)

    assert nests[0].sheet_count == 5
    assert len(nests[0].placed_parts) == 5


def test_create_nests_orthogonal_rotation_minimizes_height() -> None:
    # A _TO_2D_ROTATION szándékos tükrözése miatt a Z-tengelyű szeletek
    # kontúr-sorrendje (Y, X)-re változott (ld. ADR-0010) — az itt
    # szeletelt doboz (X=10, Y=40) kontúrjának 0. koordinátája immár Y
    # (40 mm), az 1. X (10 mm), azaz a nyers kontúr már eleve a
    # (szélesebb, alacsonyabb) tájolásban áll — az ORTHOGONAL mód emiatt
    # NEM forgat (0°), mert a forgatás nélküli magasság (10 mm) már
    # minimális; korábban (X, Y) sorrenddel a 90°-os forgatás volt
    # szükséges ugyanehhez az eredményhez.
    numbered = _numbered_box(extents=(10.0, 40.0, 15.0), slice_thickness_mm=3.0)
    materials = (
        MaterialDefinition(
            material_id="wood3",
            thickness_mm=3.0,
            sheet_width_mm=1000.0,
            sheet_height_mm=1000.0,
            kerf_mm=0.2,
        ),
    )
    grouped = prepare_nesting_parts(
        numbered, materials, slice_material_id="wood3", seam_marking_height_mm=2.0
    )

    nests = create_nests(
        grouped, materials, nesting_rotation_mode=NestingRotationMode.ORTHOGONAL
    )

    for placed in nests[0].placed_parts:
        assert placed.rotation_deg == pytest.approx(0.0)


def test_create_nests_none_rotation_mode_never_rotates() -> None:
    numbered = _numbered_box(extents=(10.0, 40.0, 15.0), slice_thickness_mm=3.0)
    materials = (
        MaterialDefinition(
            material_id="wood3",
            thickness_mm=3.0,
            sheet_width_mm=1000.0,
            sheet_height_mm=1000.0,
            kerf_mm=0.2,
        ),
    )
    grouped = prepare_nesting_parts(
        numbered,
        materials,
        slice_material_id="wood3",
        seam_marking_height_mm=2.0,
        nesting_rotation_mode=NestingRotationMode.NONE,
    )

    nests = create_nests(
        grouped, materials, nesting_rotation_mode=NestingRotationMode.NONE
    )

    for placed in nests[0].placed_parts:
        assert placed.rotation_deg == 0.0


def test_create_nests_produces_seam_records_for_split_parts() -> None:
    numbered = _numbered_box(extents=(250.0, 30.0, 15.0), slice_thickness_mm=3.0)
    materials = (
        MaterialDefinition(
            material_id="wood3",
            thickness_mm=3.0,
            sheet_width_mm=100.0,
            sheet_height_mm=100.0,
            kerf_mm=0.2,
        ),
    )
    grouped = prepare_nesting_parts(
        numbered, materials, slice_material_id="wood3", seam_marking_height_mm=2.0
    )

    nests = create_nests(grouped, materials)

    assert len(nests[0].seams) == 5  # 5 szelet, mindegyik toldva
    for seam in nests[0].seams:
        assert len(seam.seam_lines) == 2  # 3 darabhoz 2 vágás
        assert len(seam.sub_identifiers) == 3


def test_build_text_strokes_rect_seven_not_mirrored_both_orientations() -> None:
    """Regressziós teszt a toldási/seam al-azonosítók `_glyph_point_rect()`/
    `_build_text_strokes_rect()`-jére (ADR-0010, prompt 8. szakasz),
    mindkét `upright` értékre — a "7" karakter (aszimmetrikus: teljes
    szélességű felső vízszintes vonal + a *nagyobb* gx-oldalon futó
    függőleges szár) tényleges stroke-koordinátái alapján.

    Az `upright=True` ág változatlan (már eddig is determináns +1,
    helyes) — ez csak alapvonal-ellenőrzés. A hibás `upright=False`
    ág `(anchor_x - gy, anchor_y - gx)` volt (determináns -1, tükrözve);
    a javított `(anchor_x - gy, anchor_y + gx - width_mm)` (determináns
    +1) a "7" szárát a felső vonal VÉGpontjához kapcsolva, tükrözés
    nélkül (tiszta 90°-os elforgatásnak megfelelően) helyezi el."""
    anchor_x, anchor_y, height_mm = 0.0, 0.0, 10.0

    # upright=True — nem változott, csak alapvonal-ellenőrzés.
    upright_strokes = _build_text_strokes_rect("7", height_mm, True, anchor_x, anchor_y)
    top_stroke, stem_upper_stroke, stem_lower_stroke = upright_strokes
    assert top_stroke[0] == pytest.approx((0.0, -10.0))
    assert top_stroke[1] == pytest.approx((-6.0, -10.0))
    assert stem_upper_stroke[0] == pytest.approx((-6.0, -10.0))
    assert stem_upper_stroke[1] == pytest.approx((-6.0, -5.0))
    assert stem_lower_stroke[0] == pytest.approx((-6.0, -5.0))
    assert stem_lower_stroke[1] == pytest.approx((-6.0, 0.0))

    # upright=False — a javított, nem tükrözött leképezés.
    rotated_strokes = _build_text_strokes_rect(
        "7", height_mm, False, anchor_x, anchor_y
    )
    top_stroke, stem_upper_stroke, stem_lower_stroke = rotated_strokes

    # A felső vízszintes glyph-vonal (90°-os elforgatás után függőleges
    # szakasz) a szár VÉGpontjához (`top_stroke[1]`) kapcsolódik, ami
    # egyben a szár kezdőpontja is — folytonos, nem eltört/tükrözött
    # betűalak.
    assert top_stroke[1] == pytest.approx(stem_upper_stroke[0])
    assert top_stroke[0] == pytest.approx((-10.0, -6.0))
    assert top_stroke[1] == pytest.approx((-10.0, 0.0))
    assert stem_upper_stroke[0] == pytest.approx((-10.0, 0.0))
    assert stem_upper_stroke[1] == pytest.approx((-5.0, 0.0))
    assert stem_lower_stroke[0] == pytest.approx((-5.0, 0.0))
    assert stem_lower_stroke[1] == pytest.approx((0.0, 0.0))
