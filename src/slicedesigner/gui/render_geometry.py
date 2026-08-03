"""Tiszta geometriai segédfüggvények: `Mesh`/`SliceSet` → `pyvista.PolyData`.

Nem tartalmaz Qt/widget-kódot, és — az `is_ccw()` winding-vizsgálat
kivételével — nem hív engine-függvényt sem (ARCHITECTURE.md: a GUI
kizárólag a Project komponensen keresztül kommunikál, engine-t
közvetlenül nem hív). A `Mesh`/`SliceSet`/`Slice`/`Contour`/`SliceAxis`
típusok importja kivétel e szabály alól — ezek egyszerű, megosztott
domain adatstruktúrák, nem üzleti logika (lásd pl.
`gui/config_builder.py`, amely szintén importál engine-dataclass-okat).

A `_is_ccw()` a szolid/lyuk kontúr-szétválasztáshoz szükséges
winding-irány vizsgálat **saját, önálló** implementációja — szándékosan
NEM importálja az `engines/slice_engine.py` `is_ccw()`-ját, mert az
közvetlen engine-hívás lenne. A CCW = szolid, CW = lyuk konvenció a
DOWEL_SYSTEM_SPEC.md 4. szakaszában rögzített, stabil geometriai
szerződés — ez tudatos, dokumentált duplikáció, nem véletlen
kód-ismétlés.
"""

from __future__ import annotations

import numpy as np
import pyvista as pv
from shapely.geometry import LinearRing

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


def slice_set_to_polydata(slice_set: SliceSet) -> pv.PolyData:
    """A szeletelt összeállítás geometriája: minden Slice minden szolid
    (CCW) kontúrjának extrudált uniója. CW (lyuk-) kontúrok kihagyva.
    Üres Slice Set-re (`slices=()`) üres `PolyData`-t ad."""
    parts: list[pv.PolyData] = []
    for slice_ in slice_set.slices:
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
