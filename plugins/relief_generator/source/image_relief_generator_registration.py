"""Image Relief Generator — MeshSourceDescriptor regisztráció.

Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_ORCHESTRATION.md, ADR-0017.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QDialog, QMessageBox

from plugins.relief_generator.gui.region_assignment_dialog import (
    RegionAssignmentDialog,
)
from plugins.relief_generator.source.image_relief_generator_mesh_source import (
    ImageReliefGeneratorMeshSource,
)
from plugins.relief_generator.source.image_relief_generator_parameters import (
    ImageReliefGeneratorParameters,
)
from slicedesigner.project.mesh_source_registry import (
    MeshSourceDescriptor,
    ParameterSpec,
)


def _edit_region_assignment(values: dict[str, Any]) -> str | None:
    """A `"Szerkesztés..."` gomb `ParameterSpec.editor` callable-je
    (ADR-0022) — megnyitja a `RegionAssignmentDialog`-ot.

    Args:
        values: a form jelenlegi állapota (l. `_GeneratorParameterForm.values()`).

    Returns:
        Sikeres szerkesztés után az újonnan írt ideiglenes hozzárendelési
        fájl útvonala; `None`, ha nincs kiválasztott kép, vagy a
        felhasználó megszakította a szerkesztést.
    """
    image_path = values.get("image_path", "")
    if not image_path:
        QMessageBox.warning(
            None, "Régiók szerkesztése", "Először válassz ki egy kép fájlt."
        )
        return None
    existing_assignment_path = values.get("assignment_path") or None
    dialog = RegionAssignmentDialog(
        image_path=image_path,
        existing_assignment_path=existing_assignment_path,
    )
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    return dialog.result_path


_PARAMETERS: tuple[ParameterSpec, ...] = (
    ParameterSpec(name="image_path", label="Kép fájl", type="file", default=""),
    ParameterSpec(
        name="assignment_path",
        label="Hozzárendelési fájl (JSON)",
        type="file",
        default="",
        editor=_edit_region_assignment,
    ),
    ParameterSpec(
        name="width",
        label="Szélesség",
        type="float",
        default=100.0,
        minimum=0.0,
        unit="mm",
    ),
    ParameterSpec(
        name="height",
        label="Magasság",
        type="float",
        default=100.0,
        minimum=0.0,
        unit="mm",
    ),
    ParameterSpec(
        name="base_thickness",
        label="Alapvastagság",
        type="float",
        default=3.0,
        minimum=0.0,
        unit="mm",
    ),
    ParameterSpec(
        name="relief_height_raised",
        label="Relief magasság (kiemelt)",
        type="float",
        default=2.0,
        minimum=0.0,
        unit="mm",
    ),
    ParameterSpec(
        name="relief_height_recessed",
        label="Relief mélység (süllyesztett)",
        type="float",
        default=1.0,
        minimum=0.0,
        unit="mm",
    ),
    ParameterSpec(
        name="sampling_distance",
        label="Mintavételezési távolság",
        type="float",
        default=1.0,
        minimum=0.01,
        unit="mm",
    ),
)


def _build(values: dict[str, Any]) -> ImageReliefGeneratorMeshSource:
    """A generikus `values` dict-ből `ImageReliefGeneratorMeshSource`-t épít."""
    parameters = ImageReliefGeneratorParameters(
        image_path=values["image_path"],
        assignment_path=values["assignment_path"],
        width=values["width"],
        height=values["height"],
        base_thickness=values["base_thickness"],
        relief_height_raised=values["relief_height_raised"],
        relief_height_recessed=values["relief_height_recessed"],
        sampling_distance=values["sampling_distance"],
    )
    return ImageReliefGeneratorMeshSource(parameters)


def build_mesh_source_descriptor() -> MeshSourceDescriptor:
    """Az entry point által hívott factory — l. `pyproject.toml`."""
    return MeshSourceDescriptor(
        display_name="Image Relief Generator",
        parameters=_PARAMETERS,
        build=_build,
    )
