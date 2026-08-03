"""DXF Export Engine — a Nesting Engine kimenetének DXF fájlokká alakítása.

Lásd: docs/specifications/DXF_EXPORT_SPEC.md.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

import ezdxf
from ezdxf.filemanagement import new as ezdxf_new

from slicedesigner.engines.exceptions import InvalidDxfExportError
from slicedesigner.engines.nesting_engine import Nest

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Export:
    """A DXF Export Engine kimenete: egy anyaglaphoz tartozó, elmentett fájl.

    Lásd: DXF_EXPORT_SPEC.md 4. szakasz.
    """

    dxf_version: str
    layer_names: tuple[str, str]
    material_id: str
    sheet_number: int
    filename: str


def export_nests_to_dxf(
    nests: tuple[Nest, ...],
    output_directory: str,
    dxf_version: str = "R12",
    cut_layer_name: str = "CUT",
    cut_layer_color: int = 1,
    engrave_layer_name: str = "ENGRAVE",
    engrave_layer_color: int = 5,
    output_filename_pattern: str = "{material_id}_sheet{sheet_number}",
) -> tuple[Export, ...]:
    """A Nesting Engine kimenetének DXF fájlokká alakítása, laponként egy fájl.

    Lásd: DXF_EXPORT_SPEC.md 6. szakasz.

    Args:
        nests: a Nesting Engine kimenete.
        output_directory: a DXF fájlok célkönyvtára (technikai
            szükségszerűség — a specifikáció csak a fájlnevet írja elő,
            a tényleges "mentéshez" célkönyvtár szükséges).
        dxf_version: a generált DXF fájlok formátumverziója.
        cut_layer_name: a vágási réteg neve.
        cut_layer_color: a vágási réteg színe (AutoCAD Color Index).
        engrave_layer_name: a gravírozási réteg neve.
        engrave_layer_color: a gravírozási réteg színe (AutoCAD Color
            Index).
        output_filename_pattern: a fájlnév-generálási minta
            (`{material_id}`/`{sheet_number}` helyettesítőkkel).

    Returns:
        Export objektumok listája, anyaglaponként egy.

    Raises:
        InvalidDxfExportError: érvénytelen/nem támogatott `dxf_version`,
            üres Nest-lista, vagy két lap azonos fájlnevet kapna.
    """
    if not nests:
        raise InvalidDxfExportError("A Nest-ek listája nem lehet üres.")

    try:
        ezdxf_new(dxfversion=dxf_version)
    except Exception as exc:
        raise InvalidDxfExportError(
            f"A dxf_version ('{dxf_version}') érvénytelen vagy nem támogatott."
        ) from exc

    sheet_entries: list[tuple[Nest, int]] = [
        (nest, sheet_number)
        for nest in nests
        for sheet_number in range(1, nest.sheet_count + 1)
    ]

    filenames = [
        output_filename_pattern.format(
            material_id=nest.material_id, sheet_number=sheet_number
        )
        for nest, sheet_number in sheet_entries
    ]
    if len(filenames) != len(set(filenames)):
        raise InvalidDxfExportError(
            "Az output_filename_pattern alapján két vagy több lap azonos fájlnevet "
            "kapna."
        )

    exports: list[Export] = []
    for (nest, sheet_number), filename in zip(sheet_entries, filenames, strict=True):
        doc = ezdxf_new(dxfversion=dxf_version)
        doc.units = ezdxf.units.MM
        doc.layers.add(name=cut_layer_name, color=cut_layer_color)
        doc.layers.add(name=engrave_layer_name, color=engrave_layer_color)
        msp = doc.modelspace()

        sheet_parts = [p for p in nest.placed_parts if p.sheet_number == sheet_number]
        for part in sheet_parts:
            for contour in part.contours:
                msp.add_polyline2d(
                    contour.points, close=True, dxfattribs={"layer": cut_layer_name}
                )
            for mark in part.numbering_marks:
                for stroke in mark.strokes:
                    msp.add_polyline2d(
                        stroke, close=False, dxfattribs={"layer": engrave_layer_name}
                    )

        full_path = Path(output_directory) / f"{filename}.dxf"
        doc.saveas(str(full_path))

        exports.append(
            Export(
                dxf_version=dxf_version,
                layer_names=(cut_layer_name, engrave_layer_name),
                material_id=nest.material_id,
                sheet_number=sheet_number,
                filename=f"{filename}.dxf",
            )
        )

    return tuple(exports)
