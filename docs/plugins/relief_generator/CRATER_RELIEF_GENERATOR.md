# Crater Relief Generator

Kapcsolódó dokumentumok: [VORONOI_RELIEF_GENERATOR.md](VORONOI_RELIEF_GENERATOR.md),
[PROCEDURAL_NOISE.md](PROCEDURAL_NOISE.md),
[WAVE_FUNCTION_MODEL.md](WAVE_FUNCTION_MODEL.md) (18–20. szakasz, a
`HeightField` generátor-független szerződése).

Státusz: Elfogadva
ROADMAP: Phase 11.2

## 1. Cél

A Crater Relief Generator a `BACKLOG.md` (korábbi) 1. tételéből származó
négy procedurális Height Field recept közül a második: kör alakú,
elszigetelt (és sűrűbb elhelyezés esetén természetesen egymásba futó),
lapos aljú, meredek szélű, holdkráter-szerű mélyedések, változó
méretben, rétegenként — kisebb kráterekkel, amelyek szabadon eshetnek
nagyobbak belsejébe, és **méretükkel arányosan sekélyebbek is**.

## 2. Miért nem elég a puszta hatványfüggvényes torzítás?

A `VoronoiNoiseField.sample(x,y)` a legközelebbi magponthoz mért
távolság — ez definíció szerint a teljes síkot hézagmentesen, a
legközelebbi magponthoz rendelve osztja fel ("F1" Worley-zaj,
PROCEDURAL_NOISE.md 3. szakasz). A `[0,1]`-es kimeneti tartomány mindig
a Voronoi-cella sokszögletű határáig tart. Egy korábbi tervezet
(`h = sample(x,y) ** power`) csak a magasságprofilt alakította — a
kráter így mindig a cellahatárig ért, láthatóan sokszögletes, nem kör
alakú maradt.

## 3. Miért nem elég egyetlen `radius`-ra vágott réteg?

Egy korábbi javítás bevezette a `radius` küszöböt (l. lent, 4. szakasz)
— ez megoldotta a sokszögletesség problémáját, de minden krátert
azonos méretűvé tette. Élő tesztelés során ez mesterkéltnek hatott a
valódi holdfelszínhez képest, ahol a kráterméretek erősen változatosak,
és gyakori, hogy egy kisebb kráter egy nagyobb belsejébe esik — ezt a
rétegzés (`octaves`/`lacunarity`) oldja fel.

## 4. Domain-modell (rétegzett, méret- és mélység-arányos)

```text
CraterParameters (scale, seed, radius, power, octaves, lacunarity)
        │
        ▼  réteg i = 0 .. octaves-1
   scale_i = scale / lacunarity^i        — rácsméret zsugorodik
   depth_i = 1 / lacunarity^i            — max. mélység is zsugorodik
        │
   VoronoiNoiseField(scale_i, seed+i).sample(x, y)         — [0,1]
        │
        ▼  d >= radius?  →  h_i = 1.0 (érintetlen)
        ▼  d <  radius   →  t = d/radius
                             h_i = 1 − (1 − t^power) · depth_i
        │
        ▼  min(h_0, ..., h_{octaves-1})
    HeightField
```

A `radius`-on belüli tartomány mindig az adott réteg saját magpontjától
mért, radiálisan szimmetrikus távolság — ez adja a kör alakú
kráterprofilt. A rétegek `min`-nel kombinálódnak, nem összegződnek
(ellentétben a `GradientNoiseField` fraktál-kombinációjával) — itt nem
zajfinomításról van szó, hanem fizikailag különálló kráter-generációk
egymásra rétegezéséről: egy adott pontban az számít, melyik réteg
vágja legmélyebbre. `octaves=1` esetén ez pontosan a korábbi, egyrétegű
viselkedést adja vissza.

## 5. Miért arányos a mélység a mérettel, külön paraméter nélkül?

A valódi holdkráterek mélysége nagyjából arányos az átmérőjükkel — élő
tesztelés során derült ki, hogy ennek hiánya (minden réteg krátere
egyformán mély, `h=0`-ig) mesterkéltnek hatott. A projektgazda
kifejezett kérése szerint ez nem új, felhasználó által állítandó
paraméter, hanem beépített viselkedés: a már meglévő `lacunarity`
egyszerre vezérli a rácsméretet ÉS a maximális mélységet
(`depth_i = 1 / lacunarity^i`) — mivel mindkettő ugyanattól az egy
értéktől függ, a nagyobb kráterek arányosan mélyebbek, a kisebbek
arányosan sekélyebbek maradnak, minden további tervezés nélkül.
`octaves=1` esetén a mélység-szorzó mindig `1.0` — teljesen
visszamenőleg kompatibilis.

## 6. Paraméterek

| Paraméter | Típus | Alapérték (GUI) | Alapérték (domain) | Korlát |
|---|---|---|---|---|
| `scale` | float | 0.2 | — | szigorúan pozitív |
| `seed` | int | 0 | — | bármely egész |
| `radius` | float | 0.4 | — | `(0, 1]` |
| `power` | float | 3.0 | — | szigorúan pozitív |
| `octaves` | int | 3 | 1 | `>= 1` |
| `lacunarity` | float | 2.0 | 2.0 | `> 1.0` |

A domain-osztály (`CraterParameters`) alapértéke `octaves=1` — a
`GradientNoiseField` konvencióját követve a fraktál-rétegzés alapból
"kikapcsolt". A GUI-mező alapértéke `3`, hogy a felhasználó alapból a
változatosabb viselkedést lássa. A `lacunarity` egyszerre vezérli a
rácsméret- és a mélység-zsugorodást (l. 5. szakasz) — nincs külön
mezője ennek a két hatásnak.

## 7. Generátor-választás (ROADMAP Phase 11.0/11.2)

A `generator_type` enum (`registration.py`) `"Crater"` értéke választja
ki ezt a generátort — a Holdkráter-specifikus mezők a Phase 11.0-ban
bevezetett `ParameterSpec.visible_when` mechanizmuson keresztül
kizárólag ekkor jelennek meg. A meglévő Wave/Voronoi mezők semmilyen
módosítást nem igényeltek a `generator_type` harmadik értékének
bevezetéséhez.

## 8. `HeightFieldSource` — generátor-független bekötés

A `CraterHeightFieldSource` (`generators/crater_generator.py`) a Phase
11.1-ben bevezetett `HeightFieldSource` Protocol harmadik megvalósítása
— a `VoronoiHeightFieldSource`/`WaveHeightFieldSource` mintáját követi.
A `ReliefGeneratorParameters`/`ReliefGeneratorMeshSource` egyike sem
igényelt módosítást ehhez a recepthez.

## 9. Hatókörön kívül

* Kráterperem-kiemelkedés (a valódi holdkráterek jellegzetes, megemelt
  pereme, `h > 1.0` a `radius` közelében) — a jelen recept a `radius`
  határon pontosan `h=1.0`-ra fut ki, kiemelkedés nélkül.
* Nem egyenletes (pl. hatványeloszlású) magpont-sűrűség rétegenként — a
  méret-változatosságot kizárólag a rétegzés (`octaves`/`lacunarity`)
  adja, nem a magpontok saját eloszlása.
* A méret/mélység arány finomhangolása a `lacunarity`-tól függetlenül
  (pl. egy külön "mélység-arány" mező) — a projektgazda kifejezett
  kérése szerint ez tudatosan nem önálló paraméter.
