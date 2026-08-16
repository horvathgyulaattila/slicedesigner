"""Wave Parameters — a Wave Generator felhasználói szintű bemeneti paraméterei.

Lásd: docs/plugins/relief_generator/WAVE_FUNCTION_MODEL.md 4–9. szakasz,
docs/plugins/relief_generator/PARAMETRIC_RELIEF_GENERATOR.md 11. szakasz.
"""

from dataclasses import dataclass

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

    Lásd: WAVE_FUNCTION_MODEL.md 4–9. szakasz. Mind a hat mező kötelező
    (nincs alapérték), a létrehozott példány pedig immutábilis
    (`frozen=True`). A mezők érvényességét a `__post_init__` fail-fast
    ellenőrzi.

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
    """

    wavelength: float
    amplitude: float
    direction: float
    direction_spread: float
    irregularity: float
    complexity: float

    def __post_init__(self) -> None:
        """Fail-fast validálja az összes mezőt a dokumentált tartományok szerint.

        Raises:
            WaveParametersValueError: ha bármelyik mező kívül esik a
                osztály-docstringben dokumentált érvényességi tartományán.
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
