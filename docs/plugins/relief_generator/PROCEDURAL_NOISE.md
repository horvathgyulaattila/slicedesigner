# Eljárásos zajmező-primitívek (Procedural Noise)

Létrehozva: 2026-08-23
Kapcsolódó ROADMAP-tétel: Phase 10.4
Kapcsolódó BACKLOG-tételek: (korábbi) 3. és 4. tétel — közös alapként

## 1. Cél

Két, egymástól független, determinisztikus 2D zajmező-primitívum —
`GradientNoiseField` (Perlin-szerű) és `VoronoiNoiseField` (cellás/
Worley) —, amelyek a jövőbeli `AmplitudeEnvelope`- (Phase 10.5) és
`Distortion`-bővítések (Phase 10.6) közös alapjául szolgálnak.

Ez a dokumentum KIZÁRÓLAG a két primitívumot írja le — az
`AmplitudeEnvelope`/`Distortion` Protocol-t implementáló becsomagolások
(pl. egy jövőbeli `NoiseAmplitudeEnvelope`) NEM része ennek a tételnek,
azok a Phase 10.5/10.6 saját hatóköre.

## 2. `GradientNoiseField`

### 2.1 Hash-függvény

Tisztán aritmetikai, `random` modul nélküli, determinisztikus hash egy
egész rácsponthoz:

```text
h(ix, iy, seed) = frac(sin(ix·127.1 + iy·311.7 + seed·74.7) · 43758.5453123)
```

`frac(v) = v − floor(v)`, tehát `h(...) ∈ [0.0, 1.0)`.

### 2.2 Gradiens-vektor

```text
angle(ix, iy, seed) = h(ix, iy, seed) · 2π
gradient(ix, iy, seed) = (cos(angle), sin(angle))
```

Egységnyi hosszú, determinisztikus irányvektor minden rácsponton.

### 2.3 Mintavételezés

Egy `(x, y)` ponton, `scale` rácsmérettel:

1. `gx = x/scale`, `gy = y/scale`; egész sarokpontok `(ix0,iy0)`,
   `(ix1,iy1) = (ix0+1,iy0+1)`; törtrész `fx = gx−ix0`, `fy = gy−iy0`.
2. Minden sarokra a gradiens és a saroktól a ponthoz mutató vektor
   skaláris szorzata: `n = gradient · (gx−ix, gy−iy)`.
3. Simított interpolációs súly mindkét tengelyen:
   `smoothstep(t) = 3t² − 2t³`.
4. Bilineáris interpoláció a 4 skaláris szorzat között a simított
   súlyokkal.
5. Normalizálás `√2/2`-vel osztva, majd `[-1.0, 1.0]`-ra vágva
   (numerikus biztonsági háló — az elméleti tartomány gyakorlatilag
   ez, de a vágás garantálja az invariánst).

**Fraktál-kombináció (`octaves > 1`):** `persistence`/`lacunarity`
szerint csökkenő amplitúdójú, növekvő frekvenciájú rétegek összegzése,
normalizálva vissza `[-1.0, 1.0]`-ba — ugyanaz az elv, mint a
`WaveGenerator` automatikus komponens-előállítása
(WAVE_FUNCTION_MODEL.md 22. szakasz), de itt folytonos térbeli zaj, nem
diszkrét komponens-lista.

### 2.4 Invariáns

`sample(x, y) ∈ [-1.0, 1.0]`, minden bemenetre — tesztelve.

## 3. `VoronoiNoiseField`

### 3.1 Mag-pontok

Minden egész rácscellához (`(cix, ciy)`) egy, a cellán belül
determinisztikusan eltolt mag-pont:

```text
seed_x(cix, ciy, seed) = cix + h(cix, ciy, seed)
seed_y(cix, ciy, seed) = ciy + h(cix, ciy, seed+1)
```

### 3.2 Mintavételezés

Egy `(x, y)` ponton, `scale` rácsmérettel: a 3×3 szomszédos cella (a
lekérdezett pontot tartalmazó cella és a nyolc szomszédja)
mag-pontjai közül a legközelebbinek a távolsága (klasszikus "F1"
Worley-zaj), `√2`-vel normalizálva és `[0.0, 1.0]`-ra vágva.

### 3.3 Invariáns

`sample(x, y) ∈ [0.0, 1.0]`, minden bemenetre — tesztelve.

## 4. Miért két különböző tartomány?

Szándékos döntés — nincs mesterségesen egységesített `[-1,1]`/`[0,1]`
konvenció. A `GradientNoiseField` a `[-1,1]`-be képező `WaveFunction`/
jitter-konvenciót követi (0 körül oszcillál); a `VoronoiNoiseField` egy
nem-negatív TÁVOLSÁG-jellegű mennyiség, ami természetesen illeszkedik
az `AmplitudeEnvelope` `[0,1]`-es falloff-konvenciójához
(AMPLITUDE_ENVELOPE.md). A tényleges leképezést a Phase 10.5/10.6-beli
becsomagolások döntik el.

## 5. Determinizmus

Mindkét primitívum tisztán aritmetikai — nem használ `random` modult
vagy bármilyen implicit véletlenszám-állapotot (WAVE_DOMAIN_MODEL.md
14. szakasz elve). Azonos `(x, y, scale, seed, ...)` bemenetre mindig
azonos kimenetet ad, folyamatok/hívások között is.

## 6. Hatókörön kívül

* Az `AmplitudeEnvelope`/`Distortion` Protocol-t implementáló
  becsomagolások — Phase 10.5/10.6.
* GUI-kitettség (`ParameterSpec`) — csak a becsomagolásokkal együtt
  kerül be, ha azok ténylegesen GUI-n konfigurálható paraméterré
  válnak.
* Voronoi F2−F1 vagy más többrétegű Voronoi-kombináció — nincs
  jelenlegi felhasználója, az egyszerűség elve alapján kimarad, amíg
  igény nem merül fel rá.
* 3D/időbeli zaj — kizárólag 2D, statikus (nem animált) mező.
