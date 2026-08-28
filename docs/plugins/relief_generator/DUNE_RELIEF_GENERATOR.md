# Dune Relief Generator

Kapcsolódó dokumentumok: [PROCEDURAL_NOISE.md](PROCEDURAL_NOISE.md) (a
`GradientNoiseField` domain-contractja, amire ez a generátor épül),
[WAVE_FUNCTION_MODEL.md](WAVE_FUNCTION_MODEL.md) (18–20. szakasz, a
`HeightField` generátor-független szerződése).

Státusz: Elfogadva
ROADMAP: Phase 11.3

## 1. Cél

A Dune Relief Generator a `BACKLOG.md` (korábbi) 1. tételéből származó
négy procedurális Height Field recept közül a harmadik: szélfútta
homokdűnék — anizotróp, szélirány-mentén aszimmetrikus dűnegerincek,
véges testekre tagolva, a felszínükön a szélirányt és a lejtő szél
felőli kitettségét követő, finom hullámfodor-mintázattal.

## 2. Három elutasított tervezet — élő tesztelés tanulságai

1. **Koordináta-alapú fodor-fázis** (`NoiseDistortion`-nal eltolt X-
   koordináta): a fodor teljesen független volt a domb-alaktól —
   "rátett", mesterkélt hatást keltett.
2. **Magasság-alapú fodor-fázis** (a domb-alap MAGASSÁGÁBÓL számított
   fázis, szintvonal-elv): túl szigorúan követte a domborzatot —
   minden dombot koncentrikus gyűrűkbe zárt.
3. **Szélirányú/lejtő-kitettségű fodor, de izotróp domb-alap**: a
   fodor iránya és erőssége már helyesen a szélhez kötődött, de maga a
   domb-ALAP egy irány-független `GradientNoiseField` volt — a valódi
   dűnéknek viszont a szél mentén nézve lankás/hosszú, arra
   merőlegesen nézve éles/keskeny, ÉS aszimmetrikus (lankás elöl,
   meredek hátul) alakjuk van, amit egy izotróp zajmező nem tud
   kifejezni.

## 3. A negyedik terv: anizotróp, szélirányú dűnegerinc

A domb-ALAP is a szélirányhoz kötött: egy periodikus, aszimmetrikus
profilfüggvény a szélirány menti koordinátán (nem zajmező), egy
második, nagy léptékű zajmezővel véges "testekre" szegmentálva.

## 4. Domain-modell

```text
DuneParameters (dune_spacing, asymmetry, segment_scale,
                 ripple_wavelength, ripple_amplitude, warp_scale,
                 warp_strength, direction, slope_sensitivity, seed)

θ = radians(direction)
u(x,y) = x·cosθ + y·sinθ                                — szél menti pozíció

gerinc(u) = aszimmetrikus, periodikus profil (dune_spacing periódussal,
            asymmetry aránnyal a meredek, szélárnyékos szakaszra)
            — lankás felfutás, meredek lezuhanás egy cikluson belül

szakasz(x,y) = GradientNoiseField(segment_scale, seed).sample(x,y), [0,1]-re alakítva
               — végessé, egyedi "testekre" tagolja a gerinceket

alap(x,y) = 0.5 + RIDGE_HEIGHT · (gerinc(u) − 0.5) · szakasz(x,y)
            (RIDGE_HEIGHT belső, fix konstans: 0.9)

lejtés(x,y) = [alap(x+ε·cosθ, y+ε·sinθ) − alap(x−ε·cosθ, y−ε·sinθ)] / (2ε)
              (irányított, véges differenciás derivált; ε belső, fix konstans)

szél_kitettség(x,y) = clamp(lejtés(x,y) · slope_sensitivity, 0, 1)

fázis(x,y) = x·cosθ + y·sinθ + warp_strength · GradientNoiseField(warp_scale, seed+1).sample(x,y)
fodor(x,y) = sin(2π / ripple_wavelength · fázis(x,y))

h(x,y) = clamp(alap(x,y) + ripple_amplitude · szél_kitettség(x,y) · fodor(x,y), 0, 1)
```

Összeadás, nem `min`-kombinálás (szemben a Crater Generatorral, l.
CRATER_RELIEF_GENERATOR.md 4. szakasz) — a hullámfodor a domb
FELSZÍNÉN ül.

**Nyíltan jelzett bizonytalanság:** a `dune_spacing`/`asymmetry`/
`segment_scale`/`slope_sensitivity` alapértékeit becsültük, nem zárt
képletből származnak — élő tesztelés minden korábbinál nagyobb eséllyel
igényel további finomhangolást, de az már csak számok állítása, nem
architektúra-csere.

## 5. Paraméterek

| Paraméter | Típus | Alapérték | Korlát |
|---|---|---|---|
| `dune_spacing` | float | 0.3 | szigorúan pozitív |
| `asymmetry` | float | 0.25 | `(0, 1)` |
| `segment_scale` | float | 0.5 | szigorúan pozitív |
| `ripple_wavelength` | float | 0.03 | szigorúan pozitív |
| `ripple_amplitude` | float | 0.08 | szigorúan pozitív |
| `warp_scale` | float | 0.15 | szigorúan pozitív |
| `warp_strength` | float | 0.02 | bármely véges valós |
| `direction` | float | 0.0 | bármely valós (fok) |
| `slope_sensitivity` | float | 3.0 | bármely valós (becsült, hangolandó) |
| `seed` | int | 0 | bármely egész |

A két belső zajmező (dűnetest-szegmentálás, fodor-fázis-zavarás) a
`seed`, `seed+1` értékeket kapja.

## 6. Generátor-választás (ROADMAP Phase 11.0/11.3)

A `generator_type` enum (`registration.py`) `"Dune"` értéke választja
ki ezt a generátort — a Dűne-specifikus mezők a Phase 11.0-ban
bevezetett `ParameterSpec.visible_when` mechanizmuson keresztül
kizárólag ekkor jelennek meg. A meglévő Wave/Voronoi/Crater mezők
semmilyen módosítást nem igényeltek a `generator_type` negyedik
értékének bevezetéséhez.

## 7. `HeightFieldSource` — generátor-független bekötés

A `DuneHeightFieldSource` (`generators/dune_generator.py`) a Phase
11.1-ben bevezetett `HeightFieldSource` Protocol negyedik
megvalósítása — a `VoronoiHeightFieldSource`/`CraterHeightFieldSource`
mintáját követi. A `ReliefGeneratorParameters`/`ReliefGeneratorMeshSource`
egyike sem igényelt módosítást ehhez a recepthez.

## 8. Hatókörön kívül

* Fraktál-kombinált (több `octaves`) fodor- vagy gerinc-mintázat — a
  jelen recept egyetlen frekvenciával/periódussal dolgozik mindkét
  rétegen.
* A `RIDGE_HEIGHT` felhasználó által állítható paraméterré tétele —
  jelenleg belső, fix konstans.
* A `slope_sensitivity` automatikus (pl. a `dune_spacing`-ből
  számított) kalibrálása — jelenleg fix, felhasználó által hangolt
  alapértékkel dolgozunk.
