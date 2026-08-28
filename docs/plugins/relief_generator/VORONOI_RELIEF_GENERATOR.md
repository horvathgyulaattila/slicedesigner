# Voronoi Relief Generator

Kapcsolódó dokumentumok: [PROCEDURAL_NOISE.md](PROCEDURAL_NOISE.md),
[WAVE_FUNCTION_MODEL.md](WAVE_FUNCTION_MODEL.md) (18–20. szakasz, a
`HeightField` generátor-független szerződése).

Státusz: Elfogadva
ROADMAP: Phase 11.1

## 1. Cél

A Voronoi Relief Generator a `BACKLOG.md` (korábbi) 1. tételéből
származó négy procedurális Height Field recept közül az első és
legegyszerűbb: egy nyers cellás/Worley-zaj felület, közvetlenül a Phase
10.4-es `VoronoiNoiseField`-re építve.

## 2. Domain-modell

```text
VoronoiParameters (scale, seed)
        │
        ▼
   VoronoiNoiseField
        │
        ▼
    HeightField
```

A `VoronoiNoiseField.sample(x, y)` már `[0.0, 1.0]`-be esik
(PROCEDURAL_NOISE.md) — nincs szükség normalizálásra, ellentétben a
`WaveGenerator`-ral (WAVE_FUNCTION_MODEL.md 23. szakasz).

## 3. Paraméterek

| Paraméter | Típus | Alapérték | Korlát |
|---|---|---|---|
| `scale` | float | 0.2 | szigorúan pozitív |
| `seed` | int | 0 | bármely egész |

## 4. Generátor-választás (ROADMAP Phase 11.0/11.1)

A relief_generator plugin egyetlen `MeshSourceDescriptor`-t regisztrál
(nem önálló pluginként) — a `generator_type` (`"Wave"`/`"Voronoi"`) enum
`ParameterSpec` választja ki a tényleges generátort. A Wave-specifikus
mezők (11 db) és a Voronoi-specifikus mezők (`voronoi_scale`,
`voronoi_seed`) a Phase 11.0-ban bevezetett `ParameterSpec.visible_when`
mechanizmuson keresztül kölcsönösen kizárva jelennek meg a GUI-n.

## 5. `HeightFieldSource` — generátor-független bekötés

A `ReliefGeneratorParameters.height_field_source: HeightFieldSource`
(egy egymetódusú Protocol,
`plugins/relief_generator/source/relief_generator_parameters.py`)
absztrahálja a konkrét generátort a `ReliefGeneratorMeshSource` elől. A
`WaveHeightFieldSource` (`generators/wave_generator.py`) és a
`VoronoiHeightFieldSource` (`generators/voronoi_generator.py`) ugyanazt
a mintát követi: a saját paraméter-dataclass-t és a hozzá tartozó
generátor-osztályt fogja össze egyetlen `build_height_field() ->
HeightField` metódus mögé. Ez a mechanizmus lehetővé teszi, hogy a
jövőbeli receptek (11.2 Holdkráter, 11.3 Dűne, 11.4 Faerezet) a
`ReliefGeneratorMeshSource`/`ReliefGeneratorParameters` módosítása
nélkül csatlakozzanak be.

## 6. Hatókörön kívül

* Közös "Height Field Recipe" absztrakció a paraméter-dataclassok vagy a
  `ParameterSpec` GUI-mezők szintjén — a `HeightFieldSource` Protocol a
  `generators/` rétegben elegendő keretnek bizonyult.
* A Voronoi-cellák alakjának torzítása (holdkráter, dűne stb.) — ezek a
  11.2–11.4 saját, önálló receptjei.
