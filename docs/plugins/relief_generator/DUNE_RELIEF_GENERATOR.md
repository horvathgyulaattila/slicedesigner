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
homokdűnék — anizotróp, transzverzális (a széllel keresztben futó)
dűnegerincek, elülső (lankás) és hátsó (meredek) oldalukon eltérő
irányú, kétszinten foltos hullámfodor-mintázattal.

## 2. Négy elutasított tervezet — élő tesztelés tanulságai

1. **Koordináta-alapú fodor-fázis** (`NoiseDistortion`-nal eltolt X-
   koordináta): a fodor teljesen független volt a domb-alaktól —
   "rátett", mesterkélt hatást keltett.
2. **Magasság-alapú fodor-fázis** (a domb-alap MAGASSÁGÁBÓL számított
   fázis, szintvonal-elv): túl szigorúan követte a domborzatot —
   minden dombot koncentrikus gyűrűkbe zárt.
3. **Szélirányú/lejtő-kitettségű fodor, de izotróp domb-alap**: a
   fodor iránya és erőssége már helyesen a szélhez kötődött, de maga a
   domb-ALAP egy irány-független `GradientNoiseField` volt.
4. **Periodikus, aszimmetrikus 1D gerinc-profil**: a domb-ALAPOT is a
   szélirányhoz kötöttük, egy periodikus profilfüggvénnyel,
   szegmentáló zajmezővel véges "testekre" tagolva. Élő tesztelés:
   "teljesen eltűnt a természetes domborzat... Csak egy steril, csupa
   párhuzamos vonalakból álló szinuszhullám maradt." **A kritikus
   tanulság:** egy periodikus, egyetlen 1D-koordinátától függő
   profilfüggvény (bármennyire aszimmetrikus is) alapvetően más
   matematikai objektum, mint egy 2D zajmező — véges, ismétlődő ciklus
   kontra korrelálatlan, végtelen variációjú mező —, ezért sosem adja
   vissza annak szerves karakterét.

## 3. Az ötödik, elfogadott tervezet

A domb-ALAP a korábban dicsért, izotróp `GradientNoiseField`-re épül
vissza, két rétegben: egy durva réteg, amire KIZÁRÓLAG erre a rétegre
alkalmazott, lejtés-alapú (nem érték-alapú) domain-warp ad
aszimmetriát — élő kísérletezés mutatta, hogy a teljes, több-oktávos
mezőn ugyanez a warp összegyűrődést (fold-over torzítást) okoz, mert
sok lokális szélsőértéke van; az egyoktávos, durva rétegen viszont
tiszta, nem-összegyűrődő aszimmetrikus profilt ad. Egy második,
torzítás NÉLKÜLI finomréteg adja hozzá a szerves textúrát. A gerincek
a koordináták anizotróp (szélirányban összenyomott, keresztirányban
nyújtott) torzításával transzverzálisan, a széllel keresztben nyúlnak
meg — ez adja a klasszikus "hullámos sivatag" hatást, amiben a
fodor-mintázat nem keresztezi a nagy gerinceket.

A fodor-réteg a szélirányú lejtés ELŐJELE alapján, lágy átmenettel
keveri az elülső (lankás, keresztirányú fázisú) és a hátsó (meredek,
szélirányú fázisú) mintát — korábbi kísérlet mutatta, hogy egy
"exposure"-alapú, a lejtés abszolútértékét nullázó maszk a domb egész
hátsó felét kopasz sávvá teszi, ami nem volt szándékolt. Mindkét oldal
fodor-erősségét egy KÉTSZINTŰ, egymástól független foltosság
moduláltja: egy domb-szintű (a domb-alappal azonos anizotróp
koordinátatérben mintavételezve, hogy egy-egy gerinccel "együtt
utazzon", és akár teljesen nullázható) és egy dombon-belüli, finomabb,
önmagában sosem nullázó réteg — enélkül a fodrozódás egyenletes,
mesterséges "pizsama"-mintázatot adott.

## 4. Domain-modell

```text
DuneParameters (direction, seed, coarse_scale, ridge_spacing,
                 ridge_length, asymmetry_strength, fine_scale,
                 fine_octaves, fine_persistence, fine_lacunarity,
                 detail_weight, ripple_wavelength_front,
                 ripple_amplitude_front, ripple_wavelength_back,
                 ripple_amplitude_back, ripple_warp_scale,
                 ripple_warp_strength, blend_low, blend_high,
                 patch_dune_scale, patch_dune_low, patch_dune_high,
                 patch_within_scale)

θ = radians(direction)
u(x,y) = x·cosθ + y·sinθ                       — szél menti pozíció
v(x,y) = −x·sinθ + y·cosθ                      — keresztirányú pozíció

--- Domb-alap ---

coarse = GradientNoiseField(coarse_scale, seed)
fine = GradientNoiseField(fine_scale, seed+1, fine_octaves,
                           fine_persistence, fine_lacunarity)

uu(x,y) = u(x,y) · ridge_spacing
vv(x,y) = v(x,y) / ridge_length

Ha asymmetry_strength ≠ 0:
    lejtés_uu = [coarse.sample(uu+ε,vv) − coarse.sample(uu−ε,vv)] / (2ε)
    uu ← uu − asymmetry_strength · lejtés_uu     — CSAK a durva rétegre

alap(x,y) = coarse.sample(uu,vv) + detail_weight · fine.sample(u·ridge_spacing, v/ridge_length)

--- Fodor-réteg ---

lejtés(x,y) = [alap(x+ε·cosθ,y+ε·sinθ) − alap(x−ε·cosθ,y−ε·sinθ)] / (2ε)
keverék(x,y) = smoothstep(clamp((lejtés − blend_low)/(blend_high − blend_low), 0, 1))
               — 1: teljesen elülső minta, 0: teljesen hátsó minta

warp_front = GradientNoiseField(ripple_warp_scale, seed+2)
warp_back  = GradientNoiseField(ripple_warp_scale, seed+3)
patch_dune_front  = GradientNoiseField(patch_dune_scale, seed+4)
patch_dune_back   = GradientNoiseField(patch_dune_scale, seed+5)
patch_within_front = GradientNoiseField(patch_within_scale, seed+6)
patch_within_back  = GradientNoiseField(patch_within_scale, seed+7)

domb_folt_front(x,y) = smoothstep(clamp((patch_dune_front.sample(uu,vv) − patch_dune_low)/(patch_dune_high − patch_dune_low), 0, 1))
domb_folt_back(x,y)  = smoothstep(clamp((patch_dune_back.sample(uu,vv) − patch_dune_low)/(patch_dune_high − patch_dune_low), 0, 1))
belső_folt_front(x,y) = 0.5 + 0.5 · patch_within_front.sample(x,y)
belső_folt_back(x,y)  = 0.5 + 0.5 · patch_within_back.sample(x,y)
folt_front = domb_folt_front · belső_folt_front
folt_back  = domb_folt_back · belső_folt_back

fázis_front(x,y) = v + ripple_warp_strength · warp_front.sample(x,y)
fázis_back(x,y)  = u + ripple_warp_strength · warp_back.sample(x,y)
fodor_front(x,y) = sin(2π / ripple_wavelength_front · fázis_front)
fodor_back(x,y)  = sin(2π / ripple_wavelength_back · fázis_back)

--- Összegzés ---

nyers(x,y) = alap(x,y)
             + keverék · ripple_amplitude_front · folt_front · fodor_front
             + (1−keverék) · ripple_amplitude_back · folt_back · fodor_back

h(x,y) = clamp(0.5 + 0.5 · nyers(x,y), 0, 1)
```

`ε` (`_SLOPE_SAMPLE_EPSILON`) belső, fix konstans: `0.001` —
ugyanaz az érték szolgálja mind az aszimmetria-warp, mind az
elülső/hátsó lejtés véges differenciás becslését.

**Nyíltan jelzett bizonytalanság:** a `coarse_scale`/`ridge_spacing`/
`ridge_length` aránya (a domb-sűrűség) és a `blend_low`/`blend_high`
küszöbök becsült, chat-en belüli előnézetek alapján kalibrált
értékek, nem zárt képletből származnak — élő tesztelés további
finomhangolást igényelhet, de az már csak számok állítása, nem
architektúra-csere.

## 5. Paraméterek

| Paraméter | Típus | Alapérték | Korlát |
|---|---|---|---|
| `direction` | float | 0.0 | bármely valós (fok) |
| `seed` | int | 0 | bármely egész |
| `coarse_scale` | float | 0.2 | szigorúan pozitív |
| `ridge_spacing` | float | 0.9 | szigorúan pozitív |
| `ridge_length` | float | 3.0 | szigorúan pozitív |
| `asymmetry_strength` | float | −0.012 | bármely valós |
| `fine_scale` | float | 0.11 | szigorúan pozitív |
| `fine_octaves` | int | 2 | `≥ 1` |
| `fine_persistence` | float | 0.5 | szigorúan pozitív |
| `fine_lacunarity` | float | 2.0 | szigorúan `> 1` |
| `detail_weight` | float | 0.15 | `≥ 0` |
| `ripple_wavelength_front` | float | 0.035 | szigorúan pozitív |
| `ripple_amplitude_front` | float | 0.055 | `≥ 0` |
| `ripple_wavelength_back` | float | 0.025 | szigorúan pozitív |
| `ripple_amplitude_back` | float | 0.06 | `≥ 0` |
| `ripple_warp_scale` | float | 0.04 | szigorúan pozitív |
| `ripple_warp_strength` | float | 0.015 | bármely valós |
| `blend_low` | float | −6.0 | szigorúan `< blend_high` |
| `blend_high` | float | 6.0 | szigorúan `> blend_low` |
| `patch_dune_scale` | float | 0.2 | szigorúan pozitív |
| `patch_dune_low` | float | −0.5 | szigorúan `< patch_dune_high` |
| `patch_dune_high` | float | 0.5 | szigorúan `> patch_dune_low` |
| `patch_within_scale` | float | 0.16 | szigorúan pozitív |

A nyolc belső zajmező (durva domb-alap, finomréteg, elülső/hátsó
fodor-fázis-zavarás, elülső/hátsó domb-szintű foltosság, elülső/hátsó
dombon-belüli foltosság) a `seed`, `seed+1`, ..., `seed+7` értékeket
kapja, ebben a sorrendben.

## 6. Generátor-választás (ROADMAP Phase 11.0/11.3)

A `generator_type` enum (`registration.py`) `"Dune"` értéke választja
ki ezt a generátort — a Dűne-specifikus mezők a Phase 11.0-ban
bevezetett `ParameterSpec.visible_when` mechanizmuson keresztül
kizárólag ekkor jelennek meg, három csoportba rendezve ("Dűne — alap",
"Dűne — fodor", "Dűne — foltosság") a mezők számának kezelhetősége
érdekében. A meglévő Wave/Voronoi/Crater mezők semmilyen módosítást
nem igényeltek.

## 7. `HeightFieldSource` — generátor-független bekötés

A `DuneHeightFieldSource` (`generators/dune_generator.py`) a Phase
11.1-ben bevezetett `HeightFieldSource` Protocol negyedik
megvalósítása — a `VoronoiHeightFieldSource`/`CraterHeightFieldSource`
mintáját követi. A `ReliefGeneratorParameters`/`ReliefGeneratorMeshSource`
egyike sem igényelt módosítást ehhez a recepthez.

## 8. Hatókörön kívül

* A domb-sűrűség és a küszöbök automatikus (pl. a modell méretéből
  számított) kalibrálása — jelenleg fix, felhasználó által hangolt
  alapértékekkel dolgozunk.
* A fodor-fázis fraktál-kombinációja (több `octaves`) — jelenleg
  mindkét fodor-réteg egyetlen frekvenciával/periódussal dolgozik; a
  gazdagítás kizárólag a domb-alap finomrétegén keresztül történik.
* A domb-szintű és dombon-belüli foltosság küszöbeinek/skálájának
  finomítása — a jelenlegi értékek chat-en belüli előnézet alapján
  becsültek.
* A `_SLOPE_SAMPLE_EPSILON` felhasználó által állítható paraméterré
  tétele — jelenleg belső, fix konstans.
