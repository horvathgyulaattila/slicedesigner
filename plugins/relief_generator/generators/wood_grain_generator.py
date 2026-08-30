"""Wood Grain Generator — deszkánként hash-elt flóderosságú, irányított
és anizotróp ("szál menti", nem "bütü menti") évgyűrű-mintázat,
fraktál-kombinált (több oktávos) gyűrűtávolsággal, és a fő mezővel
interpolált (nem rátett), méret- és láthatóság-szórással rendelkező
csomókkal — természetes faerezet.

A tervezést két, a projektgazda által feltöltött valós faerezet-
fénykép elemzése alapozta meg: (1) a deszkán nem "bütü" (koncentrikus
kör), hanem "szál menti" nézet látszik — a domb-alap ezért irányított
és erősen anizotróp, nem izotróp középpontú; (2) a mért gyűrűtávolság-
szórás (CV≈0,4–0,5) csak fraktál-kombinált (több oktávos) gyűrűvel
reprodukálható; (3) a csomók a szálakat beívelik — ez csak a fő és a
csomó saját mezeje közti interpolációval adható vissza, nem egy
rátett torzítással.

Lásd: docs/plugins/relief_generator/WOOD_GRAIN_RELIEF_GENERATOR.md,
ROADMAP Phase 11.4.
"""

import math
from dataclasses import dataclass

from plugins.relief_generator.domain.height_field import HeightField
from plugins.relief_generator.domain.procedural_noise import GradientNoiseField
from plugins.relief_generator.domain.wood_grain_parameters import WoodGrainParameters

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
"""Belső, fix konstansok — l. WOOD_GRAIN_RELIEF_GENERATOR.md 5. szakasz
"Nyíltan jelzett egyszerűsítések"."""


def _hash01(a: int, b: int, seed: int) -> float:
    """A `procedural_noise.py` belső `_hash`-ével azonos matematikájú,
    [0,1) tartományú, tisztán aritmetikai pszeudovéletlen —
    szándékosan duplikálva, mivel az eredeti modul-privát (l.
    WOOD_GRAIN_RELIEF_GENERATOR.md 4. szakasz).
    """
    raw = math.sin(a * 127.1 + b * 311.7 + seed * 74.7) * 43758.5453123
    return raw - math.floor(raw)


class WoodGrainGenerator:
    """Wood Grain Generator: deszkánként hash-elt, irányított/anizotróp,
    fraktál-kombinált évgyűrű-mintázat, a fő mezővel interpolált
    csomókkal.

    A `generate()` minden deszkát (`board_idx`) lustán, első
    lekérdezéskor számol ki és gyorsítótáraz (`elongation`,
    "bél"-pozíció, csomók) — a lekérdezések tetszőleges sorrendben
    érkezhetnek, a gyorsítótár csak ismétlődő számítást spórol meg,
    az eredményt nem befolyásolja.
    """

    def generate(self, parameters: WoodGrainParameters) -> HeightField:
        """Előállít egy `HeightField`-et a megadott paraméterekből.

        Args:
            parameters: a Wood Grain Generator érvényesített bemeneti
                paraméterei.

        Returns:
            A deszkánkénti gyűrű-mintázat és a vele interpolált
            csomók összegét, `[0,1]`-re vágva becsomagoló
            `HeightField`.
        """
        seed = parameters.seed
        board_width = parameters.board_width
        ring_spacing = parameters.ring_spacing
        ring_octaves = parameters.ring_octaves
        ring_persistence = parameters.ring_persistence
        ring_lacunarity = parameters.ring_lacunarity
        elongation_min = parameters.elongation_min
        elongation_max = parameters.elongation_max
        warp_strength = parameters.warp_strength
        knot_count_max = parameters.knot_count_max
        knot_size_min = parameters.knot_size_min
        knot_size_max = parameters.knot_size_max
        knot_ghost_probability = parameters.knot_ghost_probability
        ring_contrast = parameters.ring_contrast

        direction_rad = math.radians(parameters.direction)
        cos_theta = math.cos(direction_rad)
        sin_theta = math.sin(direction_rad)
        warp_noise = GradientNoiseField(scale=parameters.warp_scale, seed=seed)

        board_cache: dict[int, dict] = {}

        def get_board(board_idx: int) -> dict:
            if board_idx in board_cache:
                return board_cache[board_idx]
            elongation = elongation_min + _hash01(board_idx, 1, seed) * (
                elongation_max - elongation_min
            )
            pith_side = 1.0 if _hash01(board_idx, 2, seed) < 0.5 else -1.0
            pith_dist = (
                _PITH_DIST_MIN_RATIO
                + _hash01(board_idx, 3, seed)
                * (_PITH_DIST_MAX_RATIO - _PITH_DIST_MIN_RATIO)
            ) * board_width
            pith_offset = pith_side * pith_dist + board_width / 2.0
            knot_count = min(
                int(_hash01(board_idx, 4, seed) * (knot_count_max + 1)),
                knot_count_max,
            )
            knots = []
            for i in range(knot_count):
                base = 10 + i * 7
                ku = _hash01(board_idx, base + 0, seed) * board_width
                kv = _hash01(board_idx, base + 1, seed)
                size_roll = _hash01(board_idx, base + 2, seed)
                k_core = knot_size_min + size_roll * size_roll * (
                    knot_size_max - knot_size_min
                )
                influence_roll = _hash01(board_idx, base + 3, seed)
                k_influence = k_core * (
                    _KNOT_INFLUENCE_BASE_FACTOR
                    + influence_roll * _KNOT_INFLUENCE_RANGE_FACTOR
                )
                is_ghost = _hash01(board_idx, base + 4, seed) < knot_ghost_probability
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
            board = dict(elongation=elongation, pith_offset=pith_offset, knots=knots)
            board_cache[board_idx] = board
            return board

        def ring_value(r: float) -> float:
            total = 0.0
            amp = 1.0
            amp_sum = 0.0
            spacing_i = ring_spacing
            for _ in range(ring_octaves):
                total += amp * math.sin(2.0 * math.pi / spacing_i * r)
                amp_sum += amp
                amp *= ring_persistence
                spacing_i /= ring_lacunarity
            return total / amp_sum

        def height_function(x: float, y: float) -> float:
            v = x * cos_theta + y * sin_theta
            u = -x * sin_theta + y * cos_theta
            board_idx = math.floor(u / board_width)
            board = get_board(board_idx)
            u_local = u - board_idx * board_width

            r_main = math.sqrt(
                (u_local - board["pith_offset"]) ** 2
                + (v / board["elongation"]) ** 2
            )
            r_main += warp_strength * warp_noise.sample(x, y)

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
                            -(d * d)
                            / ((_KNOT_CRACK_WINDOW_FACTOR * k["k_core"]) ** 2)
                        )
                        angle = math.atan2(dv, du)
                        crack = (
                            max(
                                0.0,
                                math.cos(k["n_cracks"] * angle + k["crack_phase"]),
                            )
                            ** _KNOT_CRACK_EXPONENT
                        )
                        crack_dip = max(
                            crack_dip, _KNOT_CRACK_AMPLITUDE * crack * window
                        )
                        core_dip = max(
                            core_dip,
                            _KNOT_CORE_AMPLITUDE
                            * math.exp(
                                -(d * d)
                                / ((_KNOT_CORE_WINDOW_FACTOR * k["k_core"]) ** 2)
                            ),
                        )

            ring = ring_value(r_effective)
            raw = (
                0.5
                + 0.5 * ring_contrast * ring
                - ring_contrast * (core_dip + crack_dip)
            )
            edge_dist = min(u_local, board_width - u_local)
            if edge_dist < _BOARD_EDGE_GROOVE_WIDTH:
                raw *= 1.0 - _BOARD_EDGE_DARKEN_FACTOR * ring_contrast
            return min(max(raw, 0.0), 1.0)

        return HeightField(height_function)


@dataclass(frozen=True)
class WoodGrainHeightFieldSource:
    """A `HeightFieldSource` szerződés (ROADMAP Phase 11.1,
    `relief_generator_parameters.py`) Wood Grain-megvalósítása — a
    `DuneHeightFieldSource`/`CraterHeightFieldSource` mintáját követve.
    """

    parameters: WoodGrainParameters

    def build_height_field(self) -> HeightField:
        return WoodGrainGenerator().generate(self.parameters)
