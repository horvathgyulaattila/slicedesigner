"""Közös kivétel-hierarchia a Slice Designer domain rétegéhez (engines/)."""


class SliceDesignerError(Exception):
    """A Slice Designer domain rétegének közös kivétel-bázisosztálya."""


class InvalidMeshError(SliceDesignerError):
    """A Mesh Import engine bemenete vagy a betöltött geometria érvénytelen."""


class InvalidSliceError(SliceDesignerError):
    """A Slice Engine bemenete érvénytelen, vagy a szeletelés nem végezhető el."""


class InvalidDowelError(SliceDesignerError):
    """A Dowel Engine bemenete érvénytelen, vagy a Dowel-elhelyezés nem végezhető el."""


class InvalidGapError(SliceDesignerError):
    """A Gap Engine bemenete érvénytelen, vagy a Spacer-elhelyezés nem végezhető el."""


class InvalidBackplateError(SliceDesignerError):
    """A Backplate Engine bemenete érvénytelen, vagy a csap-elhelyezés nem
    végezhető el."""
