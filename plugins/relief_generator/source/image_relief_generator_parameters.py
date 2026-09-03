"""Image Relief Generator MeshSource paraméterei — a teljes generálási
lánc bemenete.

Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_ORCHESTRATION.md.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ImageReliefGeneratorParameters:
    """Az Image Relief Generator MeshSource-adapterének bemeneti paraméterei.

    Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_ORCHESTRATION.md.

    Attributes:
        image_path: a színkódolt régió-térkép fájlútvonala.
        assignment_path: a hozzárendelési JSON fájlútvonala.
        width: a felszín fizikai X-kiterjedése.
        height: a felszín fizikai Y-kiterjedése.
        base_thickness: a relief "nulla" síkjának Z-koordinátája.
        relief_height_raised: a Raised irány terjedelme.
        relief_height_recessed: a Recessed irány terjedelme.
        sampling_distance: a Raw Mesh mintavételezési sűrűsége.
    """

    image_path: str
    assignment_path: str
    width: float
    height: float
    base_thickness: float
    relief_height_raised: float
    relief_height_recessed: float
    sampling_distance: float
