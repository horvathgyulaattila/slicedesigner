"""Wave — komponensalapú hullámmodell (ROADMAP Phase 9.1: Wave model extension).

A `Wave` a hullám alakját (`WaveFunction`), terjedését (`PropagationModel`)
és térbeli amplitúdómodulációját (`AmplitudeEnvelope`) külön kezelő,
bővíthető komponensmodell; a `WaveSet` ezen `Wave` komponensek rendezett
gyűjteménye és determinisztikus összegzése.

Lásd: docs/plugins/relief_generator/WAVE_DOMAIN_MODEL.md.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, Protocol

from plugins.relief_generator.exceptions import WaveSetValueError, WaveValueError


class WaveFunction(Protocol):
    """A hullám matematikai alakját meghatározó komponens.

    Lásd: WAVE_DOMAIN_MODEL.md 6. szakasz.
    """

    def evaluate(self, phase_position: float, wavelength: float, phase: float) -> float:
        """Kiértékeli a hullámalakot egy adott fázispozíción.

        Args:
            phase_position: a `PropagationModel` által meghatározott
                térbeli fázispozíció (`P(x,y)`).
            wavelength: a hullám hullámhossza (`λ`).
            phase: a hullám fáziseltolása (`φ`).

        Returns:
            A hullámalak értéke a megadott fázispozíción.
        """
        ...


@dataclass(frozen=True)
class Sinusoidal:
    """Szinuszos `WaveFunction`: `W(P,λ,φ) = sin(2π/λ·P + φ)`.

    Lásd: WAVE_DOMAIN_MODEL.md 6.2 szakasz. A Phase 8 alapmodelljének
    megfelelő hullámalak.
    """

    def evaluate(self, phase_position: float, wavelength: float, phase: float) -> float:
        return math.sin(2.0 * math.pi / wavelength * phase_position + phase)


@dataclass(frozen=True)
class Triangle:
    """Háromszög `WaveFunction`: `W(θ) = (2/π)·asin(sin(θ))`, `θ = 2π/λ·P + φ`.

    Lásd: WAVE_DOMAIN_MODEL.md 6.3 szakasz. `[-1, 1]` tartományba képez,
    mint a `Sinusoidal`.
    """

    def evaluate(self, phase_position: float, wavelength: float, phase: float) -> float:
        theta = 2.0 * math.pi / wavelength * phase_position + phase
        return (2.0 / math.pi) * math.asin(math.sin(theta))


@dataclass(frozen=True)
class Sawtooth:
    """Fűrészfog `WaveFunction`: lineáris rámpa `[-1, 1]` között.

    Lásd: WAVE_DOMAIN_MODEL.md 6.3 szakasz. `θ = 2π/λ·P + φ`,
    `t = θ/(2π)`, `W(θ) = 2·(t − floor(t + 0.5))`.
    """

    def evaluate(self, phase_position: float, wavelength: float, phase: float) -> float:
        theta = 2.0 * math.pi / wavelength * phase_position + phase
        t = theta / (2.0 * math.pi)
        return 2.0 * (t - math.floor(t + 0.5))


@dataclass(frozen=True)
class Square:
    """Négyszög `WaveFunction`: kétértékű `{-1, 1}`, 50%-os kitöltési tényezővel.

    Lásd: WAVE_DOMAIN_MODEL.md 6.3 szakasz. `θ = 2π/λ·P + φ`,
    `t = (θ/(2π)) mod 1`, `W(θ) = 1` ha `t < 0.5`, egyébként `-1`.
    """

    def evaluate(self, phase_position: float, wavelength: float, phase: float) -> float:
        theta = 2.0 * math.pi / wavelength * phase_position + phase
        t = (theta / (2.0 * math.pi)) % 1.0
        return 1.0 if t < 0.5 else -1.0


@dataclass(frozen=True)
class AsymmetricPhase:
    """Egy másik `WaveFunction`-t becsomagoló, a fázisszöget torzító
    `WaveFunction` — tetszőleges alap-alakkal (Sinusoidal/Triangle/
    Sawtooth/Square) kombinálható, irányfüggően lankás/meredek
    ("dűneszerű") aszimmetrikus profilt ad (ROADMAP Phase 12.2,
    `BACKLOG.md` 2. tétel).

    Lásd: WAVE_DOMAIN_MODEL.md 6.4 szakasz. A klasszikus "fázistorzítás"
    (phase distortion) technika: legyen `θ = 2π/λ·P + φ` (ugyanaz, amit
    a becsomagolt függvény is használna); a torzított fázisszög
    `θ' = θ + k·sin(θ)` (`k = asymmetry_strength`), amit a becsomagolt
    függvény egy ezzel ekvivalens, torzított `phase_position'`-ön
    keresztül kap meg (mivel a `WaveFunction.evaluate` szignatúrája
    `phase_position`-t vár, nem közvetlenül `θ`-t):

    ```text
    P' = P + (λ/2π)·k·sin(θ)
    W'(P,λ,φ) = W_inner(P', λ, φ)
    ```

    `|k| < 1` esetén a `P → P'` leképezés mindenhol monoton; `|k| ≥ 1`
    esetén nem monoton (a leképezés "visszahajlik"), de a `HeightField`
    ettől még mindig tökéletesen érvényes, egyértékű marad — minden
    `(x,y)`-hoz pontosan egy `P'`, tehát pontosan egy magasság tartozik.
    `|k|` 1 fölé emelése megfigyelhetően (chat-en belüli előnézettel
    validálva) nem "elromlik", hanem a profil finom aszimmetriájából
    fokozatosan egy magasabb-harmonikus, ismétlődő ripple-mintázatba
    vált át — ez szándékosan nincs korlátozva, ugyanúgy, ahogy a
    `Dune`/`WoodGrain` hasonló "erősség" paraméterei (`asymmetry_strength`,
    `ripple_warp_strength`, `warp_strength`) sem korlátozottak.

    Attributes:
        inner: a becsomagolt, alap `WaveFunction` (bármelyik a négy
            meglévő közül, vagy akár egy másik `AsymmetricPhase`).
        asymmetry_strength: a fázistorzítás mértéke (`k`) — pozitív
            érték a hullám egyik oldalát, negatív a másikat teszi
            meredekebbé/keskenyebbé, miközben az ellentétes oldal
            lankásabbá/szélesebbé válik. `0` esetén nincs torzítás (a
            becsomagolt függvénnyel azonos kimenetet ad). Bármely véges
            valós érték érvényes.
    """

    inner: WaveFunction
    asymmetry_strength: float

    def evaluate(self, phase_position: float, wavelength: float, phase: float) -> float:
        theta = 2.0 * math.pi / wavelength * phase_position + phase
        distorted_position = phase_position + (
            wavelength / (2.0 * math.pi) * self.asymmetry_strength * math.sin(theta)
        )
        return self.inner.evaluate(distorted_position, wavelength, phase)


WaveFunctionName = Literal["Sinusoidal", "Triangle", "Sawtooth", "Square"]
"""A GUI-n és a felhasználói szintű paramétereken (`WaveParameters.function`,
`WaveSourceSpec.function`) választható `WaveFunction`-nevek (ROADMAP Phase 10.2)."""

_WAVE_FUNCTION_FACTORIES: dict[WaveFunctionName, Callable[[], "WaveFunction"]] = {
    "Sinusoidal": Sinusoidal,
    "Triangle": Triangle,
    "Sawtooth": Sawtooth,
    "Square": Square,
}


def build_wave_function(
    name: WaveFunctionName, asymmetry_strength: float = 0.0
) -> WaveFunction:
    """A `WaveFunctionName` alapján egy konkrét `WaveFunction`-példányt épít.

    Args:
        name: a választott hullámalak neve.
        asymmetry_strength: opcionális fázistorzítás mértéke (ROADMAP
            Phase 12.2) — ha nem nulla, a visszaadott függvényt egy
            `AsymmetricPhase` csomagolja be. Alapértelmezett: `0.0` —
            ekkor a visszaadott függvény pontosan a korábbi (Phase
            10.2-kompatibilis) viselkedést adja, nincs becsomagolás.

    Returns:
        A megfelelő `WaveFunction`-implementáció új példánya, `0.0`-tól
        eltérő `asymmetry_strength` esetén `AsymmetricPhase`-be
        csomagolva.
    """
    base = _WAVE_FUNCTION_FACTORIES[name]()
    if asymmetry_strength == 0.0:
        return base
    return AsymmetricPhase(inner=base, asymmetry_strength=asymmetry_strength)


class PropagationModel(Protocol):
    """A hullám térbeli fázispozícióját meghatározó komponens.

    Lásd: WAVE_DOMAIN_MODEL.md 7. szakasz.
    """

    def phase_position(self, x: float, y: float) -> float:
        """Kiszámítja a fázispozíciót egy adott térbeli koordinátán.

        Args:
            x: X-koordináta.
            y: Y-koordináta.

        Returns:
            A `P(x,y)` fázispozíció.
        """
        ...


@dataclass(frozen=True)
class DirectionalPropagation:
    """Síkhullám-terjedés: `P(x,y) = x·cos(θ) + y·sin(θ)`.

    Lásd: WAVE_DOMAIN_MODEL.md 7.2 szakasz.

    Attributes:
        direction_rad: a hullám iránya radiánban (`θ`).
    """

    direction_rad: float

    def phase_position(self, x: float, y: float) -> float:
        return x * math.cos(self.direction_rad) + y * math.sin(self.direction_rad)


class AmplitudeEnvelope(Protocol):
    """A hullám térbeli amplitúdómodulációját meghatározó komponens.

    Lásd: WAVE_DOMAIN_MODEL.md 8. szakasz. Kontraktus: `0 <= M(x,y) <= 1`
    minden `(x,y)`-ra — ezt az egyes megvalósítások felelősek betartani;
    a `Wave`/`WaveSet` ezt futásidőben nem kényszeríti ki (a végső,
    normalizált érték tartományát a downstream `HeightField.query` már
    ellenőrzi).
    """

    def amplitude_factor(self, x: float, y: float) -> float:
        """Kiszámítja az amplitúdómodulációs szorzót egy adott koordinátán.

        Args:
            x: X-koordináta.
            y: Y-koordináta.

        Returns:
            Az `M(x,y)` amplitúdómodulációs szorzó, a `[0.0, 1.0]` zárt
            intervallumból.
        """
        ...


@dataclass(frozen=True)
class UniformEnvelope:
    """Envelope nélküli amplitúdómoduláció: `M(x,y) = 1.0`.

    Lásd: WAVE_DOMAIN_MODEL.md 8.2 szakasz. Az alapértelmezett envelope;
    ezzel a `Wave.evaluate` eredménye a Phase 8 azonos konfigurációjú
    eredményével kompatibilis.
    """

    def amplitude_factor(self, x: float, y: float) -> float:
        return 1.0


class Distortion(Protocol):
    """A hullám fázispozíció-számítása előtt alkalmazott koordináta-
    torzítást meghatározó, opcionális komponens.

    Lásd: PROCEDURAL_DISTORTION.md 2.1 szakasz. A `Distortion` kizárólag
    a `PropagationModel` bemenetét torzítja — az `AmplitudeEnvelope`
    továbbra is az eredeti, torzítatlan `(x,y)` koordinátákat kapja.
    """

    def warp(self, x: float, y: float) -> tuple[float, float]:
        """Torzítja a koordinátákat a `PropagationModel` kiértékelése előtt.

        Args:
            x: X-koordináta.
            y: Y-koordináta.

        Returns:
            A torzított `(x', y')` koordináták.
        """
        ...


@dataclass(frozen=True)
class Wave:
    """Egy konkrét matematikai hullámkomponens.

    Lásd: WAVE_DOMAIN_MODEL.md 4. szakasz, PROCEDURAL_DISTORTION.md 2.
    szakasz. Az összes mező kötelező (nincs alapérték a `weight` és a
    `distortion` kivételével), a létrehozott példány immutábilis
    (`frozen=True`). Az `amplitude`/`wavelength` érvényességét a
    `__post_init__` fail-fast ellenőrzi.

    Attributes:
        amplitude: a komponens saját amplitúdója (`A_i`). Szigorúan
            pozitív.
        wavelength: a komponens hullámhossza (`λ_i`). Szigorúan pozitív.
        phase: a komponens fáziseltolása (`φ_i`), véges numerikus érték.
        function: a hullám alakját meghatározó komponens (`W_i`).
        propagation: a hullám fázispozícióját meghatározó komponens
            (`P_i`).
        envelope: a hullám térbeli amplitúdómodulációját meghatározó
            komponens (`M_i`).
        weight: a komponens hozzájárulása a `WaveSet` eredményéhez
            (`w_i`). Bármely véges valós érték lehet. Alapértelmezett:
            `1.0`.
        distortion: a `propagation` kiértékelése előtt alkalmazott,
            opcionális koordináta-torzítás (`Dist_i`). Alapértelmezett:
            `None` — ekkor a `propagation` az eredeti `(x,y)`
            koordinátákat kapja (identitás-transzformáció), ami a
            Phase 8/9.1–9.5 viselkedést biztosítja.
    """

    amplitude: float
    wavelength: float
    phase: float
    function: WaveFunction
    propagation: PropagationModel
    envelope: AmplitudeEnvelope
    weight: float = 1.0
    distortion: Distortion | None = None

    def __post_init__(self) -> None:
        """Fail-fast validálja az `amplitude`/`wavelength` mezőket.

        Raises:
            WaveValueError: ha `amplitude` vagy `wavelength` nem
                szigorúan pozitív.
        """
        if not self.amplitude > 0.0:
            raise WaveValueError(
                "Az amplitude-nak szigorúan pozitívnak kell lennie, "
                f"kapott érték: {self.amplitude}"
            )
        if not self.wavelength > 0.0:
            raise WaveValueError(
                "A wavelength-nek szigorúan pozitívnak kell lennie, "
                f"kapott érték: {self.wavelength}"
            )

    def evaluate(self, x: float, y: float) -> float:
        """Kiértékeli a komponens hozzájárulását egy adott koordinátán.

        Lásd: WAVE_DOMAIN_MODEL.md 4.1 szakasz és PROCEDURAL_DISTORTION.md
        2.1 szakasz:
        `f_i(x,y) = w_i · A_i · M_i(x,y) · W_i(P_i(Dist_i(x,y)), λ_i, φ_i)`.
        A `distortion` (ha meg van adva) kizárólag a `propagation`
        bemenetét torzítja; az `envelope` az eredeti, torzítatlan
        `(x,y)`-t kapja.

        Args:
            x: X-koordináta.
            y: Y-koordináta.

        Returns:
            A komponens `f_i(x,y)` hozzájárulása.
        """
        if self.distortion is None:
            propagation_x, propagation_y = x, y
        else:
            propagation_x, propagation_y = self.distortion.warp(x, y)
        phase_position = self.propagation.phase_position(propagation_x, propagation_y)
        shape = self.function.evaluate(phase_position, self.wavelength, self.phase)
        return (
            self.weight * self.amplitude * self.envelope.amplitude_factor(x, y) * shape
        )


@dataclass(frozen=True)
class WaveSet:
    """`Wave` komponensek rendezett gyűjteménye.

    Lásd: WAVE_DOMAIN_MODEL.md 9. szakasz. Legalább egy komponenst kell
    tartalmaznia; ezt a `__post_init__` fail-fast ellenőrzi. A `waves`
    sorrendje determinisztikus és megőrzött (`tuple`).

    Attributes:
        waves: a komponensek rendezett, nem üres gyűjteménye.
    """

    waves: tuple[Wave, ...]

    def __post_init__(self) -> None:
        """Fail-fast validálja, hogy a `waves` nem üres.

        Raises:
            WaveSetValueError: ha `waves` üres.
        """
        if len(self.waves) == 0:
            raise WaveSetValueError(
                "A WaveSet-nek legalább egy Wave komponenst tartalmaznia kell."
            )

    def evaluate_raw(self, x: float, y: float) -> float:
        """Kiszámítja a nyers, normalizálatlan matematikai mezőt.

        Lásd: WAVE_DOMAIN_MODEL.md 9.1 szakasz: `F(x,y) = Σ f_i(x,y)`.

        Args:
            x: X-koordináta.
            y: Y-koordináta.

        Returns:
            A komponensek `f_i(x,y)` értékeinek összege.
        """
        return sum(wave.evaluate(x, y) for wave in self.waves)
