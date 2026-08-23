"""Wave Parameters — a Wave Generator felhasználói szintű bemeneti paraméterei.

Lásd: docs/plugins/relief_generator/WAVE_FUNCTION_MODEL.md 4–9. szakasz,
docs/plugins/relief_generator/PARAMETRIC_RELIEF_GENERATOR.md 11. szakasz.
A Phase 9 (Wave Extension) óta négy opcionális mező is bővíti: `envelope`,
`distortion`, `sources`, `include_automatic` — l. docs/plugins/relief_generator/
WAVE_EXTENSION_IMPLEMENTATION_PLAN.md, ROADMAP Phase 9.7.b/g,
docs/plugins/relief_generator/MULTIPLE_WAVE_SOURCES.md 9. szakasz.
"""

from dataclasses import dataclass

from plugins.relief_generator.domain.multiple_wave_sources import WaveSourceSpec
from plugins.relief_generator.domain.wave import AmplitudeEnvelope, Distortion
from plugins.relief_generator.exceptions import WaveParametersValueError

_DIRECTION_MIN = 0.0
_DIRECTION_MAX = 360.0
_DIRECTION_SPREAD_MIN = 0.0
_DIRECTION_SPREAD_MAX = 180.0
_UNIT_INTERVAL_MIN = 0.0
_UNIT_INTERVAL_MAX = 1.0


@dataclass(frozen=True)
class WaveParameters:
    """A Directional Wave Generator felhasználó által megadott bemeneti paraméterei.

    Lásd: WAVE_FUNCTION_MODEL.md 4–9. szakasz. A hat alapmező kötelező
    (nincs alapérték), a négy Phase 9 mező (`envelope`, `distortion`,
    `sources`, `include_automatic`) opcionális. A létrehozott példány
    immutábilis (`frozen=True`). A hat alapmező érvényességét a
    `__post_init__` fail-fast ellenőrzi; az `envelope`/`distortion`/
    `sources` elemei saját maguk (`RadialAmplitudeEnvelope`,
    `SwirlDistortion`, `WaveSourceSpec` stb. `__post_init__`-je)
    validálnak, itt nincs duplikált ellenőrzés.

    Attributes:
        wavelength: a domináns komponens hullámhossza, normalizált
            koordinátaegységben. Szigorúan pozitív.
        amplitude: a domináns komponens amplitúdója, normalizált
            koordinátaegységben. Szigorúan pozitív.
        direction: a domináns hullámirány, fokban, a `[0.0, 360.0]` zárt
            intervallumból.
        direction_spread: a komponensirányok domináns iránytól való
            legnagyobb megengedett eltérése, fokban, a `[0.0, 180.0]` zárt
            intervallumból.
        irregularity: a komponensek amplitúdójának, hullámhosszának és
            fázisának determinisztikus szórási mértéke, a `[0.0, 1.0]`
            zárt intervallumból.
        complexity: a hullámkomponensek számát meghatározó paraméter, a
            `[0.0, 1.0]` zárt intervallumból.
        envelope: opcionális, az összes komponensre — automatikusan
            generáltakra ÉS `sources`-ból épülőkre egyaránt — egységesen
            alkalmazott `AmplitudeEnvelope` (pl.
            `RadialAmplitudeEnvelope`). Alapértelmezett: `None` — ekkor
            minden komponens `UniformEnvelope`-ot kap, a Phase
            8/9.1–9.7.f viselkedésnek megfelelően.
        distortion: opcionális, az összes komponensre — automatikusan
            generáltakra ÉS `sources`-ból épülőkre egyaránt — egységesen
            alkalmazott `Distortion` (pl. `SwirlDistortion`).
            Alapértelmezett: `None` — ekkor egyik komponens sem torzul.
        sources: opcionális, explicit hullámforrás-specifikációk (l.
            `WaveSourceSpec`, MULTIPLE_WAVE_SOURCES.md), amelyek az
            automatikusan generált komponensek UTÁN kerülnek a végső
            `WaveSet`-be. Alapértelmezett: üres tuple.
        include_automatic: ha `False`, a `WaveGenerator` nem épít
            automatikus komponenseket — a végső `WaveSet` kizárólag a
            `sources`-ból áll. Ha ezzel egyidejűleg `sources` is üres, a
            `WaveSet` érvénytelen állapotba kerül
            (`WaveSetValueError`) — ez szándékos, nem duplikált itt.
            Alapértelmezett: `True` (Phase 8/9.1–9.7.f-kompatibilis
            viselkedés).
    """

    wavelength: float
    amplitude: float
    direction: float
    direction_spread: float
    irregularity: float
    complexity: float
    envelope: AmplitudeEnvelope | None = None
    distortion: Distortion | None = None
    sources: tuple[WaveSourceSpec, ...] = ()
    include_automatic: bool = True

    def __post_init__(self) -> None:
        """Fail-fast validálja a hat alapmezőt a dokumentált tartományok szerint.

        Az `envelope`/`distortion`/`sources` elemei saját maguk
        validálnak a létrehozásukkor; az `include_automatic` egy sima
        `bool`, nincs rajta invariáns — itt nincs duplikált ellenőrzés.

        Raises:
            WaveParametersValueError: ha a hat alapmező bármelyike kívül
                esik a osztály-docstringben dokumentált érvényességi
                tartományán.
        """
        if not self.wavelength > 0.0:
            raise WaveParametersValueError(
                "A wavelength-nek szigorúan pozitívnak kell lennie, "
                f"kapott érték: {self.wavelength}"
            )
        if not self.amplitude > 0.0:
            raise WaveParametersValueError(
                "Az amplitude-nak szigorúan pozitívnak kell lennie, "
                f"kapott érték: {self.amplitude}"
            )
        if not _DIRECTION_MIN <= self.direction <= _DIRECTION_MAX:
            raise WaveParametersValueError(
                f"A direction-nek a [{_DIRECTION_MIN}, {_DIRECTION_MAX}] zárt "
                f"intervallumba kell esnie, kapott érték: {self.direction}"
            )
        if not _DIRECTION_SPREAD_MIN <= self.direction_spread <= _DIRECTION_SPREAD_MAX:
            raise WaveParametersValueError(
                f"A direction_spread-nek a [{_DIRECTION_SPREAD_MIN}, "
                f"{_DIRECTION_SPREAD_MAX}] zárt intervallumba kell esnie, "
                f"kapott érték: {self.direction_spread}"
            )
        if not _UNIT_INTERVAL_MIN <= self.irregularity <= _UNIT_INTERVAL_MAX:
            raise WaveParametersValueError(
                f"Az irregularity-nek a [{_UNIT_INTERVAL_MIN}, "
                f"{_UNIT_INTERVAL_MAX}] zárt intervallumba kell esnie, "
                f"kapott érték: {self.irregularity}"
            )
        if not _UNIT_INTERVAL_MIN <= self.complexity <= _UNIT_INTERVAL_MAX:
            raise WaveParametersValueError(
                f"A complexity-nek a [{_UNIT_INTERVAL_MIN}, "
                f"{_UNIT_INTERVAL_MAX}] zárt intervallumba kell esnie, "
                f"kapott érték: {self.complexity}"
            )
