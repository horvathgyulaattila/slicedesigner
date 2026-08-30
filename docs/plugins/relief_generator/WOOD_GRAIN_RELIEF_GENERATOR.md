# Wood Grain Relief Generator

Kapcsolódó dokumentumok: [PROCEDURAL_NOISE.md](PROCEDURAL_NOISE.md) (a
`GradientNoiseField` domain-contractja, amire ez a generátor épül).

Státusz: Elfogadva
ROADMAP: Phase 11.4

## 1. Cél

A Wood Grain Relief Generator a Phase 11 negyedik (utolsó)
procedurális Height Field receptje: természetes faerezet — deszkánként
tagolt, "szál menti" (nem "bütü menti") évgyűrű-mintázat, fraktál-
kombinált gyűrűtávolsággal, és a fő mintázattal szervesen interpolált,
méret- és láthatóság-szórással rendelkező csomókkal.

## 2. Tervezési előzmény — miért nem elég egy "körkörös gradiens"

A ROADMAP eredeti leírása ("körkörös gradiens, Perlin-zajjal torzítva,
gyűrűzve") egy izotróp, egy középpontú, egyetlen `sin()`-es gyűrű-
mintázatot sejtetett. A projektgazda két valós faerezet-fénykép
alapos elemzése (metszet-profilok, csúcstávolság-statisztika sok száz
mérési ponton, csomó-közeli kivágatok) három lényeges eltérést mutatott:

1. **A deszkán nem "bütü" (koncentrikus kör), hanem "szál menti"
   nézet látszik** — a fa törzsét nem a közepén, hanem attól távol,
   tangenciálisan vágják, ezért a valójában koncentrikus évgyűrűkből
   csak egy távoli, lapos, hosszan elnyúló ("katedrális") szeletet
   látunk.
2. **A gyűrűtávolság erősen szórt** (mért CV≈0,4–0,5) és a távolság-
   eloszlás nem haranggörbe, hanem exponenciálisan lecsengő — ez több,
   egymásra rétegzett frekvenciájú gyűrű (fraktál-kombináció) jele,
   nem egyetlen tiszta periódusé.
3. **A csomók a szálakat beívelik, nem csak eltérítik** — a csomó
   közelében a fő rost mintázata és a csomó saját, izotróp mezeje
   között sima átmenet (interpoláció) van, ez adja az egymásba
   ágyazódó "macskaszem" mintázatot.

## 3. Domain-modell

```text
WoodGrainParameters (direction, seed, board_width, ring_spacing,
                      ring_octaves, ring_persistence, ring_lacunarity,
                      elongation_min, elongation_max, warp_scale,
                      warp_strength, knot_count_max, knot_size_min,
                      knot_size_max, knot_ghost_probability,
                      ring_contrast)

θ = radians(direction)
v(x,y) = x·cosθ + y·sinθ                    — szál menti koordináta
u(x,y) = −x·sinθ + y·cosθ                   — kereszt-szál koordináta

board_idx = floor(u / board_width)
u_local = u − board_idx · board_width       — [0, board_width) tartományban

--- Deszkánkénti, determinisztikusan hash-elt jellemzők ---
(hash01(a, b, seed) — l. 4. szakasz — a `procedural_noise.py` belső
`_hash`-ével azonos, [0,1) tartományú, tisztán aritmetikai függvény)

h(slot) = hash01(board_idx, slot, seed)

elongation  = elongation_min + h(1)·(elongation_max − elongation_min)
pith_side   = +1, ha h(2) < 0.5, egyébként −1
pith_dist   = (0.05 + h(3)·0.5) · board_width         — belső, fix arány
pith_offset = pith_side · pith_dist + board_width/2
knot_count  = min(⌊h(4) · (knot_count_max+1)⌋, knot_count_max)

--- Csomónkénti jellemzők (i = 0 .. knot_count−1, slot-bázis = 10+i·7) ---
ku = hash01(board_idx, bázis+0, seed) · board_width
kv = hash01(board_idx, bázis+1, seed)
k_core      = knot_size_min + hash01(bázis+2)² · (knot_size_max − knot_size_min)
k_influence = k_core · (3.5 + hash01(bázis+3) · 3.0)          — belső, fix tartomány
is_ghost    = hash01(bázis+4) < knot_ghost_probability
n_cracks    = 3 + ⌊hash01(bázis+5) · 5⌋                        — belső, fix tartomány: 3..7
crack_phase = hash01(bázis+6) · 2π

--- Domb-alap ---
warp = GradientNoiseField(warp_scale, seed).sample(x,y)
r_main = sqrt((u_local − pith_offset)² + (v/elongation)²) + warp_strength · warp

--- Csomók (interpolálva, TÁVOLSÁG ROTÁCIÓ-INVARIÁNS, (u,v)-ben számolva) ---
r_effective = r_main
core_dip = 0, crack_dip = 0
minden csomóra:
    du = u − (board_idx·board_width + ku),  dv = v − kv
    d = sqrt(du² + dv²)
    ha d < k_influence · 2.2:
        blend = exp(−d² / k_influence²)
        r_effective ← (1−blend)·r_effective + blend·d
        ha NEM szellem ÉS d < k_core · 1.6:
            ablak = exp(−d² / (0.9·k_core)²)
            szög = atan2(dv, du)
            repedés = max(0, cos(n_cracks·szög + crack_phase))⁸
            crack_dip ← max(crack_dip, 0.32 · repedés · ablak)
            core_dip  ← max(core_dip, 0.10 · exp(−d² / (0.35·k_core)²))

--- Gyűrű (fraktál-kombináció) ---
gyűrű(r) = Σ_{i=0}^{ring_octaves−1} ring_persistence^i · sin(2π / (ring_spacing/ring_lacunarity^i) · r)
           / Σ_{i=0}^{ring_octaves−1} ring_persistence^i

nyers = 0.5 + 0.5·ring_contrast·gyűrű(r_effective) − ring_contrast·(core_dip + crack_dip)

ha min(u_local, board_width − u_local) < 0.006:      — deszkahatár-horony
    nyers ← nyers · (1 − 0.45 · ring_contrast)

h(x,y) = clamp(nyers, 0, 1)
```

## 4. A `hash01` segédfüggvény — szándékos duplikáció

A `procedural_noise.py`-ban lévő `_hash(ix, iy, seed)` modul-privát
(alulvonással kezdődik), ezért ez a generátor egy azonos matematikájú,
saját, modulon belüli `_hash01` függvényt definiál, nem importálja azt.
Ez tudatos kompromisszum: az alternatíva a `_hash` publikussá tétele
lett volna a `procedural_noise.py`-ban, ami egy már lezárt, alapvető
modul módosítását jelentette volna egyetlen új generátor kedvéért — a
Szoftverarchitekt ezt a hatásvizsgálatban jelezte, a projektgazda
jóváhagyta.

Fontos: ez **nem** a Python `random` modult használja — a projekt
elve szerint (l. PROCEDURAL_NOISE.md) semmilyen generátor nem
támaszkodhat implicit véletlenszám-állapotra; minden "véletlennek"
tűnő érték a `(board_idx, slot, seed)` hármasból determinisztikusan
származik.

## 5. Paraméterek

| Paraméter | Típus | Alapérték | Korlát |
|---|---|---|---|
| `direction` | float | 90.0 | bármely valós (fok) |
| `seed` | int | 0 | bármely egész |
| `board_width` | float | 0.42 | szigorúan pozitív |
| `ring_spacing` | float | 0.09 | szigorúan pozitív |
| `ring_octaves` | int | 4 | `≥ 1` |
| `ring_persistence` | float | 0.55 | szigorúan pozitív |
| `ring_lacunarity` | float | 2.3 | szigorúan `> 1` |
| `elongation_min` | float | 5.0 | szigorúan pozitív, `< elongation_max` |
| `elongation_max` | float | 50.0 | `> elongation_min` |
| `warp_scale` | float | 0.35 | szigorúan pozitív |
| `warp_strength` | float | 0.02 | bármely valós |
| `knot_count_max` | int | 3 | `≥ 0` |
| `knot_size_min` | float | 0.006 | szigorúan pozitív, `< knot_size_max` |
| `knot_size_max` | float | 0.06 | `> knot_size_min` |
| `knot_ghost_probability` | float | 0.3 | `[0, 1]` |
| `ring_contrast` | float | 0.6 | `≥ 0` |

**Nyíltan jelzett egyszerűsítések** (a Dűne 23 mezős tapasztalata
után szándékosan kevesebb felhasználói mező): a `pith_dist` belső
aránya, a csomó-befolyási-tényező tartománya, a repedésszám-tartomány,
a csomó-hatás/mag levágási küszöbei (2.2 / 1.6), a repedés/mag
mélység-amplitúdói és a deszkahatár-horony mértéke **fix, belső
konstansok** — finomhangolásuk, ha élő tesztelés indokolja, backlog-
tétel.

## 6. Generátor-választás (ROADMAP Phase 11.0/11.4)

A `generator_type` enum (`registration.py`) `"WoodGrain"` értéke
választja ki ezt a generátort — a Faerezet-specifikus mezők a Phase
11.0-ban bevezetett `ParameterSpec.visible_when` mechanizmuson
keresztül kizárólag ekkor jelennek meg, két alcsoportba rendezve
("Faerezet — alap", "Faerezet — csomók"). A meglévő Wave/Voronoi/
Crater/Dune mezők semmilyen módosítást nem igényeltek.

## 7. `HeightFieldSource` — generátor-független bekötés

A `WoodGrainHeightFieldSource` (`generators/wood_grain_generator.py`)
a Phase 11.1-ben bevezetett `HeightFieldSource` Protocol ötödik
megvalósítása — a `DuneHeightFieldSource`/`CraterHeightFieldSource`
mintáját követi.

## 8. Hatókörön kívül

* A deszkák közötti horony mélységének/szélességének felhasználói
  paraméterré tétele — jelenleg fix, belső konstans.
* A csomók sugárirányú elhelyezkedésének (melyik oldalról "indul")
  fizikailag pontosabb modellezése — a jelenlegi, a fő mezővel
  interpolált megoldás a projektgazda szerint már kellően hitelesen
  megfogja ezt a hatást, külön modellezés nélkül is.
* A repedésszám és a csomó-hatási tényező tartományának felhasználói
  paraméterré tétele.
* Fraktál-kombináció a fodor-fázison (itt nincs is fodor-réteg, ez a
  recept a Dune-tól eltérően nem tartalmaz külön fodrot).
