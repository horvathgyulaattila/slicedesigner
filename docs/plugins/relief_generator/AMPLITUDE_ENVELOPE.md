# AMPLITUDE_ENVELOPE.md

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-19
Utolsó módosítás: 2026-08-19
Kapcsolódó dokumentumok: [WAVE_DOMAIN_MODEL.md](WAVE_DOMAIN_MODEL.md)

## 1. Cél

A jelen dokumentum (ROADMAP Phase 9.2 — Spatial amplitude envelope) a [WAVE_DOMAIN_MODEL.md](WAVE_DOMAIN_MODEL.md) (9.1) 8. szakaszában rögzített `AmplitudeEnvelope` absztrakciót konkretizálja egy térbeli, középpont körüli amplitúdómodulációs modellel (`Radial`), három falloff-változattal.

## 2. RadialAmplitudeEnvelope

A `Radial` envelope egy megadott középpont körül végzi az amplitúdómodulációt.

Paraméterei: center X; center Y; radius; falloff.

A térbeli távolság:

```text
d = √( (x − x_c)² + (y − y_c)² )
```

A center nincs a generált felület határain belülre korlátozva. A radius pozitív valós érték (`R > 0`); lehet nagyobb a teljes panel méreténél. A domain nem ír elő mesterséges minimális vagy maximális radiusértéket.

## 3. Radial envelope center

A radial envelope center önálló domainparaméter. Nem azonos automatikusan: a geometriai középponttal; a RadialPropagation source pozíciójával ([RADIAL_WAVE_SOURCE.md](RADIAL_WAVE_SOURCE.md)); bármely más domainobjektum középpontjával. A center a vizsgált domainen kívül is elhelyezhető — ez érvényes és támogatott konfiguráció.

## 4. Radial Falloff

A radial envelope három falloff modellt támogat: Linear, Smooth, Gaussian. A falloff azt határozza meg, hogyan változik az envelope amplitúdója a centerhez viszonyított távolság függvényében. A három modell eltérően értelmezi a radiuson túli tartományt.

## 5. Linear Falloff

```text
t = clamp(d / R, 0, 1)
M(t) = 1 − t
```

A radiuson kívül `M = 0`. A Linear envelope tehát véges támogatású.

## 6. Smooth Falloff

Smoothstep függvényt használ:

```text
S(t) = 3t² − 2t³
M(t) = 1 − S(t) = 1 − 3t² + 2t³
```

ahol `t = clamp(d / R, 0, 1)`. A radiuson kívül `M = 0`. A Smooth célja a Linear modellnél lágyabb amplitúdóátmenet.

## 7. Gaussian Falloff

```text
M(t) = e^(−k·t²)
t = d / R
```

ahol `R` = reference radius, `k` = Gaussian sharpness (domain/felhasználói paraméter). Invariáns: `k > 0`. Nagyobb `k` gyorsabb lecsengést és koncentráltabb envelope-et eredményez; kisebb `k` lassabb lecsengést és szélesebb envelope-et.

## 8. Gaussian radius

A Gaussian esetében a radius **referencia-skála**, nem hard cutoff — ezért `t = d / R` **clamp nélkül** kerül kiszámításra. Ennek következménye: `d > R` esetén is `M(d) > 0` véges `d` esetén. A Gaussian elméletileg nem éri el pontosan a nullát véges távolságban (`e^(−k·t²) > 0`), de `t → ∞` esetén `M(t) → 0`. A domainmodell nem tartalmaz mesterséges Gaussian cutoffot vagy epsilon-alapú levágást.

## 9. Gaussian sharpness határesetek

A domainfeltétel `k > 0`. A `k → 0+` tartományban `M(t) → 1`, tehát a Gaussian egyre inkább Uniform viselkedést mutat. Nagyon nagy `k` esetén a hatás egyre koncentráltabbá válik a center körül. A domainmodell nem határoz meg mesterséges felső korlátot; a felhasználói felület később meghatározhat praktikus értéktartományt.

## 10. Envelope által létrehozott konstans nulla eredmény

Ha az envelope minden vizsgált ponton `M(x,y) = 0`, akkor `H(x,y) = 0` minden ponton. Ez érvényes eredmény. Az ilyen eredményt az envelope alkalmazása után nem szabad újranormalizálni (lásd [WAVE_DOMAIN_MODEL.md](WAVE_DOMAIN_MODEL.md) 12. szakasz).

## 11. NoiseAmplitudeEnvelope (ROADMAP Phase 10.5)

A `Noise` envelope a Phase 10.4-ben bevezetett `GradientNoiseField`/
`VoronoiNoiseField` primitívumok egyikét csomagolja be
`AmplitudeEnvelope`-ként, egy apró, helyben (`amplitude_envelope.py`)
definiált `NoiseSource` Protocol-lal (`sample(x,y) -> float`) — mindkét
primitívum már ezt a metódus-aláírást implementálja, structural
typing-gal, a `procedural_noise.py` módosítása nélkül.

```text
raw = noise.sample(x, y)
normalized = (raw − input_min) / (input_max − input_min)
M(x,y) = clamp(normalized, 0, 1)
```

`input_min`/`input_max` alapértéke `0.0`/`1.0` — ez a `VoronoiNoiseField`
natív tartományának felel meg, nem igényel remapet.
`GradientNoiseField`-hez `input_min=-1.0, input_max=1.0` adandó meg (a
GUI-bekötés, l. `registration.py`, ezt automatikusan beállítja a
választott zajtípus szerint).

Nincs invertálás — a `VoronoiNoiseField` cellahatárai (nagy F1-távolság)
adják a magas amplitúdót, a mag-pontok közelsége (kis távolság) az
alacsonyat; ha a fordított viselkedés válik szükségessé, az külön,
jövőbeli kiegészítés.

## 12. Kivétel

`NoiseAmplitudeEnvelopeValueError` — akkor dobódik, ha
`input_max <= input_min`.
