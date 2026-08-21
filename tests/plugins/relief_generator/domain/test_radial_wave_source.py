"""Tesztek a RadialPropagation-höz (ROADMAP Phase 9.3).

Lásd: docs/plugins/relief_generator/RADIAL_WAVE_SOURCE.md.
"""

import math
import sys
from pathlib import Path

import pytest

# A `plugins/` névtér PEP 420 namespace package (l. ADR-0016). L. a
# `test_wave.py`/`test_amplitude_envelope.py` azonos mintáját.
_REPO_ROOT = str(Path(__file__).resolve().parents[4])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

from plugins.relief_generator.domain.radial_wave_source import (  # noqa: E402
    RadialPropagation,
)
from plugins.relief_generator.domain.wave import (  # noqa: E402
    Sinusoidal,
    UniformEnvelope,
    Wave,
)


def test_radial_propagation_matches_formula() -> None:
    propagation = RadialPropagation(source_x=1.0, source_y=2.0)

    result = propagation.phase_position(x=4.0, y=6.0)

    expected = math.sqrt((4.0 - 1.0) ** 2 + (6.0 - 2.0) ** 2)
    assert result == pytest.approx(expected)


def test_radial_propagation_at_source_is_zero() -> None:
    propagation = RadialPropagation(source_x=3.5, source_y=-2.0)

    result = propagation.phase_position(x=3.5, y=-2.0)

    assert result == 0.0


def test_radial_propagation_source_can_be_far_outside_surface() -> None:
    # A source-nak nincs invariáns megkötése -- bármilyen véges koordináta
    # érvényes, a vizsgált felszínen kívül is.
    propagation = RadialPropagation(source_x=-1000.0, source_y=1000.0)

    result = propagation.phase_position(x=0.0, y=0.0)

    expected = math.hypot(1000.0, 1000.0)
    assert result == pytest.approx(expected)


def test_radial_propagation_satisfies_propagation_model_contract_with_wave() -> None:
    # Integrációs jellegű mini-teszt: a RadialPropagation valódi
    # PropagationModel-ként használható egy Wave-ben (l. domain/wave.py),
    # a wave.py módosítása nélkül (structural typing, Protocol).
    propagation = RadialPropagation(source_x=0.0, source_y=0.0)
    wave = Wave(
        amplitude=2.0,
        wavelength=1.0,
        phase=0.0,
        function=Sinusoidal(),
        propagation=propagation,
        envelope=UniformEnvelope(),
    )

    # A forrásban P=0 -> sin(0)=0 -> a Wave hozzájárulása nulla.
    assert wave.evaluate(0.0, 0.0) == pytest.approx(0.0)

    # Máshol a Wave hozzájárulása nem feltétlenül nulla.
    off_source = wave.evaluate(0.25, 0.0)
    assert off_source != pytest.approx(0.0)
