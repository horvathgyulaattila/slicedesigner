"""Tesztek a `WoodGrainGenerator`-hoz és a `WoodGrainHeightFieldSource`-hoz.

Lásd: docs/plugins/relief_generator/WOOD_GRAIN_RELIEF_GENERATOR.md,
ROADMAP Phase 11.4, tests/plugins/relief_generator/generators/test_wave_generator.py
(sys.path-minta).
"""

import math
import sys
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parents[4])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

import pytest  # noqa: E402

from plugins.relief_generator.domain.procedural_noise import (  # noqa: E402
    GradientNoiseField,
)
from plugins.relief_generator.domain.wood_grain_parameters import (  # noqa: E402
    WoodGrainParameters,
)
from plugins.relief_generator.generators.wood_grain_generator import (  # noqa: E402
    WoodGrainGenerator,
    WoodGrainHeightFieldSource,
)

_VALID_KWARGS = dict(
    direction=90.0,
    seed=0,
    board_width=0.42,
    ring_spacing=0.09,
    ring_octaves=4,
    ring_persistence=0.55,
    ring_lacunarity=2.3,
    elongation_min=5.0,
    elongation_max=50.0,
    warp_scale=0.35,
    warp_strength=0.02,
    knot_count_max=3,
    knot_size_min=0.006,
    knot_size_max=0.06,
    knot_ghost_probability=0.3,
    ring_contrast=0.6,
)


def _with(**overrides: object) -> WoodGrainParameters:
    kwargs = dict(_VALID_KWARGS)
    kwargs.update(overrides)
    return WoodGrainParameters(**kwargs)  # type: ignore[arg-type]


def _hash01(a: int, b: int, seed: int) -> float:
    raw = math.sin(a * 127.1 + b * 311.7 + seed * 74.7) * 43758.5453123
    return raw - math.floor(raw)


_PITH_DIST_MIN_RATIO = 0.05
_PITH_DIST_MAX_RATIO = 0.55
_KNOT_INFLUENCE_BASE_FACTOR = 3.5
_KNOT_INFLUENCE_RANGE_FACTOR = 3.0
_KNOT_INFLUENCE_CUTOFF = 2.2
_KNOT_CORE_CUTOFF = 1.6
_KNOT_CRACK_WINDOW_FACTOR = 0.9
_KNOT_CRACK_AMPLITUDE = 0.32
_KNOT_CRACK_EXPONENT = 8
_KNOT_CORE_WINDOW_FACTOR = 0.35
_KNOT_CORE_AMPLITUDE = 0.10
_KNOT_CRACKS_MIN = 3
_KNOT_CRACKS_RANGE = 5
_BOARD_EDGE_GROOVE_WIDTH = 0.006
_BOARD_EDGE_DARKEN_FACTOR = 0.45


def _manual_expected(x: float, y: float, parameters: WoodGrainParameters) -> float:
    seed = parameters.seed
    board_width = parameters.board_width
    warp_noise = GradientNoiseField(scale=parameters.warp_scale, seed=seed)
    theta = math.radians(parameters.direction)
    cos_t, sin_t = math.cos(theta), math.sin(theta)

    def get_board(board_idx: int) -> dict:
        elongation = parameters.elongation_min + _hash01(board_idx, 1, seed) * (
            parameters.elongation_max - parameters.elongation_min
        )
        pith_side = 1.0 if _hash01(board_idx, 2, seed) < 0.5 else -1.0
        pith_dist = (
            _PITH_DIST_MIN_RATIO
            + _hash01(board_idx, 3, seed) * (_PITH_DIST_MAX_RATIO - _PITH_DIST_MIN_RATIO)
        ) * board_width
        pith_offset = pith_side * pith_dist + board_width / 2.0
        knot_count = min(
            int(_hash01(board_idx, 4, seed) * (parameters.knot_count_max + 1)),
            parameters.knot_count_max,
        )
        knots = []
        for i in range(knot_count):
            base = 10 + i * 7
            ku = _hash01(board_idx, base + 0, seed) * board_width
            kv = _hash01(board_idx, base + 1, seed)
            size_roll = _hash01(board_idx, base + 2, seed)
            k_core = parameters.knot_size_min + size_roll * size_roll * (
                parameters.knot_size_max - parameters.knot_size_min
            )
            influence_roll = _hash01(board_idx, base + 3, seed)
            k_influence = k_core * (
                _KNOT_INFLUENCE_BASE_FACTOR + influence_roll * _KNOT_INFLUENCE_RANGE_FACTOR
            )
            is_ghost = _hash01(board_idx, base + 4, seed) < parameters.knot_ghost_probability
            n_cracks = _KNOT_CRACKS_MIN + int(
                _hash01(board_idx, base + 5, seed) * _KNOT_CRACKS_RANGE
            )
            crack_phase = _hash01(board_idx, base + 6, seed) * 2.0 * math.pi
            knots.append(
                dict(
                    ku=ku,
                    kv=kv,
                    k_core=k_core,
                    k_influence=k_influence,
                    is_ghost=is_ghost,
                    n_cracks=n_cracks,
                    crack_phase=crack_phase,
                )
            )
        return dict(elongation=elongation, pith_offset=pith_offset, knots=knots)

    def ring_value(r: float) -> float:
        total = 0.0
        amp = 1.0
        amp_sum = 0.0
        spacing_i = parameters.ring_spacing
        for _ in range(parameters.ring_octaves):
            total += amp * math.sin(2.0 * math.pi / spacing_i * r)
            amp_sum += amp
            amp *= parameters.ring_persistence
            spacing_i /= parameters.ring_lacunarity
        return total / amp_sum

    v = x * cos_t + y * sin_t
    u = -x * sin_t + y * cos_t
    board_idx = math.floor(u / board_width)
    board = get_board(board_idx)
    u_local = u - board_idx * board_width

    r_main = math.sqrt(
        (u_local - board["pith_offset"]) ** 2 + (v / board["elongation"]) ** 2
    )
    r_main += parameters.warp_strength * warp_noise.sample(x, y)

    r_effective = r_main
    core_dip = 0.0
    crack_dip = 0.0
    for k in board["knots"]:
        du = u - (board_idx * board_width + k["ku"])
        dv = v - k["kv"]
        d = math.hypot(du, dv)
        if d < k["k_influence"] * _KNOT_INFLUENCE_CUTOFF:
            blend = math.exp(-(d * d) / (k["k_influence"] ** 2))
            r_effective = (1.0 - blend) * r_effective + blend * d
            if not k["is_ghost"] and d < k["k_core"] * _KNOT_CORE_CUTOFF:
                window = math.exp(
                    -(d * d) / ((_KNOT_CRACK_WINDOW_FACTOR * k["k_core"]) ** 2)
                )
                angle = math.atan2(dv, du)
                crack = (
                    max(0.0, math.cos(k["n_cracks"] * angle + k["crack_phase"]))
                    ** _KNOT_CRACK_EXPONENT
                )
                crack_dip = max(crack_dip, _KNOT_CRACK_AMPLITUDE * crack * window)
                core_dip = max(
                    core_dip,
                    _KNOT_CORE_AMPLITUDE
                    * math.exp(
                        -(d * d) / ((_KNOT_CORE_WINDOW_FACTOR * k["k_core"]) ** 2)
                    ),
                )

    ring = ring_value(r_effective)
    raw = 0.5 + 0.5 * parameters.ring_contrast * ring - parameters.ring_contrast * (
        core_dip + crack_dip
    )
    edge_dist = min(u_local, board_width - u_local)
    if edge_dist < _BOARD_EDGE_GROOVE_WIDTH:
        raw *= 1.0 - _BOARD_EDGE_DARKEN_FACTOR * parameters.ring_contrast
    return min(max(raw, 0.0), 1.0)


def test_generate_values_stay_within_unit_interval() -> None:
    parameters = _with()
    height_field = WoodGrainGenerator().generate(parameters)

    grid = [i / 20.0 for i in range(21)]
    values = [height_field.query(x, y) for x in grid for y in grid]

    assert all(0.0 <= value <= 1.0 for value in values)


def test_generate_is_deterministic_across_repeated_calls() -> None:
    parameters = _with(direction=35.0, seed=3)
    generator = WoodGrainGenerator()

    first = generator.generate(parameters)
    second = generator.generate(parameters)

    sample_points = [(0.0, 0.0), (0.2, 0.9), (0.5, 0.5), (0.9, 0.2), (1.0, 1.0)]
    for x, y in sample_points:
        assert first.query(x, y) == second.query(x, y)


def test_matches_manual_formula() -> None:
    # A kimenetnek pontosan meg kell egyeznie a teljes képlettel: a
    # deszkánként hash-elt anizotróp domb-alap, a vele interpolált
    # csomók, és a fraktál-kombinált gyűrű összege, [0,1]-re vágva.
    parameters = _with()
    wood = WoodGrainGenerator().generate(parameters)

    grid = [i / 10.0 for i in range(11)]
    for x in grid:
        for y in grid:
            expected = _manual_expected(x, y, parameters)
            assert wood.query(x, y) == pytest.approx(expected, abs=1e-9)


def test_same_seed_produces_same_board_layout() -> None:
    # Ugyanaz a seed ugyanazt a deszka-elrendezést (elongation,
    # pith_offset, csomók) kell adja — ez a `_hash01(board_idx, slot,
    # seed)` hármas alapú determinizmust igazolja.
    a = WoodGrainGenerator().generate(_with(seed=7))
    b = WoodGrainGenerator().generate(_with(seed=7))

    grid = [i / 15.0 for i in range(16)]
    for x in grid:
        for y in grid:
            assert a.query(x, y) == b.query(x, y)


def test_different_seeds_produce_different_fields() -> None:
    a = WoodGrainGenerator().generate(_with(seed=0))
    b = WoodGrainGenerator().generate(_with(seed=1))

    assert a.query(0.5, 0.5) != b.query(0.5, 0.5)


def test_height_field_source_delegates_to_generator() -> None:
    parameters = _with()
    source = WoodGrainHeightFieldSource(parameters)

    height_field = source.build_height_field()
    expected = WoodGrainGenerator().generate(parameters)

    sample_points = [(0.0, 0.0), (0.3, 0.7), (1.0, 1.0)]
    for x, y in sample_points:
        assert height_field.query(x, y) == expected.query(x, y)


def test_ghost_knot_probability_one_removes_core_and_crack_contribution() -> None:
    # knot_ghost_probability=1.0 esetén minden csomó "szellem" —
    # core_dip/crack_dip sosem érvényesül, csak a csomó saját,
    # izotróp távolság-mezeje interpolálódik a fő mezővel.
    ghost_only = _with(knot_ghost_probability=1.0, knot_count_max=3)
    wood = WoodGrainGenerator().generate(ghost_only)

    grid = [i / 15.0 for i in range(16)]
    for x in grid:
        for y in grid:
            expected = _manual_expected(x, y, ghost_only)
            assert wood.query(x, y) == pytest.approx(expected, abs=1e-9)


def test_zero_ring_contrast_yields_flat_half_output() -> None:
    parameters = _with(ring_contrast=0.0)
    wood = WoodGrainGenerator().generate(parameters)

    grid = [i / 15.0 for i in range(16)]
    for x in grid:
        for y in grid:
            assert wood.query(x, y) == pytest.approx(0.5, abs=1e-12)


def test_higher_ring_contrast_increases_value_range() -> None:
    small = WoodGrainGenerator().generate(_with(ring_contrast=0.05))
    large = WoodGrainGenerator().generate(_with(ring_contrast=0.9))

    grid = [i / 30.0 for i in range(31)]
    small_values = [small.query(x, y) for x in grid for y in grid]
    large_values = [large.query(x, y) for x in grid for y in grid]

    assert (max(large_values) - min(large_values)) > (
        max(small_values) - min(small_values)
    )
