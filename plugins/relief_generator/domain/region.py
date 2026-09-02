"""Region — az Image Relief Generator Semantic World rétegének alap
adatmodellje.

Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_REGION_MODEL.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from plugins.relief_generator.exceptions import RegionValueError


class Mask(Protocol):
    """Egy Region térbeli érvényességi tartománya — funkcionális kontraktus.

    Nincs domain-szintű materializált reprezentáció (raszter/vektor/
    implicit függvény — Image Interpretation belső backend-döntés, l.
    IMAGE_RELIEF_REGION_MODEL.md 3. szakasz).
    """

    def member(self, x: float, y: float) -> bool:
        """Eldönti, hogy a Mask az adott ponton érvényes-e.

        Args:
            x: térbeli X-koordináta, a kép közös, abszolút
                koordinátarendszerében (nem normalizált — a konkrét
                értelmezés Image Interpretation belső döntése).
            y: térbeli Y-koordináta, ugyanabban a koordinátarendszerben.

        Returns:
            `True`, ha a Mask az adott `(x, y)` ponton érvényes.
        """
        ...


class DepthBehavior(Enum):
    """Egy Region iránya a relief szempontjából (nem fizikai mélység/magasság).

    Lásd: IMAGE_RELIEF_REGION_MODEL.md 5. szakasz.
    """

    RAISED = "raised"
    RECESSED = "recessed"
    INHERIT = "inherit"


@dataclass(frozen=True)
class Region:
    """Az Image Relief Generator Semantic World rétegének alap egysége.

    A létrehozott példány immutábilis (`frozen=True`); a `contribution`
    érvényességét a `__post_init__` fail-fast ellenőrzi.

    Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_REGION_MODEL.md
    2–6. szakasz.

    Attributes:
        mask: a Region térbeli érvényességi tartománya (3. szakasz).
        contribution: milyen erősséggel járul hozzá a Region a
            reliefhez — nem negatív, nem közvetlen fizikai magasság; a
            szülő már resolvált állapotához képest relatív (4. szakasz).
        depth_behavior: a Region iránya (`Raised`/`Recessed`/`Inherit`,
            5. szakasz).
        children: a Region szemantikus/hierarchikus gyermekei — nem
            geometriai Boolean-fa (6. szakasz). Alapértelmezetten üres
            (levél Region).
    """

    mask: Mask
    contribution: float
    depth_behavior: DepthBehavior
    children: tuple["Region", ...] = ()

    def __post_init__(self) -> None:
        """Fail-fast validálja a `contribution` mezőt.

        Raises:
            RegionValueError: ha a `contribution` negatív.
        """
        if self.contribution < 0.0:
            raise RegionValueError(
                "A contribution nem lehet negatív, "
                f"kapott érték: {self.contribution}"
            )
