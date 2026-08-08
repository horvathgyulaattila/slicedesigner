"""Slice Engine — a Mesh keresztmetszeteinek (szeleteinek) előállítása.

Lásd: docs/specifications/SLICE_ENGINE_SPEC.md.
"""

import logging
from dataclasses import dataclass
from enum import Enum

import trimesh
from shapely.geometry import LinearRing, Polygon
from shapely.geometry.polygon import orient

from slicedesigner.engines.exceptions import InvalidSliceError
from slicedesigner.engines.mesh_import import Mesh

logger = logging.getLogger(__name__)

# Lebegőpontos zajszűrési küszöb (nem üzleti paraméter) annak eldöntésére,
# hogy a számított skálázási tényező ténylegesen eltér-e 1.0-tól.
_SCALE_IDENTITY_EPSILON = 1e-9


class SliceAxis(Enum):
    """A szeletelési tengely."""

    X = "X"
    Y = "Y"
    Z = "Z"


_AXIS_INDEX: dict[SliceAxis, int] = {SliceAxis.X: 0, SliceAxis.Y: 1, SliceAxis.Z: 2}

_AXIS_NORMAL: dict[SliceAxis, tuple[float, float, float]] = {
    SliceAxis.X: (1.0, 0.0, 0.0),
    SliceAxis.Y: (0.0, 1.0, 0.0),
    SliceAxis.Z: (0.0, 0.0, 1.0),
}

# Explicit, kézzel megkonstruált 2D-vetítési mátrixok tengelyenként, a
# `trimesh.Path3D.to_2D(to_2D=...)` számára.
#
# TÖRTÉNETI MEGJEGYZÉS (2026-08-08-i audit, ld. ADR-0010): ez a mátrix-
# készlet korábban SZÁNDÉKOSAN tisztán forgatás volt (determináns +1,
# tükrözés nélkül) — ez volt a DXF-exportban jelentkező, ismételten
# jelentett tükröződés valódi, addig fel nem ismert gyökéroka. Az audit
# bizonyította (mátrix-elemzéssel ÉS egy, a projektgazda saját, élőben
# validált, korábbi CAM-workaround-jával való összevetéssel), hogy a
# helyes vetítéshez PONTOSAN EGY tükrözés szükséges, egységesen mind a
# három tengelyválasztásra — ellenkező esetben a kontúr a fizikai
# modellhez képest tükrözve jelenik meg. A mátrixok ezért most
# determináns -1-gyel, szándékos tükrözéssel készülnek: az előző
# (forgatás-only) verzióhoz képest az első két sor fel van cserélve.
# A konkrét tükrözési tengely megválasztása bizonyítottan közömbös
# (egy forgatás erejéig egyenértékű bármely másik választással), mivel
# a Nesting Engine szabadon forgatja az alkatrészeket lap-elrendezéskor,
# és a betű-rajzolás (`numbering_engine.py::_glyph_to_local`) igazoltan
# független attól, melyik konkrét tengely melyik szerepet kapja.
_TO_2D_ROTATION: dict[SliceAxis, list[list[float]]] = {
    # kontúr = (+Y, +X)
    SliceAxis.Z: [
        [0.0, 1.0, 0.0, 0.0],
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ],
    # kontúr = (+Z, +Y)
    SliceAxis.X: [
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ],
    # kontúr = (+X, +Z)
    SliceAxis.Y: [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ],
}

# A Slice Engine kontúr-koordinátáinak világtengely-sorrendje — a fenti
# `_TO_2D_ROTATION`-nal KÖTELEZŐEN szinkronban tartandó egyetlen forrás.
# A Backplate és Numbering Engine ezt importálja (nem duplikálja) — ld.
# ADR-0010: a korábbi, egymástól függetlenül kézzel karbantartott
# másolatok (mindkét engine-ben `_SLICE_AXIS_CONTOUR_ORDER` néven) az
# audit során talált hibaosztály egyik oka voltak.
_SLICE_AXIS_CONTOUR_ORDER: dict[SliceAxis, tuple[str, str]] = {
    SliceAxis.Z: ("Y", "X"),
    SliceAxis.X: ("Z", "Y"),
    SliceAxis.Y: ("X", "Z"),
}


class HoleKind(Enum):
    """Egy CW (lyuk-) kontúr eredetének/típusának megkülönböztetése.

    Lásd: DOWEL_SYSTEM_SPEC.md 4. szakasz.
    """

    DOWEL_THROUGH = "dowel_through"
    DOWEL_BLIND = "dowel_blind"


@dataclass(frozen=True)
class Contour:
    """Egy zárt kontúr a szeletelési síkban, 2D pontlistaként (mm).

    A körüljárási irány hordozza a jelentést: óramutató járásával
    ellentétes (CCW) = szilárd anyag (sziget) határa; óramutató
    járásával megegyező (CW) = kivágott lyuk határa
    (DOWEL_SYSTEM_SPEC.md 4. szakasz).

    A `hole_kind` és `depth_mm` a Slice Engine által előállított,
    egyszerű geometriai lyukaknál (és minden szolid határnál) `None` —
    kizárólag a Dowel Engine által vágott Dowel Hole-oknál kerül
    kitöltésre (DOWEL_SYSTEM_SPEC.md 4. szakasz).
    """

    points: tuple[tuple[float, float], ...]
    hole_kind: HoleKind | None = None
    depth_mm: float | None = None


@dataclass(frozen=True)
class EngravingMark:
    """Egy gravírozási jel (pl. egy azonosító-szöveg) nyitott vonal-strokejai.

    A `strokes` minden eleme egy nyitott poliline (2 vagy több pont) — NEM
    zárt hurok, ezért nem `Contour` (ami zárt kontúrt, szolid/lyuk
    megkülönböztetést feltételez). A gravírozás sem nem szilárd anyag,
    sem nem lyuk — felületi jelölés (NUMBERING_SPEC.md 4. szakasz).
    """

    text: str
    strokes: tuple[tuple[tuple[float, float], ...], ...]
    height_mm: float
    island_index: int


@dataclass(frozen=True)
class Slice:
    """Egyetlen szelet a Slice Set-en belül.

    Lásd: SLICE_ENGINE_SPEC.md 4. szakasz.

    A `numbering_marks` a Numbering Engine által elhelyezett azonosító
    gravírozás-jeleit tartalmazza (alapértelmezetten üres — a Slice
    Engine maga nem numeráz).
    """

    thickness_mm: float
    contours: tuple[Contour, ...]
    position_mm: float
    index: int
    numbering_marks: tuple[EngravingMark, ...] = ()


@dataclass(frozen=True)
class SliceSet:
    """A Slice Engine kimenete: egy Mesh-hez tartozó szeletek összessége.

    Lásd: SLICE_ENGINE_SPEC.md 4. szakasz.

    A `slice_axis` a Slice Engine hívásakor használt szeletelési tengelyt
    rögzíti — a downstream engine-eknek (pl. Backplate) szükségük van rá
    a kontúr-koordináták valós tengelyekhez való hozzárendeléséhez.
    Alapértéke `SliceAxis.Z`, hogy a kézzel épített (teszt-)SliceSetek,
    amelyek nem adják meg explicit módon, ne törjenek — a tényleges
    `create_slice_set()` hívás mindig explicit módon adja át.
    """

    source_mesh: Mesh
    gap_mm: float
    slices: tuple[Slice, ...]
    slice_count: int
    slice_axis: SliceAxis = SliceAxis.Z


def _compute_uniform_scale_factor(
    axis_size: float, slice_count: int, slice_thickness_mm: float, gap_mm: float
) -> float:
    """A Mesh egységes skálázási tényezője, amivel a `slice_count` db,
    `slice_thickness_mm` vastag szelet (`gap_mm` réssel köztük) pontosan
    kiadja a szeletelési tengely menti céloméretet.

    Megosztott logika a Slice Engine (`create_slice_set`) és a Backplate
    Engine (a Backplate-alak Boole-metszetéhez szükséges, azonos módon
    skálázott Mesh előállításához) között — egyetlen forrásból, elkerülve
    a korábban már egyszer hibát okozó (`render_geometry.py`/
    `numbering_engine.py` önálló, elavult közelítései miatti)
    duplikációt.
    """
    target_size = slice_count * slice_thickness_mm + (slice_count - 1) * gap_mm
    return target_size / axis_size


def create_slice_set(
    mesh: Mesh,
    slice_thickness_mm: float,
    slice_axis: SliceAxis = SliceAxis.Z,
    gap_mm: float = 0.0,
    max_scale_tolerance: float = 0.02,
) -> SliceSet:
    """A Mesh keresztmetszeteinek előállítása a szeletelési tengely mentén.

    Args:
        mesh: a Mesh Import kimenete.
        slice_thickness_mm: az egyes szeletek vastagsága (mm).
        slice_axis: a szeletelési tengely.
        gap_mm: a szeletek közötti tervezett hézag (mm).
        max_scale_tolerance: a Mesh méretének maximálisan megengedett
            arányos eltérése, amit a rendszer egységes skálázással
            kompenzál (SLICE_ENGINE_SPEC.md 5. szakasz).

    Returns:
        A pozicionált Slice Set.

    Raises:
        InvalidSliceError: érvénytelen `slice_thickness_mm`/`gap_mm`, üres
            Mesh, nulla méret a szeletelési tengely mentén, a számított
            szeletszám (N) 1-nél kisebb, a szükséges skálázás meghaladja
            `max_scale_tolerance`-t, vagy egy metszősík üres/nyitott
            keresztmetszetet eredményez.
    """
    if slice_thickness_mm <= 0:
        raise InvalidSliceError(
            "A slice_thickness_mm értékének pozitívnak kell lennie: "
            f"{slice_thickness_mm}"
        )
    if gap_mm < 0:
        raise InvalidSliceError(f"A gap_mm értéke nem lehet negatív: {gap_mm}")
    if not mesh.vertices or not mesh.triangles:
        raise InvalidSliceError("A Mesh üres, nem szeletelhető.")

    axis_index = _AXIS_INDEX[slice_axis]
    axis_size = mesh.bounding_box.max[axis_index] - mesh.bounding_box.min[axis_index]
    if axis_size <= 0:
        raise InvalidSliceError(
            f"A Mesh mérete nulla a szeletelési tengely ({slice_axis.value}) mentén."
        )

    slice_count = round((axis_size + gap_mm) / (slice_thickness_mm + gap_mm))
    if slice_count < 1:
        raise InvalidSliceError(
            f"A számított szeletszám érvénytelen ({slice_count}); "
            "ellenőrizd a slice_thickness_mm és gap_mm értékét."
        )

    target_size = slice_count * slice_thickness_mm + (slice_count - 1) * gap_mm
    relative_deviation = abs(target_size - axis_size) / axis_size
    if relative_deviation > max_scale_tolerance:
        raise InvalidSliceError(
            f"A szükséges skálázás ({relative_deviation:.4f}) meghaladja a "
            f"max_scale_tolerance értékét ({max_scale_tolerance})."
        )

    scale_factor = _compute_uniform_scale_factor(
        axis_size, slice_count, slice_thickness_mm, gap_mm
    )
    trimesh_mesh = trimesh.Trimesh(vertices=mesh.vertices, faces=mesh.triangles)
    if abs(scale_factor - 1.0) > _SCALE_IDENTITY_EPSILON:
        scale_matrix = [
            [scale_factor, 0.0, 0.0, 0.0],
            [0.0, scale_factor, 0.0, 0.0],
            [0.0, 0.0, scale_factor, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
        trimesh_mesh.apply_transform(scale_matrix)
        logger.warning(
            "A Mesh egységesen átskálázva (arány: %.6f) a %s tengely mentén "
            "%.4f mm céloméret eléréséhez.",
            scale_factor,
            slice_axis.value,
            target_size,
        )

    bounds = trimesh_mesh.bounds
    axis_min = float(bounds[0][axis_index])

    plane_normal = _AXIS_NORMAL[slice_axis]

    positions = [
        i * (slice_thickness_mm + gap_mm) + slice_thickness_mm / 2
        for i in range(slice_count)
    ]

    slices: list[Slice] = []
    for i, position in enumerate(positions, start=1):
        plane_origin = [0.0, 0.0, 0.0]
        plane_origin[axis_index] = axis_min + position

        path3d = trimesh_mesh.section(
            plane_origin=plane_origin, plane_normal=plane_normal
        )
        if path3d is None:
            raise InvalidSliceError(
                f"A(z) {i}. szeletnél ({position:.4f} mm pozíció) a metszősík "
                "üres keresztmetszetet eredményezett."
            )
        path2d, _to_3d = path3d.to_2D(to_2D=_TO_2D_ROTATION[slice_axis])
        if not path2d.is_closed:
            raise InvalidSliceError(
                f"A(z) {i}. szeletnél ({position:.4f} mm pozíció) a metszősík "
                "nyitott (nem zárt) keresztmetszetet eredményezett."
            )

        contours: list[Contour] = []
        for polygon in path2d.polygons_full:
            oriented = orient(polygon, sign=1.0)
            contours.append(
                Contour(
                    points=tuple(
                        (float(x), float(y)) for x, y in oriented.exterior.coords[:-1]
                    )
                )
            )
            for interior in oriented.interiors:
                contours.append(
                    Contour(
                        points=tuple(
                            (float(x), float(y)) for x, y in interior.coords[:-1]
                        )
                    )
                )

        slices.append(
            Slice(
                thickness_mm=slice_thickness_mm,
                contours=tuple(contours),
                position_mm=position,
                index=i,
            )
        )

    return SliceSet(
        source_mesh=mesh,
        slice_axis=slice_axis,
        gap_mm=gap_mm,
        slices=tuple(slices),
        slice_count=slice_count,
    )


def is_ccw(points: tuple[tuple[float, float], ...]) -> bool:
    """Egy zárt kontúr pontjainak körüljárási iránya (True = CCW = szilárd határ)."""
    return bool(LinearRing(points).is_ccw)


@dataclass(frozen=True)
class Island:
    """Egy Slice-on belüli, geometriailag különálló anyagrész (szolid + lyukak).

    Megosztott segédtípus a lyuk-vs-sziget megkülönböztetést igénylő
    downstream engine-ek (Dowel, Gap) számára.
    """

    slice_index: int
    solid: Contour
    holes: tuple[Contour, ...]
    polygon: Polygon


def reconstruct_islands(slice_: Slice) -> list[Island]:
    """Egy Slice lapos kontúrlistájából szigetek (szolid + hozzá tartozó lyukak)
    építése."""
    solids = [c for c in slice_.contours if is_ccw(c.points)]
    holes = [c for c in slice_.contours if not is_ccw(c.points)]

    islands: list[Island] = []
    for solid in solids:
        solid_polygon = Polygon(solid.points)
        own_holes = [
            h
            for h in holes
            if solid_polygon.contains(Polygon(h.points).representative_point())
        ]
        island_polygon = Polygon(solid.points, holes=[h.points for h in own_holes])
        islands.append(
            Island(
                slice_index=slice_.index,
                solid=solid,
                holes=tuple(own_holes),
                polygon=island_polygon,
            )
        )
    return islands
