"""Determinisztikus, több léptékű komponens-előállítási szabály — közös
segédfüggvények és konstansok (WAVE_FUNCTION_MODEL.md 22. szakasz).

A `WaveGenerator` (automatikus generálás) és a
`multiple_wave_sources.build_waves()` (explicit forrás koncentrikus
rétegzése, ROADMAP Phase 10.3) egyaránt ugyanazt a determinisztikus
komponensszám/amplitúdó/hullámhossz/fázis-leképezést használja — ez a
modul a közös, oldalhatás-mentes építőelemeket gyűjti, hogy elkerülje a
duplikációt a két hívó modul között. Domain-szintű modul (nem függ a
`generators/` csomagtól), hogy mindkét irányból (domain és generators)
importálható legyen körkörös import nélkül.
"""

from __future__ import annotations

import math

MIN_COMPONENTS = 1
"""A `complexity = 0.0`-hoz tartozó legkisebb komponensszám."""

MAX_COMPONENTS = 5
"""A `complexity = 1.0`-hoz tartozó legnagyobb komponensszám."""

PERSISTENCE = 0.5
"""Az egymást követő komponensek amplitúdó-csökkenési aránya
(`A_i ∝ PERSISTENCE**i`)."""

LACUNARITY = 2.0
"""Az egymást követő komponensek hullámhossz-csökkenési aránya
(`λ_i ∝ 1/LACUNARITY**i`)."""

GOLDEN_RATIO = 1.618033988749895
"""Az aranymetszés-arány (φ), a `rho(i, salt)` perturbációs segédfüggvény alapja."""

GOLDEN_ANGLE_RAD = 2.399963229728653
"""Az aranyszög radiánban, a fázisok determinisztikus, jól szóródó elosztásához."""

AMPLITUDE_JITTER_SCALE = 0.5
"""Az `irregularity` amplitúdóra gyakorolt hatásának skálázója (`A_JITTER`)."""

WAVELENGTH_JITTER_SCALE = 0.3
"""Az `irregularity` hullámhosszra gyakorolt hatásának skálázója (`λ_JITTER`)."""

PHASE_JITTER_SCALE = 1.0
"""Az `irregularity` fázisra gyakorolt hatásának skálázója (`φ_JITTER`)."""


def component_count(complexity: float) -> int:
    """A `complexity`-ből a komponensszámot számítja (WAVE_FUNCTION_MODEL.md
    22. szakasz, "Komponensszám").

    Args:
        complexity: a `[0.0, 1.0]` tartományból.

    Returns:
        A `[MIN_COMPONENTS, MAX_COMPONENTS]` zárt intervallumba eső
        komponensszám.
    """
    return MIN_COMPONENTS + round(complexity * (MAX_COMPONENTS - MIN_COMPONENTS))


def rho(index: int, salt: int) -> float:
    """Determinisztikus, `[-1,1]`-be eső perturbációs érték (`ρ(i, salt)`).

    Lásd: WAVE_FUNCTION_MODEL.md 22. szakasz. `random` modult vagy
    bármilyen implicit véletlenszám-állapotot nem használ: kizárólag az
    `index` és a `salt` értékétől függő, aranymetszés-arányon alapuló,
    jól szóródó sorozat.

    Args:
        index: a komponens indexe (`i >= 0`).
        salt: a felhasználási helyet megkülönböztető konstans.

    Returns:
        A `[-1.0, 1.0]` zárt intervallumba eső, determinisztikus érték.
    """
    scaled = (index + 1 + salt) * GOLDEN_RATIO
    fractional_part = scaled - math.floor(scaled)
    return 2.0 * fractional_part - 1.0
