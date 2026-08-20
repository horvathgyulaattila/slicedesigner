# WAVE_DOMAIN_MODEL.md

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-19
Utolsó módosítás: 2026-08-19
Kapcsolódó dokumentumok: [PROJECT_CONSTITUTION.md](../../PROJECT_CONSTITUTION.md), [WAVE_FUNCTION_MODEL.md](WAVE_FUNCTION_MODEL.md), [AMPLITUDE_ENVELOPE.md](AMPLITUDE_ENVELOPE.md), [RADIAL_WAVE_SOURCE.md](RADIAL_WAVE_SOURCE.md), [WAVE_WEIGHTING.md](WAVE_WEIGHTING.md), [MULTIPLE_WAVE_SOURCES.md](MULTIPLE_WAVE_SOURCES.md), [PROCEDURAL_DISTORTION.md](PROCEDURAL_DISTORTION.md)

## 1. Cél

A jelen dokumentum (ROADMAP Phase 9.1 — Wave model extension) célja a Phase 8-ban elfogadott, kizárólag Directional Wave Source-ra épülő matematikai hullámgenerátor ([WAVE_FUNCTION_MODEL.md](WAVE_FUNCTION_MODEL.md)) domainmodelljének explicit, komponensalapú, bővíthető szerkezetűvé alakítása.

A 9.1 önmagában nem vezet be új matematikai viselkedést a Phase 8-hoz képest — kizárólag a szerkezetet alakítja át úgy, hogy a további Phase 9 alfázisok (9.2–9.6) ráépülhessenek anélkül, hogy a Wave alapfogalmait újra kellene tervezni.

A 9.1 hatóköre:

* egy komponensalapú `Wave` fogalom bevezetése, amely külön kezeli a hullám alakját (`WaveFunction`), terjedését (`PropagationModel`) és térbeli amplitúdómodulációját (`AmplitudeEnvelope`);
* ezen három komponens *absztrakciójának* rögzítése, egyelőre egy-egy konkrét, a Phase 8-cal kompatibilis megvalósítással (Sinusoidal, Directional, Uniform);
* a Phase 8 viselkedésével való visszafelé kompatibilitás megőrzése.

## 2. Domain határai

A Wave domain feladata egy matematikai magasságfüggvény definiálása és kiértékelése.

A domain felelőssége:

* hullámkomponensek definiálása;
* hullámfüggvény meghatározása;
* hullámterjedési modell meghatározása;
* térbeli amplitúdómoduláció meghatározása;
* hullámkomponensek determinisztikus kombinálása;
* az eredmény normalizálásának domain-szintű szabályozása.

A domain nem felelős:

* mesh generálásért;
* STL generálásért;
* mesh javításért;
* geometriai topológiáért;
* CNC toolpath generálásért;
* vizualizációért;
* fájlkezelésért;
* sampling vagy mesh resolution meghatározásáért.

A koncepcionális pipeline:

```text
WaveParameters
      ↓
WaveSet felépítése
      ↓
Wave kiértékelés
      ↓
nyers matematikai mező
      ↓
normalizálás
      ↓
AmplitudeEnvelope alkalmazása
      ↓
HeightField
```

## 3. Domain fogalmak — a teljes Phase 9 célmodell

Az alábbi diagram a teljes Phase 9 (9.1–9.6) végállapotát mutatja, nem csak a 9.1 hatókörét. A zárójeles jelölés mutatja, melyik alfázis vezeti be az adott elemet.

```text
Wave
├── WaveFunction              (9.1: Sinusoidal)
├── PropagationModel          (9.1: Directional | 9.3: Radial)
├── AmplitudeEnvelope         (9.1: Uniform | 9.2: Radial + Falloff)
└── Distortion                (9.6, opcionális komponens)

WaveSet                       (9.1: alapstruktúra | 9.4: explicit többforrás-konfiguráció | 9.5: weight-szemantika)
```

A részletes 9.1-modell:

```text
Wave
├── amplitude
├── wavelength
├── phase
├── weight
├── function
├── propagation
└── envelope

WaveFunction
└── Sinusoidal

PropagationModel
└── Directional            (Radial: lásd RADIAL_WAVE_SOURCE.md)

AmplitudeEnvelope
└── Uniform                (Radial + Falloff: lásd AMPLITUDE_ENVELOPE.md)
```

A modell szándékosan komponensalapú. A `Wave` nem tartalmazza közvetlenül a propagation vagy az envelope konkrét matematikai logikáját.

## 4. Wave

### 4.1 Definíció

A `Wave` egy konkrét matematikai hullámkomponenst reprezentáló domain objektum.

Egy Wave az alábbi tulajdonságokból épül fel:

* amplitude;
* wavelength;
* phase;
* weight;
* WaveFunction;
* PropagationModel;
* AmplitudeEnvelope.

Általános alakja:

```text
f_i(x,y) = w_i · A_i · M_i(x,y) · W_i(P_i(x,y), λ_i, φ_i)
```

ahol:

* `A_i` = amplitude;
* `w_i` = weight;
* `M_i(x,y)` = amplitude envelope;
* `W_i` = WaveFunction;
* `P_i(x,y)` = a PropagationModel által meghatározott térbeli pozíció;
* `λ_i` = wavelength;
* `φ_i` = phase.

A 9.1 modellben `W_i` = Sinusoidal.

## 5. Wave paraméterek

### 5.1 Amplitude

Az `amplitude` a hullám saját amplitúdóját határozza meg.

Invariáns: `A_i > 0`.

Az amplitude a hullám intrinsic erőssége.

### 5.2 Wavelength

A `wavelength` a hullám térbeli periódusát határozza meg.

Invariáns: `λ_i > 0`.

A wavelength és a térbeli koordináták ugyanabban a koordinátarendszerben értelmezendők. A domain nem írja elő, hogy a wavelengthnek el kell férnie a teljes generált felületen — egyaránt érvényes `λ ≫ panel size` és `λ ≪ panel size`. A gyakorlati mintavételi korlátok nem a Wave domain felelőssége.

### 5.3 Phase

A `phase` a hullám fáziseltolását határozza meg. Az értéknek véges numerikus értéknek kell lennie. A phase normalizálása domain szinten nem kötelező; matematikailag ekvivalens phase-reprezentációk használata megengedett.

### 5.4 Weight

A `weight` azt határozza meg, hogy az adott hullámkomponens milyen mértékben járul hozzá a WaveSet eredményéhez. Alapértelmezett érték: `w_i = 1`.

A weight és az amplitude külön fogalmak — az `amplitude` a hullám saját amplitúdója, a `weight` a komponens hozzájárulása a kompozícióhoz. A weight szemantikájának részletes kifejtése (negatív érték, `weight = 0` érvényessége) a [WAVE_WEIGHTING.md](WAVE_WEIGHTING.md) (9.5) tárgya.

## 6. WaveFunction

### 6.1 Definíció

A `WaveFunction` azt határozza meg, hogy milyen matematikai alakú maga a hullám. Külön domainfogalom, hogy a `Wave` ne legyen szükségtelenül a szinuszos hullámhoz kötve.

### 6.2 Sinusoidal

A Phase 8 alapmodelljének megfelelő szinuszos hullámot reprezentálja:

```text
W(P, λ, φ) = sin( (2π / λ) · P + φ )
```

Ez biztosítja a Phase 8 matematikai viselkedésének megőrzését.

### 6.3 Jövőbeli WaveFunctionök

A domainmodell később lehetővé teszi további WaveFunctionök bevezetését (pl. Cosine, Triangle, Sawtooth), de ezek nem részei a 9.1 scope-jának.

## 7. PropagationModel

### 7.1 Definíció

A `PropagationModel` azt határozza meg, hogyan határozható meg a hullám fázispozíciója az adott térbeli koordinátán — a kérdés: *hol tart a hullám a ciklusában az adott térbeli pozíción?* Ez különbözik az amplitude envelope kérdésétől (*milyen erősen érvényesüljön a hullám az adott térbeli pozíción?*).

A domainmodell nem köti a propagationt kizárólag egyszerű távolságfüggvényhez, ami lehetővé teszi későbbi propagation modellek (pl. Radial, lásd [RADIAL_WAVE_SOURCE.md](RADIAL_WAVE_SOURCE.md)) bevezetését.

### 7.2 DirectionalPropagation

A `Directional` propagation síkhullámot reprezentál. A térbeli fázispozíció:

```text
P(x,y) = x·cos(θ) + y·sin(θ)
```

ahol `θ` a hullám iránya. A direction értékének véges numerikus értéknek kell lennie; a domain nem követeli meg a `0 ≤ θ < 2π` feltételt — az egymással `2π`-vel eltérő irányértékek matematikailag ekvivalensnek tekinthetők.

## 8. AmplitudeEnvelope

### 8.1 Definíció

Az `AmplitudeEnvelope` a hullám térbeli amplitúdómodulációját határozza meg: `M(x,y)`.

Invariáns: `0 ≤ M(x,y) ≤ 1`. Az envelope nem erősíti fel a hullámot, csak annak térbeli amplitúdóját csökkenti.

### 8.2 UniformEnvelope

A Uniform envelope a térbeli amplitúdómoduláció hiányát jelenti: `M(x,y) = 1`. Ez az alapértelmezett envelope. Uniform envelope esetén a 9.1 matematikai eredménye a Phase 8 azonos konfigurációjú eredményével kompatibilis.

A Radial envelope és a Falloff-modellek (Linear, Smooth, Gaussian) a [AMPLITUDE_ENVELOPE.md](AMPLITUDE_ENVELOPE.md) (9.2) dokumentumban kerülnek kidolgozásra.

## 9. WaveSet

### 9.1 Definíció

A `WaveSet` konkrét `Wave` komponensek rendezett gyűjteménye. A nyers matematikai mező:

```text
F(x,y) = Σ f_i(x,y)   (i = 1..n)
```

A WaveSet feladata: Wave komponensek tárolása; komponensek determinisztikus sorrendjének megőrzése; komponensek összegzése. A WaveSet legalább egy Wave komponenst tartalmaz.

### 9.2 Nem felelőssége

A WaveSet nem generál mesh-t, nem generál STL-t, nem határozza meg a sampling resolutiont, nem jelenít meg adatot, nem kezel GUI-paramétereket.

A WaveSet explicit, felhasználói szinten megadható többforrás-konfigurációja a [MULTIPLE_WAVE_SOURCES.md](MULTIPLE_WAVE_SOURCES.md) (9.4) tárgya.

## 10. WaveParameters és WaveSet

A meglévő `WaveParameters` továbbra is magasabb szintű generálási paramétereket reprezentál:

```text
WaveParameters
      ↓
determinisztikus komponens-felépítés
      ↓
WaveSet
```

A `WaveParameters` és a `Wave` nem ugyanazt a fogalmat jelenti. A `WaveParameters` például tartalmazhat: wavelength, amplitude, direction, direction spread, irregularity, complexity, seed. A konkrét generálás során ezekből konkrét `Wave` komponensek állnak elő — ez biztosítja a Phase 8 magasabb szintű paraméterezésének folytonosságát.

## 11. Koordinátarendszer

A Wave domain nem köti a koordinátákat automatikusan normalizált (`[0,1]`) tartományhoz. A következő értékek — `(x,y)`, wavelength, radial source, envelope center, radius — azonos és konzisztens koordinátarendszerben értendők. A koordinátarendszer mértékegységét a domainmodell nem rögzíti (lehet például milliméter). A Wave domain számára kizárólag a belső konzisztencia szükséges.

## 12. Normalizálás

A WaveSet nyers eredménye: `F(x,y) = Σ f_i(x,y)`.

A normalizálás:

```text
N(F) = (F − F_min) / (F_max − F_min)
```

A normalizálás az amplitude envelope alkalmazása előtt történik. A végső matematikai felület:

```text
H(x,y) = N(F(x,y)) · M(x,y)
```

Az envelope alkalmazása után **nincs újranormalizálás** — ez kötelező domainviselkedés.

## 13. Degenerált normalizálás

Ha `F_max = F_min`, a normál normalizálási képlet nevezője nulla lenne. Ebben az esetben `N(F) = 0` minden ponton. Ez érvényes, determinisztikus eredmény, nem domainhiba — például akkor fordulhat elő, ha minden komponens hozzájárulása nulla.

## 14. Determinizmus

A Wave domainnek determinisztikusnak kell lennie. Azonos `WaveParameters`, `WaveSet` konstrukciós bemenetek, WaveFunction paraméterek, propagation paraméterek, envelope paraméterek és — ahol releváns — random seed esetén azonos matematikai `HeightField` eredménynek kell létrejönnie. A véletlenszerűség nem függhet implicit globális állapottól; a későbbi procedurális randomness (lásd [PROCEDURAL_DISTORTION.md](PROCEDURAL_DISTORTION.md), 9.6) explicit, determinisztikus seedhez kötendő.

## 15. Phase 8 backward compatibility

A 9.1 modellnek meg kell őriznie a Phase 8 viselkedését azonos konfiguráció mellett. A kompatibilis alapkonfiguráció:

```text
WaveFunction = Sinusoidal
Propagation   = Directional
Envelope      = Uniform
Weight        = 1
```

Azonos bemenetek és determinisztikus állapot esetén: `H_9.1(x,y) = H_Phase8(x,y)`. A backward compatibility a 9.1 validációjának kötelező része.

## 16. Bővíthetőségi alapelvek

A 9.1 domainmodellnek lehetővé kell tennie további modellek hozzáadását az alapfogalmak újratervezése nélkül.

### 16.1 WaveFunction

Később hozzáadható például: Cosine, Triangle, Sawtooth, egyéb periodikus matematikai függvény.

### 16.2 PropagationModel

Később hozzáadható további propagation modell (elsőként: Radial, [RADIAL_WAVE_SOURCE.md](RADIAL_WAVE_SOURCE.md), 9.3). A domainmodell nem feltételezi, hogy minden propagation egyszerű lineáris vagy radiális távolságfüggvény.

### 16.3 AmplitudeEnvelope

Később hozzáadható például: Directional, Rectangular, Image, HeightMap, Vector envelope (elsőként: Radial + Falloff, [AMPLITUDE_ENVELOPE.md](AMPLITUDE_ENVELOPE.md), 9.2). Az envelope továbbra is az `M(x,y)` amplitúdómodulációs szerződést teljesíti.

### 16.4 Domain warping / Distortion

A domain warping nem része a 9.1-nek. A domainmodell azonban nem zárhatja ki egy későbbi külön domainfogalom bevezetését — ezt a [PROCEDURAL_DISTORTION.md](PROCEDURAL_DISTORTION.md) (9.6) vezeti be, koordináta-torzításként, a `PropagationModel` kiértékelése előtt beavatkozó, önálló komponensként.

### 16.5 Envelope compositing

Több envelope kombinációja nem része a 9.1-nek. A modell azonban lehetővé teszi egy későbbi `CompositeEnvelope` fogalom bevezetését; ezt nem szükséges most implementálni vagy részletesen definiálni.

## 17. Kompozíciós határ

A `WaveSet` egyszerű komponensgyűjtemény: `F = Σ f_i`. A 9.1 nem vezet be nested `WaveSet` struktúrát — tehát a `WaveSet` nem tartalmazhat beágyazott `WaveSet`-eket. Összetettebb kompozíciós modellek későbbi külön domain döntést igényelnek.

## 18. A Wave nem lehet „mindent tudó” objektum

A domainmodellnek kerülni kell azt a struktúrát, amelyben minden későbbi funkció közvetlenül a `Wave` paraméterei közé kerül.

Nem kívánt modell:

```text
Wave
├── amplitude
├── wavelength
├── phase
├── direction
├── source
├── radial_radius
├── gaussian_strength
├── noise
├── distortion
├── image
├── vector
└── ...
```

Kívánt modell:

```text
Wave
├── amplitude
├── wavelength
├── phase
├── weight
├── WaveFunction
├── PropagationModel
└── AmplitudeEnvelope
```

A komponensek saját felelősségi körükben maradnak.

## 19. Scope — 9.1 része

```text
Wave
│
├── WaveFunction
│    └── Sinusoidal
│
├── PropagationModel
│    └── Directional
│
└── AmplitudeEnvelope
     └── Uniform

WaveSet
Normalization contract
Edge-case contract
Backward compatibility contract
```

## 20. Scope — 9.1-en kívül

Nem része a 9.1-nek:

* RadialPropagation ([RADIAL_WAVE_SOURCE.md](RADIAL_WAVE_SOURCE.md), 9.3);
* Radial AmplitudeEnvelope és Falloff-modellek ([AMPLITUDE_ENVELOPE.md](AMPLITUDE_ENVELOPE.md), 9.2);
* explicit, felhasználói szinten megadható többforrás-konfiguráció ([MULTIPLE_WAVE_SOURCES.md](MULTIPLE_WAVE_SOURCES.md), 9.4);
* a weight szemantika részletes kifejtése ([WAVE_WEIGHTING.md](WAVE_WEIGHTING.md), 9.5);
* koordináta-torzítás / Distortion ([PROCEDURAL_DISTORTION.md](PROCEDURAL_DISTORTION.md), 9.6);
* további WaveFunction implementációk;
* envelope compositing;
* image-based, heightmap-based, vector-based envelope;
* önálló noise generator;
* mesh generation, mesh optimization, adaptive sampling, sampling resolution meghatározása, STL export, CNC toolpath generálás;
* GUI-implementáció (widget-elrendezés, konkrét Qt-kód);
* preset rendszer.

**Fontos pontosítás:** a GUI-implementáció kizárása **nem** jelenti azt, hogy a generátor-konfiguráció (pl. a jövőbeli, 9.4-ben tervezett explicit forráslista) nem tartalmazhat felhasználó által megadható paramétereket. A projekt már rendelkezik egy általános, deklaratív paraméter-séma mechanizmussal (`MeshSourceDescriptor`/`ParameterSpec`, ADR-0017), amely a domain-szinten deklarált paraméterekből automatikusan generál interaktív GUI-mezőt, plugin-specifikus Qt-kód nélkül. A "GUI kizárva" tehát a *GUI-implementációra* vonatkozik, nem a *paraméterek generátor-konfigurációban való létezésére*.

## 21. Architekturális határok

A Wave domain független marad: a `HeightField` konkrét implementációjától; a `ReliefGeometry` modelltől; a mesh generátortól; az STL szerializációtól; a Slice Engine-től; a GUI-tól. A matematikai hullámgenerálás kimeneti határa továbbra is a meglévő `HeightField` szerződés. A 9.1 nem módosítja a Geometry és Mesh rétegek alapvető felelősségi köreit.

## 22. Összefoglaló domainmodell

```text
                         WaveParameters
                               │
                               ▼
                            WaveSet
                               │
                         Wave, Wave, ...
                               │
                  ┌────────────┼────────────┐
                  ▼            ▼            ▼
             amplitude   WaveFunction  Propagation   Envelope
                              │            │            │
                              ▼            ▼            ▼
                         Sinusoidal   Directional     Uniform
```

A matematikai feldolgozás:

```text
WaveParameters
      ↓
WaveSet construction
      ↓
Wave evaluation
      ↓
raw field F(x,y)
      ↓
normalization N(F)
      ↓
AmplitudeEnvelope M(x,y)
      ↓
H(x,y) = N(F) · M(x,y)
      ↓
HeightField
```

## 23. A 9.1 végleges domainfilozófiája

A 9.1 domainmodellben az alábbi felelősségek különülnek el:

1. **`Wave`** — egy konkrét hullámkomponens.
2. **`WaveFunction`** — milyen matematikai alakú a hullám.
3. **`PropagationModel`** — hogyan helyezkedik el a hullám fázisa a térben.
4. **`AmplitudeEnvelope`** — hol és milyen mértékben érvényesül a hullám amplitúdója.
5. **`WaveSet`** — hogyan kombinálódnak a hullámkomponensek.
6. **Normalization** — hogyan válik a komponált matematikai mező normalizált felületté.
7. **`HeightField`** — a matematikai domain kimeneti határa.

A modell célja nem a lehető legtöbb jövőbeli funkció előzetes megvalósítása, hanem az, hogy a jelenlegi matematikai hullámgenerátor egyszerű, tiszta és bővíthető domainalapot kapjon. A későbbi Phase 9 fejlesztések (9.2–9.6) erre a modellre épülnek; a 9.1-ben definiált fogalmakat pusztán implementációs kényelmi okból nem szükséges újratervezni — az ettől eltérő igény külön domain-döntést jelent.
