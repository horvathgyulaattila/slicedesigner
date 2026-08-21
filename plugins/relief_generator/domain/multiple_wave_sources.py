"""Multiple Wave Sources — explicit, felhasználói szinten megadható
hullámforrás-lista (ROADMAP Phase 9.4: Multiple wave sources).

A `WaveSourceSpec` egy explicit hullámforrás specifikációja; a
`build_wave` egyetlen specifikációból épít konkrét `Wave`-et; a
`build_combined_wave_set` az automatikus generálásból származó
`Wave`-lista és az explicit forráslista determinisztikus összefűzéséből
épít végső `WaveSet`-et.

Lásd: docs/plugins/relief_generator/MULTIPLE_WAVE_SOURCES.md. A tényleges
`WaveParameters`/`WaveGenerator`/GUI-bekötés a ROADMAP 9.7 (Integration)
hatóköre — ez a modul önmagában, a `WaveGenerator` módosítása nélkül
tesztelhető domain-építőelem.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, cast

from plugins.relief_generator.domain.radial_wave_source import RadialPropagation
from plugins.relief_generator.domain.wave import (
    DirectionalPropagation,
    Sinusoidal,
    UniformEnvelope,
    Wave,
    WaveSet,
)
from plugins.relief_generator.exceptions import WaveSourceSpecValueError

SourceType = Literal["Directional", "Radial"]


@dataclass(frozen=True)
class WaveSourceSpec:
    """Egy explicit hullámforrás felhasználó által megadható specifikációja.

    Lásd: MULTIPLE_WAVE_SOURCES.md 4. szakasz. A típus-specifikus mezők
    (`direction`, illetve `source_x`/`source_y`) közül kizárólag a
    `source_type`-nak megfelelők adhatók meg; a `__post_init__` ezt és a
    `WAVE_DOMAIN_MODEL.md` invariánsait (`amplitude > 0`,
    `wavelength > 0`) fail-fast ellenőrzi.

    Attributes:
        source_type: `"Directional"` vagy `"Radial"`.
        amplitude: a forrás amplitúdója. Szigorúan pozitív.
        wavelength: a forrás hullámhossza. Szigorúan pozitív.
        phase: a forrás fáziseltolása, véges numerikus érték.
        weight: a forrás hozzájárulása a `WaveSet` eredményéhez.
            Alapértelmezett: `1.0`.
        direction: `source_type="Directional"` esetén kötelező, a hullám
            iránya fokban. `source_type="Radial"` esetén meg nem adható
            (`None`).
        source_x: `source_type="Radial"` esetén kötelező, a forrás
            X-koordinátája. `source_type="Directional"` esetén meg nem
            adható (`None`).
        source_y: `source_type="Radial"` esetén kötelező, a forrás
            Y-koordinátája. `source_type="Directional"` esetén meg nem
            adható (`None`).
    """

    source_type: SourceType
    amplitude: float
    wavelength: float
    phase: float
    weight: float = 1.0
    direction: float | None = None
    source_x: float | None = None
    source_y: float | None = None

    def __post_init__(self) -> None:
        """Fail-fast validálja a mezőket a `source_type`-nak megfelelően.

        Raises:
            WaveSourceSpecValueError: ha `amplitude` vagy `wavelength`
                nem szigorúan pozitív, vagy a típus-specifikus mezők nem
                a `source_type`-nak megfelelően vannak kitöltve.
        """
        if not self.amplitude > 0.0:
            raise WaveSourceSpecValueError(
                "Az amplitude-nak szigorúan pozitívnak kell lennie, "
                f"kapott érték: {self.amplitude}"
            )
        if not self.wavelength > 0.0:
            raise WaveSourceSpecValueError(
                "A wavelength-nek szigorúan pozitívnak kell lennie, "
                f"kapott érték: {self.wavelength}"
            )
        if self.source_type == "Directional":
            if self.direction is None:
                raise WaveSourceSpecValueError(
                    "Directional source_type esetén a direction kötelező."
                )
            if self.source_x is not None or self.source_y is not None:
                raise WaveSourceSpecValueError(
                    "Directional source_type esetén a source_x/source_y nem adható meg."
                )
        else:
            if self.source_x is None or self.source_y is None:
                raise WaveSourceSpecValueError(
                    "Radial source_type esetén a source_x és source_y kötelező."
                )
            if self.direction is not None:
                raise WaveSourceSpecValueError(
                    "Radial source_type esetén a direction nem adható meg."
                )


def build_wave(spec: WaveSourceSpec) -> Wave:
    """Egyetlen `WaveSourceSpec`-ből konkrét `Wave`-et épít.

    Lásd: MULTIPLE_WAVE_SOURCES.md 4. szakasz: minden `WaveSourceSpec`-ből
    előálló `Wave` `WaveFunction`-je `Sinusoidal`, `AmplitudeEnvelope`-ja
    `Uniform` (mindkettő rögzített).

    Args:
        spec: az explicit hullámforrás specifikációja.

    Returns:
        A specifikációnak megfelelő `Wave`.
    """
    propagation: DirectionalPropagation | RadialPropagation
    if spec.source_type == "Directional":
        propagation = DirectionalPropagation(
            direction_rad=math.radians(cast(float, spec.direction))
        )
    else:
        propagation = RadialPropagation(
            source_x=cast(float, spec.source_x), source_y=cast(float, spec.source_y)
        )

    return Wave(
        amplitude=spec.amplitude,
        wavelength=spec.wavelength,
        phase=spec.phase,
        function=Sinusoidal(),
        propagation=propagation,
        envelope=UniformEnvelope(),
        weight=spec.weight,
    )


def build_combined_wave_set(
    automatic_waves: tuple[Wave, ...], source_specs: tuple[WaveSourceSpec, ...]
) -> WaveSet:
    """Az automatikus generálás és az explicit forráslista összefűzéséből
    épít végső `WaveSet`-et.

    Lásd: MULTIPLE_WAVE_SOURCES.md 5–6. szakasz: az automatikusan
    generált komponensek előbb, az explicit forráslista elemei a
    megadott sorrendjükben utánuk; nincs a több forrásra vonatkozó
    önálló validációs szabály (pl. két azonos centerű `Radial` forrás
    érvényes konfiguráció).

    Args:
        automatic_waves: a `WaveParameters`-alapú automatikus generálásból
            származó, már felépített `Wave`-lista.
        source_specs: az explicit forráslista, alapértelmezetten üres.

    Returns:
        Az összefűzött `WaveSet` — az `automatic_waves` elemei előbb, a
        `source_specs`-ből épített `Wave`-ek utánuk, a megadott
        sorrendben.
    """
    explicit_waves = tuple(build_wave(spec) for spec in source_specs)
    return WaveSet(waves=automatic_waves + explicit_waves)
