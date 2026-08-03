"""Kivétel-hierarchia a Slice Designer koordinációs rétegéhez (project/)."""

from slicedesigner.engines.exceptions import SliceDesignerError


class PipelineConfigurationError(SliceDesignerError):
    """A pipeline konfigurációja hiányos vagy ellentmondásos.

    Akkor keletkezik, ha a három összeépítési kapcsoló (``use_spacers``,
    ``use_dowels``, ``use_backplate``) mindegyike ki van kapcsolva
    (ADR-0004), vagy ha egy bekapcsolt kapcsolóhoz nem tartozik a
    szükséges paraméter-objektum.
    """
