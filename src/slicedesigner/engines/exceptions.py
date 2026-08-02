"""Közös kivétel-hierarchia a Slice Designer domain rétegéhez (engines/)."""


class SliceDesignerError(Exception):
    """A Slice Designer domain rétegének közös kivétel-bázisosztálya."""


class InvalidMeshError(SliceDesignerError):
    """A Mesh Import engine bemenete vagy a betöltött geometria érvénytelen."""
