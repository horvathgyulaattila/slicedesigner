"""Tiszta geometriai segédfüggvények: `Mesh`/`SliceSet` → `pyvista.PolyData`.

Nem tartalmaz Qt/widget-kódot, és — az `is_ccw()` winding-vizsgálat
kivételével — nem hív engine-függvényt sem (ARCHITECTURE.md: a GUI
kizárólag a Project komponensen keresztül kommunikál, engine-t
közvetlenül nem hív). A `Mesh`/`SliceSet`/`Slice`/`Contour`/`SliceAxis`/
`Backplate`/`BackplateNormalAxis` típusok importja kivétel e szabály
alól — ezek egyszerű, megosztott domain adatstruktúrák/enumok, nem
üzleti logika (lásd pl. `gui/config_builder.py`, amely szintén importál
engine-dataclass-okat).

A `_is_ccw()` a szolid/lyuk kontúr-szétválasztáshoz szükséges
winding-irány vizsgálat **saját, önálló** implementációja — szándékosan
NEM importálja az `engines/slice_engine.py` `is_ccw()`-ját, mert az
közvetlen engine-hívás lenne. A CCW = szolid, CW = lyuk konvenció a
DOWEL_SYSTEM_SPEC.md 4. szakaszában rögzített, stabil geometriai
szerződés — ez tudatos, dokumentált duplikáció, nem véletlen
kód-ismétlés.

Ugyanígy a `_NORMAL_AXIS_WORLD`/`_WORLD_AXIS_INDEX` (a Backplate
`(harmadik tengely, slice_axis)` síkjának world-tengelyekhez
rendeléséhez) a `backplate_engine.py` `_NORMAL_AXIS_WORLD`/
`_WORLD_AXIS_INDEX`-mintáját követő, **önálló, duplikált**
leképezés — csak olvasásra ellenőrizve, nem importálva, ugyanazon
indoklással, mint `_is_ccw()`.
"""

from __future__ import annotations

import numpy as np
import pyvista as pv
from shapely.geometry import LinearRing

from slicedesigner.engines.backplate_engine import Backplate, BackplateNormalAxis
from slicedesigner.engines.dowel_engine import DowelPosition
from slicedesigner.engines.gap_engine import Spacer
from slicedesigner.engines.mesh_import import Mesh
from slicedesigner.engines.slice_engine import Slice, SliceAxis, SliceSet

# A kontúr 2D (u, v) koordinátáinak world-tengelyekhez rendelése
# `slice_axis` szerint: (extrudálási tengely indexe, (u-tengely indexe,
# v-tengely indexe)). Ugyanaz a ciklikus leképezés, mint amit a
# Backplate/Numbering Engine használ a kontúr-koordináták valós
# tengelyekhez rendelésére (lásd `backplate_engine.py`/
# `numbering_engine.py` `_SLICE_AXIS_CONTOUR_ORDER`, csak olvasásra
# ellenőrizve, nem importálva).
_AXIS_MAPPING: dict[SliceAxis, tuple[int, tuple[int, int]]] = {
    SliceAxis.Z: (2, (0, 1)),
    SliceAxis.X: (0, (1, 2)),
    SliceAxis.Y: (1, (2, 0)),
}

# A `backplate_normal_axis` világtengelyhez/előjelhez rendelése — a
# `backplate_engine.py` `_NORMAL_AXIS_WORLD`-jének duplikátuma (lásd a
# modul docstringjét).
_NORMAL_AXIS_WORLD: dict[BackplateNormalAxis, tuple[str, float]] = {
    BackplateNormalAxis.PLUS_X: ("X", 1.0),
    BackplateNormalAxis.MINUS_X: ("X", -1.0),
    BackplateNormalAxis.PLUS_Y: ("Y", 1.0),
    BackplateNormalAxis.MINUS_Y: ("Y", -1.0),
    BackplateNormalAxis.PLUS_Z: ("Z", 1.0),
    BackplateNormalAxis.MINUS_Z: ("Z", -1.0),
}

# Világtengely-név → numpy-tengelyindex — a `backplate_engine.py`
# `_WORLD_AXIS_INDEX`-jének duplikátuma.
_WORLD_AXIS_INDEX: dict[str, int] = {"X": 0, "Y": 1, "Z": 2}


def _is_ccw(points: tuple[tuple[float, float], ...]) -> bool:
    """Egy zárt kontúr pontjainak körüljárási iránya.

    True = CCW = szolid határ, False = CW = lyuk határa
    (DOWEL_SYSTEM_SPEC.md 4. szakasz; vö. `engines/slice_engine.py`
    `is_ccw()` — szándékos, dokumentált duplikáció, lásd a modul
    docstringjét).
    """
    return bool(LinearRing(points).is_ccw)


def mesh_to_polydata(mesh: Mesh) -> pv.PolyData:
    """Az eredeti Mesh (`vertices`/`triangles`) átalakítása `PolyData`-vá,
    rekonstrukció nélkül. Üres Mesh-re üres `PolyData`-t ad."""
    if not mesh.vertices or not mesh.triangles:
        return pv.PolyData()

    points = np.array(mesh.vertices, dtype=float)
    faces = np.empty((len(mesh.triangles), 4), dtype=np.int64)
    faces[:, 0] = 3
    faces[:, 1:] = np.array(mesh.triangles, dtype=np.int64)
    return pv.PolyData(points, faces.reshape(-1))


def _extrude_contour(
    points: tuple[tuple[float, float], ...],
    slice_axis: SliceAxis,
    position_mm: float,
    thickness_mm: float,
) -> pv.PolyData:
    """Egy szolid kontúr extrudálása a `slice_axis` mentén, `position_mm`
    körül középre igazítva (a szelet `position_mm - thickness_mm/2` és
    `position_mm + thickness_mm/2` közötti sávot tölti ki — ugyanaz a
    konvenció, mint a domain rétegben)."""
    axis_index, (u_index, v_index) = _AXIS_MAPPING[slice_axis]

    coords = np.zeros((len(points), 3), dtype=float)
    coords[:, axis_index] = position_mm - thickness_mm / 2
    for row, (u, v) in zip(coords, points, strict=True):
        row[u_index] = u
        row[v_index] = v

    n = len(points)
    footprint = pv.PolyData(coords, faces=[n, *range(n)])
    triangulated = footprint.triangulate()

    vector = [0.0, 0.0, 0.0]
    vector[axis_index] = thickness_mm
    extruded: pv.PolyData = triangulated.extrude(vector, capping=True)
    return extruded


def _solid_contours(slice_: Slice) -> list[tuple[tuple[float, float], ...]]:
    return [c.points for c in slice_.contours if _is_ccw(c.points)]


def slice_set_to_polydata(
    slice_set: SliceSet, exclude_slice_index: int | None = None
) -> pv.PolyData:
    """A szeletelt összeállítás geometriája: minden Slice minden szolid
    (CCW) kontúrjának extrudált uniója. CW (lyuk-) kontúrok kihagyva.
    Üres Slice Set-re (`slices=()`) üres `PolyData`-t ad.

    `exclude_slice_index` (alapérték `None` — semmi nem marad ki, ez a
    korábbi viselkedés) esetén az adott `index`-ű Slice kimarad az
    extrudálásból — a szeletenkénti kiemeléshez, hogy a kiemelt szelet
    saját, külön rétege ne fedje egybe (z-fighting) az alap-
    összeállítással, lásd `single_slice_to_polydata()`."""
    parts: list[pv.PolyData] = []
    for slice_ in slice_set.slices:
        if slice_.index == exclude_slice_index:
            continue
        for points in _solid_contours(slice_):
            parts.append(
                _extrude_contour(
                    points,
                    slice_set.slice_axis,
                    slice_.position_mm,
                    slice_.thickness_mm,
                )
            )

    if not parts:
        return pv.PolyData()

    assembly = parts[0]
    for part in parts[1:]:
        assembly = assembly.merge(part)
    return assembly


def single_slice_to_polydata(slice_set: SliceSet, slice_index: int) -> pv.PolyData:
    """Kizárólag a `slice_index`-ű Slice szolid (CCW) kontúrjainak
    extrudált uniója — a szeletenkénti kiemeléshez, a `slice_set_to_polydata()`
    `exclude_slice_index`-ével párban használva. Ha nincs ilyen `index`-ű
    Slice, üres `PolyData`-t ad."""
    parts: list[pv.PolyData] = [
        _extrude_contour(
            points, slice_set.slice_axis, slice_.position_mm, slice_.thickness_mm
        )
        for slice_ in slice_set.slices
        if slice_.index == slice_index
        for points in _solid_contours(slice_)
    ]
    return _merge_parts(parts)


def _merge_parts(parts: list[pv.PolyData]) -> pv.PolyData:
    if not parts:
        return pv.PolyData()

    assembly = parts[0]
    for part in parts[1:]:
        assembly = assembly.merge(part)
    return assembly


def _embed_point(
    u: float, v: float, axis_value: float, slice_axis: SliceAxis
) -> np.ndarray:
    """Egy (u, v) kontúr-koordináta 3D world-pontba ágyazása `axis_value`
    tengely-menti koordinátával, `_AXIS_MAPPING` szerint."""
    axis_index, (u_index, v_index) = _AXIS_MAPPING[slice_axis]
    point = np.zeros(3, dtype=float)
    point[axis_index] = axis_value
    point[u_index] = u
    point[v_index] = v
    return point


def dowel_positions_to_polydata(
    dowel_positions: tuple[DowelPosition, ...], slice_set: SliceSet
) -> pv.PolyData:
    """Minden `DowelPosition` egy hengerként (`pv.Cylinder`), a
    `slice_set.slice_axis` mentén.

    A henger tengely-menti kezdő/záró koordinátája a `start_slice_index`/
    `end_slice_index` szerinti Slice külső síkjai
    (`position_mm ∓ thickness_mm/2`) — ugyanaz a számítás, mint amit a
    `dowel_engine.py` `_dowel_length_mm()`-je is használ, a Dowel saját
    `length_mm` mezőjét nem trusztolva vakon. Üres bemenetre üres
    `PolyData`-t ad.
    """
    if not dowel_positions:
        return pv.PolyData()

    axis_index, _ = _AXIS_MAPPING[slice_set.slice_axis]
    slices_by_index = {s.index: s for s in slice_set.slices}

    parts: list[pv.PolyData] = []
    for dowel in dowel_positions:
        start_slice = slices_by_index[dowel.start_slice_index]
        end_slice = slices_by_index[dowel.end_slice_index]
        start_outer = start_slice.position_mm - start_slice.thickness_mm / 2
        end_outer = end_slice.position_mm + end_slice.thickness_mm / 2

        center = _embed_point(
            dowel.x_mm, dowel.y_mm, (start_outer + end_outer) / 2, slice_set.slice_axis
        )
        direction = np.zeros(3, dtype=float)
        direction[axis_index] = 1.0

        parts.append(
            pv.Cylinder(
                center=center,
                direction=direction,
                radius=dowel.diameter_mm / 2,
                height=end_outer - start_outer,
            )
        )

    return _merge_parts(parts)


def dowel_hole_contours_to_polydata(slice_set: SliceSet) -> pv.PolyData:
    """Minden Slice minden `hole_kind is not None` kontúrja, vonalként
    (nem kitöltött felületként), a Slice mindkét síkján
    (`position_mm ∓ thickness_mm/2`), zárt hurokként.

    Kizárólag `lines` connectivityt használ — `faces`/`polys` nélkül,
    hogy körvonalként, ne kitöltött korongként jelenjen meg. Üres
    Slice Set-re, vagy ha egyetlen Slice sem tartalmaz lyuk-kontúrt, üres
    `PolyData`-t ad.
    """
    parts: list[pv.PolyData] = []
    for slice_ in slice_set.slices:
        for contour in slice_.contours:
            if contour.hole_kind is None:
                continue
            n = len(contour.points)
            for axis_value in (
                slice_.position_mm - slice_.thickness_mm / 2,
                slice_.position_mm + slice_.thickness_mm / 2,
            ):
                coords = np.array(
                    [
                        _embed_point(u, v, axis_value, slice_set.slice_axis)
                        for u, v in contour.points
                    ]
                )
                lines = [n + 1, *range(n), 0]
                parts.append(pv.PolyData(coords, lines=lines))

    return _merge_parts(parts)


def spacers_to_polydata(
    spacers: tuple[Spacer, ...], slice_set: SliceSet
) -> pv.PolyData:
    """Minden `Spacer` egy vékony hengerként (`diameter_mm`,
    `thickness_mm`), a `start_slice_index` szerinti Slice felső síkjától
    (`position_mm + thickness_mm/2`) induló, `thickness_mm` hosszú
    szakaszon. Üres bemenetre üres `PolyData`-t ad.
    """
    if not spacers:
        return pv.PolyData()

    axis_index, _ = _AXIS_MAPPING[slice_set.slice_axis]
    slices_by_index = {s.index: s for s in slice_set.slices}

    parts: list[pv.PolyData] = []
    for spacer in spacers:
        start_slice = slices_by_index[spacer.start_slice_index]
        start_top = start_slice.position_mm + start_slice.thickness_mm / 2
        end = start_top + spacer.thickness_mm

        center = _embed_point(
            spacer.x_mm, spacer.y_mm, (start_top + end) / 2, slice_set.slice_axis
        )
        direction = np.zeros(3, dtype=float)
        direction[axis_index] = 1.0

        parts.append(
            pv.Cylinder(
                center=center,
                direction=direction,
                radius=spacer.diameter_mm / 2,
                height=spacer.thickness_mm,
            )
        )

    return _merge_parts(parts)


def _backplate_inner_plane_mm(
    slice_set: SliceSet, normal_world_index: int, sign: float
) -> float:
    """A Backplate belső (az összeállítás felé néző) síkjának world-
    koordinátája, `normal_world_index` világtengely mentén.

    A `Backplate` objektum ezt nem tárolja explicit (az engine belsejében
    számolódik, lásd a prompt "Fontos, nyitott bizonytalanság" szakaszát)
    — ezért közelítésként a már meglévő, szolid (CCW) Slice-kontúr-
    pontok (ugyanazok, amiket `slice_set_to_polydata()` is használ)
    `normal_world_index` tengely menti szélsőértékét vesszük:
    `sign > 0` (`PLUS_*`) esetén a maximumot, egyébként (`MINUS_*`) a
    minimumot. Ez nem bit-pontosan az engine belső "közös érintkezési
    sík" számítása, de a `backplate_plane_tolerance_mm` (alapértelmezetten
    0.1 mm) miatt vizuálisan megkülönböztethetetlen attól.
    """
    axis_index, (u_index, v_index) = _AXIS_MAPPING[slice_set.slice_axis]
    if normal_world_index == u_index:
        coord_pos = 0
    elif normal_world_index == v_index:
        coord_pos = 1
    else:
        raise ValueError("A backplate_normal_axis nem eshet egybe a slice_axis-szal.")

    values = [
        point[coord_pos]
        for slice_ in slice_set.slices
        for points in _solid_contours(slice_)
        for point in points
    ]
    if not values:
        return 0.0
    return max(values) if sign > 0 else min(values)


def backplate_to_polydata(
    backplate: Backplate | None,
    slice_set: SliceSet,
    backplate_normal_axis: BackplateNormalAxis,
) -> pv.PolyData:
    """A Backplate szolid (CCW) kontúrjainak extrudálása `thickness_mm`
    mélységben, `backplate_normal_axis` mentén kifelé (az összeállítástól
    távolodva).

    A `Backplate.contours` a saját (harmadik tengely, `slice_axis`)
    síkjában él (`engines/backplate_engine.py` `Backplate` docstring) —
    ezt a 2D `(u, v)` pontpárt `u` → harmadik tengely, `v` → `slice_axis`
    szerint ágyazzuk world-koordinátákba. A belső (összeállítás felé
    néző) sík world-koordinátáját `_backplate_inner_plane_mm()`
    közelíti. `backplate=None` esetén (a `use_backplate` kapcsoló ki
    volt kapcsolva) üres `PolyData`-t ad.
    """
    if backplate is None:
        return pv.PolyData()

    normal_world_axis, sign = _NORMAL_AXIS_WORLD[backplate_normal_axis]
    normal_index = _WORLD_AXIS_INDEX[normal_world_axis]
    third_world_axis = next(
        iter({"X", "Y", "Z"} - {normal_world_axis, slice_set.slice_axis.value})
    )
    third_index = _WORLD_AXIS_INDEX[third_world_axis]
    slice_axis_index, _ = _AXIS_MAPPING[slice_set.slice_axis]

    inner_plane_mm = _backplate_inner_plane_mm(slice_set, normal_index, sign)

    parts: list[pv.PolyData] = []
    for contour in backplate.contours:
        if not _is_ccw(contour.points):
            continue

        n = len(contour.points)
        coords = np.zeros((n, 3), dtype=float)
        coords[:, normal_index] = inner_plane_mm
        for row, (u, v) in zip(coords, contour.points, strict=True):
            row[third_index] = u
            row[slice_axis_index] = v

        footprint = pv.PolyData(coords, faces=[n, *range(n)])
        triangulated = footprint.triangulate()

        vector = [0.0, 0.0, 0.0]
        vector[normal_index] = sign * backplate.thickness_mm
        parts.append(triangulated.extrude(vector, capping=True))

    return _merge_parts(parts)
