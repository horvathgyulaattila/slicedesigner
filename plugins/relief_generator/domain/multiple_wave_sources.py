"""Multiple Wave Sources — explicit, felhasználói szinten megadható
hullámforrás-lista (ROADMAP Phase 9.4: Multiple wave sources).

A `WaveSourceSpec` egy explicit hullámforrás specifikációja; a
`build_waves` egyetlen specifikációból épít egy vagy több, koncentrikusan
rétegzett `Wave`-et; a `build_combined_wave_set` az automatikus generálásból
származó `Wave`-lista és az explicit forráslista determinisztikus
összefűzéséből épít végső `WaveSet`-et.

Lásd: docs/plugins/relief_generator/MULTIPLE_WAVE_SOURCES.md. A tényleges
`WaveParameters`/`WaveGenerator`/GUI-bekötés a ROADMAP 9.7 (Integration)
hatóköre — ez a modul önmagában, a `WaveGenerator` módosítása nélkül
tesztelhető domain-építőelem.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, cast

from plugins.relief_generator.domain.deterministic_components import (
    AMPLITUDE_JITTER_SCALE,
    GOLDEN_ANGLE_RAD,
    LACUNARITY,
    PERSISTENCE,
    PHASE_JITTER_SCALE,
    WAVELENGTH_JITTER_SCALE,
    component_count,
    rho,
)
from plugins.relief_generator.domain.radial_wave_source import RadialPropagation
from plugins.relief_generator.domain.wave import (
    AmplitudeEnvelope,
    DirectionalPropagation,
    Distortion,
    UniformEnvelope,
    Wave,
    WaveFunctionName,
    WaveSet,
    build_wave_function,
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
        function: a forrás `WaveFunction`-je (`"Sinusoidal"`, `"Triangle"`,
            `"Sawtooth"` vagy `"Square"`). Alapértelmezett: `"Sinusoidal"`
            (Phase 9.4–10.1-kompatibilis viselkedés). Forrásonként
            egyedileg állítható, az `amplitude`/`wavelength`/`phase`
            mintájára — nem az `envelope`/`distortion`-hoz hasonlóan
            megosztott (ROADMAP Phase 10.2).
        asymmetry_strength: a forrás fázistorzítási erőssége (ROADMAP
            Phase 12.2) — l. `AsymmetricPhase` osztály docstringje,
            WAVE_DOMAIN_MODEL.md 6.4 szakasz. Alapértelmezett: `0.0`
            (nincs torzítás). Forrásonként egyedileg állítható, az
            `amplitude`/`wavelength`/`phase`/`function` mintájára.
            Bármely véges valós érték érvényes.
        irregularity: a koncentrikus rétegek amplitúdójának,
            hullámhosszának és fázisának determinisztikus szórási
            mértéke, a `[0.0, 1.0]` zárt intervallumból. Alapértelmezett:
            `0.0` (Phase 9.4–10.2-kompatibilis viselkedés). Ugyanaz a
            szemantika, mint a `WaveParameters.irregularity`-nél
            (WAVE_FUNCTION_MODEL.md 22. szakasz), de irány-/pozíció-
            szórás nélkül — l. `complexity`.
        complexity: a koncentrikus rétegek számát meghatározó paraméter,
            a `[0.0, 1.0]` zárt intervallumból. Alapértelmezett: `0.0`
            (egyetlen réteg — Phase 9.4–10.2-kompatibilis viselkedés).
            `complexity=0.0` esetén a forrás pontosan egy `Wave`-et ad
            (`build_waves()` egyelemű tuple-t ad vissza); nagyobb érték
            esetén több, csökkenő amplitúdójú/hullámhosszú réteg épül,
            UGYANAZZAL a `direction`/`source_x`/`source_y` propagation-nel
            minden rétegen (koncentrikus rétegzés, ROADMAP Phase 10.3) —
            ellentétben a `WaveParameters`-alapú automatikus generálással,
            ahol a rétegek iránya is szóródik.
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
    function: WaveFunctionName = "Sinusoidal"
    asymmetry_strength: float = 0.0
    irregularity: float = 0.0
    complexity: float = 0.0
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
        if not 0.0 <= self.irregularity <= 1.0:
            raise WaveSourceSpecValueError(
                "Az irregularity-nek a [0.0, 1.0] zárt intervallumba kell "
                f"esnie, kapott érték: {self.irregularity}"
            )
        if not 0.0 <= self.complexity <= 1.0:
            raise WaveSourceSpecValueError(
                "A complexity-nek a [0.0, 1.0] zárt intervallumba kell "
                f"esnie, kapott érték: {self.complexity}"
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


def build_waves(
    spec: WaveSourceSpec,
    envelope: AmplitudeEnvelope | None = None,
    distortion: Distortion | None = None,
) -> tuple[Wave, ...]:
    """Egyetlen `WaveSourceSpec`-ből egy vagy több, koncentrikusan rétegzett
    `Wave`-et épít.

    Lásd: MULTIPLE_WAVE_SOURCES.md 4. szakasz: minden `WaveSourceSpec`-ből
    előálló réteg `WaveFunction`-je a `spec.function` szerint épül
    (ROADMAP Phase 10.2). A `spec.complexity`/`spec.irregularity`
    (ROADMAP Phase 10.3) a WAVE_FUNCTION_MODEL.md 22. szakaszának
    determinisztikus szabályát használja — az irány-/pozíció-szórás
    (`θ_i`) rész NÉLKÜL: minden réteg UGYANAZT a `propagation`-t kapja
    (koncentrikus rétegzés), kizárólag `amplitude`/`wavelength`/`phase`
    csökken/jitterel rétegenként. `spec.complexity=0.0` (alapértelmezett)
    esetén egyetlen réteg épül, `spec.phase`-ből kiindulva, jitter
    nélkül — ez a Phase 9.4–10.2-kompatibilis viselkedés. Az
    `envelope`/`distortion` a hívó (`WaveGenerator`) által megosztott,
    opcionális komponens, MINDEN rétegre alkalmazva — 2026-08-21-i
    kiegészítés, ld. MULTIPLE_WAVE_SOURCES.md 9. szakasz.

    Args:
        spec: az explicit hullámforrás specifikációja.
        envelope: opcionális, megosztott `AmplitudeEnvelope`. `None`
            esetén `UniformEnvelope()` (Phase 8/9.1–9.7.f-kompatibilis
            alapértelmezés).
        distortion: opcionális, megosztott `Distortion`. `None` esetén
            nincs torzítás.

    Returns:
        A specifikációnak megfelelő rétegek `Wave`-jei, `i=0..n-1`
        sorrendben (`n = component_count(spec.complexity)`).
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
    resolved_envelope = envelope if envelope is not None else UniformEnvelope()

    n = component_count(spec.complexity)
    waves: list[Wave] = []
    for i in range(n):
        amplitude = (
            spec.amplitude
            * PERSISTENCE**i
            * (1.0 + spec.irregularity * AMPLITUDE_JITTER_SCALE * rho(i, 0))
        )
        wavelength = (
            spec.wavelength
            / LACUNARITY**i
            * (1.0 + spec.irregularity * WAVELENGTH_JITTER_SCALE * rho(i, 1))
        )
        phase_jitter = (
            spec.irregularity * PHASE_JITTER_SCALE * rho(i, 2) * 2.0 * math.pi
        )
        phase = (spec.phase + i * GOLDEN_ANGLE_RAD + phase_jitter) % (2.0 * math.pi)

        waves.append(
            Wave(
                amplitude=amplitude,
                wavelength=wavelength,
                phase=phase,
                function=build_wave_function(spec.function, spec.asymmetry_strength),
                propagation=propagation,
                envelope=resolved_envelope,
                weight=spec.weight,
                distortion=distortion,
            )
        )
    return tuple(waves)


def build_combined_wave_set(
    automatic_waves: tuple[Wave, ...],
    source_specs: tuple[WaveSourceSpec, ...],
    envelope: AmplitudeEnvelope | None = None,
    distortion: Distortion | None = None,
) -> WaveSet:
    """Az automatikus generálás és az explicit forráslista összefűzéséből
    épít végső `WaveSet`-et.

    Lásd: MULTIPLE_WAVE_SOURCES.md 5–6. szakasz: az automatikusan
    generált komponensek előbb, az explicit forráslista elemei a
    megadott sorrendjükben utánuk; nincs a több forrásra vonatkozó
    önálló validációs szabály (pl. két azonos centerű `Radial` forrás
    érvényes konfiguráció). Az `envelope`/`distortion` — ha meg vannak
    adva — minden `source_specs`-ből épülő `Wave`-re alkalmazódik,
    ugyanazzal a megosztott példánnyal (MULTIPLE_WAVE_SOURCES.md 9.
    szakasz, 2026-08-21-i kiegészítés).

    Args:
        automatic_waves: a `WaveParameters`-alapú automatikus generálásból
            származó, már felépített `Wave`-lista.
        source_specs: az explicit forráslista, alapértelmezetten üres.
        envelope: opcionális, megosztott `AmplitudeEnvelope`, amelyet a
            `source_specs`-ből épülő minden `Wave` megkap.
        distortion: opcionális, megosztott `Distortion`, amelyet a
            `source_specs`-ből épülő minden `Wave` megkap.

    Returns:
        Az összefűzött `WaveSet` — az `automatic_waves` elemei előbb, a
        `source_specs`-ből épített `Wave`-ek utánuk, a megadott
        sorrendben.
    """
    explicit_waves = tuple(
        wave
        for spec in source_specs
        for wave in build_waves(spec, envelope=envelope, distortion=distortion)
    )
    return WaveSet(waves=automatic_waves + explicit_waves)
