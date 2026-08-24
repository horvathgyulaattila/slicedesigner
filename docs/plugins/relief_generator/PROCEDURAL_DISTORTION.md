# PROCEDURAL_DISTORTION.md

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-19
Utolsó módosítás: 2026-08-19
Kapcsolódó dokumentumok: [WAVE_DOMAIN_MODEL.md](WAVE_DOMAIN_MODEL.md)

## 1. Cél

A jelen dokumentum (ROADMAP Phase 9.6 — Controlled procedural distortion) a [WAVE_DOMAIN_MODEL.md](WAVE_DOMAIN_MODEL.md) (9.1) 16.4 szakaszában előre jelzett `Distortion` domain fogalmat konkretizálja: egy önálló, opcionális, per-`Wave` komponenst, amely az adott `Wave` saját `PropagationModel`-jének kiértékelése *előtt* torzítja a térbeli koordinátákat.

## 2. Distortion

### 2.1 Definíció

A `Distortion` egy koordináta-transzformációt definiál: `(x,y) → (x',y')`, amelyet a `Wave` kiértékelése a `PropagationModel` elé, annak bemeneteként alkalmaz. A `Wave` [WAVE_DOMAIN_MODEL.md](WAVE_DOMAIN_MODEL.md) 4.1 szakaszában rögzített általános alakja emiatt így egészül ki:

```text
f_i(x,y) = w_i · A_i · M_i(x,y) · W_i(P_i(Dist_i(x,y)), λ_i, φ_i)
```

ahol `Dist_i` az adott `Wave` komponens (opcionális) `Distortion`-je.

A `Distortion` — csakúgy mint a `WaveFunction`, a `PropagationModel` és az `AmplitudeEnvelope` — önálló komponens, nem kerül közvetlenül a `Wave` mezői közé ([WAVE_DOMAIN_MODEL.md](WAVE_DOMAIN_MODEL.md) 18. szakasz, "A Wave nem lehet mindent tudó objektum").

### 2.2 Alapértelmezett viselkedés

Egy `Wave` alapértelmezetten nem rendelkezik `Distortion`-nel — ekkor `Dist_i` az identitás-transzformáció (`x' = x`, `y' = y`). Ez biztosítja a Phase 8/9.1–9.5 backward compatibility-t olyan konfigurációban, ahol `Distortion` nincs megadva (lásd 8. szakasz).

## 3. SwirlDistortion

A 9.6 első köre egyetlen konkrét `Distortion`-típust vezet be: a `SwirlDistortion`-t, amely egy megadott középpont körül, a távolsággal csökkenő mértékben forgatja el a koordinátákat.

Paraméterei: center X; center Y; radius; strength.

A térbeli távolság:

```text
d = √( (x − x_c)² + (y − y_c)² )
```

A forgatási szög:

```text
α(d) = strength · e^(−(d/radius)²)
```

A torzított koordináták:

```text
x' = x_c + (x − x_c)·cos(α) − (y − y_c)·sin(α)
y' = y_c + (x − x_c)·sin(α) + (y − y_c)·cos(α)
```

A `radius` **referencia-skála**, nem hard cutoff — a lecsengés Gaussian-jellegű, ugyanúgy, ahogyan az [AMPLITUDE_ENVELOPE.md](AMPLITUDE_ENVELOPE.md) Gaussian Falloffja (7–8. szakasz): `d > radius` esetén is `α(d) ≠ 0` véges `d`-re, de `d → ∞` esetén `α(d) → 0`. Invariáns: `radius > 0`.

## 4. SwirlDistortion center

A `SwirlDistortion` centere önálló domainparaméter — nem azonos automatikusan a `RadialPropagation` source pozíciójával, sem az `AmplitudeEnvelope` centerével (ugyanaz a függetlenségi elv, mint [AMPLITUDE_ENVELOPE.md](AMPLITUDE_ENVELOPE.md) 3. szakaszában). A center a vizsgált domainen kívül is elhelyezhető.

## 5. Strength és forgásirány

A `strength` bármely véges valós érték lehet. Pozitív érték az egyik, negatív érték a másik körüljárási irányba forgatja a koordinátákat. `strength = 0` esetén a `SwirlDistortion` az identitás-transzformációval egyenértékű — ez érvényes konfiguráció.

## 6. Determinizmus

A `SwirlDistortion` tisztán parametrikus — nem igényel zajgenerátort vagy seedet. Azonos paraméterek esetén azonos, determinisztikus eredményt ad, összhangban a [WAVE_DOMAIN_MODEL.md](WAVE_DOMAIN_MODEL.md) 14. szakaszának determinizmus-elvével.

## 7. Hatókörön kívül

Nem része a 9.6-nak:

* Amplitude distortion (a hullám magasságát, nem a koordinátáit moduláló torzítás) — ez fogalmilag az `AmplitudeEnvelope` (9.2) jövőbeli bővítése, `BACKLOG.md` 3. tétel — **megvalósítva**: l. [AMPLITUDE_ENVELOPE.md](AMPLITUDE_ENVELOPE.md) 11. szakasz, `NoiseAmplitudeEnvelope` (ROADMAP Phase 10.5);
* ~~további `Distortion`-típusok (pl. sima, folytonos zajmező-alapú koordináta-warp, több lépték kombinálása) — `BACKLOG.md` 4. tétel~~ — **megvalósítva**: l. 9. szakasz, `NoiseDistortion` (ROADMAP Phase 10.6);
* több `Distortion` egymásra rétegzése ("Distortion Layer" stacking);
* GUI-implementáció (a paraméterek domain-szintű létezése a meglévő `MeshSourceDescriptor`/`ParameterSpec` mechanizmuson, ADR-0017, keresztül válik automatikusan szerkeszthetővé, ugyanúgy, mint a 9.4-nél).

## 8. Phase 8/9.1–9.5 backward compatibility

Ha egy `Wave`-nek nincs `Distortion` komponense (ez az alapértelmezett állapot), a viselkedés pontosan megegyezik a `Distortion` bevezetése előtti (Phase 8, illetve 9.1–9.5) viselkedéssel. Ez a 9.6 validációjának kötelező része.

## 9. NoiseDistortion (ROADMAP Phase 10.6)

A `Noise` distortion a Phase 10.4-ben bevezetett `GradientNoiseField`
primitívumot csomagolja be `Distortion`-ként — kizárólag
`GradientNoiseField`-et, NEM `VoronoiNoiseField`-et, mert a
koordináta-eltoláshoz előjeles (`[-1,1]`) érték szükséges, amit a
`VoronoiNoiseField` nem-negatív, távolság-jellegű `[0,1]` kimenete nem
ad közvetlenül.

Klasszikus "domain warping" technika: az X és Y koordinátát KÉT,
egymástól független zajmező (jellemzően azonos `scale`, de eltérő
`seed`/`seed+1`) mintáival tolja el:

```text
x' = x + strength · noise_x(x, y)
y' = y + strength · noise_y(x, y)
```

A `strength` bármely véges valós érték lehet — pontosan a
`SwirlDistortion.strength` mintájára (3–5. szakasz), `strength=0` az
identitás-transzformációval egyenértékű. Nincs invariáns, nincs hozzá
tartozó kivétel.

A "több lépték kombinálása" (`BACKLOG.md` 4. tétel másik fele) a
`GradientNoiseField` `octaves` paraméterén (PROCEDURAL_NOISE.md 2.3
szakasz) keresztül már elérhető — nem igényelt új logikát ehhez a
tételhez.

**Hatókörön kívül marad** (l. 7. szakasz is): a "Distortion Layer"
stacking (több `Distortion` egymásra rétegzése).
