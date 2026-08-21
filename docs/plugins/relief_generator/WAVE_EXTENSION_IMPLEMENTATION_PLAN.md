# WAVE_EXTENSION_IMPLEMENTATION_PLAN.md

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-20
Utolsó módosítás: 2026-08-20
Kapcsolódó dokumentumok: [PROJECT_CONSTITUTION.md](../../PROJECT_CONSTITUTION.md), [WAVE_DOMAIN_MODEL.md](WAVE_DOMAIN_MODEL.md), [AMPLITUDE_ENVELOPE.md](AMPLITUDE_ENVELOPE.md), [RADIAL_WAVE_SOURCE.md](RADIAL_WAVE_SOURCE.md), [WAVE_WEIGHTING.md](WAVE_WEIGHTING.md), [MULTIPLE_WAVE_SOURCES.md](MULTIPLE_WAVE_SOURCES.md), [PROCEDURAL_DISTORTION.md](PROCEDURAL_DISTORTION.md), [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)

## 1. Cél

A dokumentum célja a ROADMAP Phase 9 (Wave Extension) hat, már Elfogadva státuszú
domain-contractjának (9.1–9.6) végrehajtható implementációs tervvé alakítása, a Phase 9
7. tétele (9.7 — Integration, validation, documentation) hatókörének megfelelően.

A 9.7-nek — a többi alfázistól eltérően — nincs önálló domain-contract dokumentuma, mivel
nem vezet be új domain fogalmat: tisztán implementációs és validációs feladat, a Phase 8
[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)-jának mintájára (ROADMAP.md, 2026-08-19,
folytatás 30).

A jelen dokumentum kizárólag a már elfogadott hat domain-contractból indul ki. Nem vezet
be új architekturális döntést, és nem módosítja azok tartalmát.

## 2. Hatókör

A jelen terv kizárólag:

* a 9.1–9.6 domain-contract Python-implementációjának sorrendjét;
* az alfázisonkénti automatizált tesztelési stratégiát;
* a Phase 8 `WaveGenerator` elleni backward compatibility teszt stratégiáját;
* az end-to-end integrációs teszt stratégiáját;
* az élő tesztelés menetét

határozza meg.

Nem cél a jelen tervben:

* a `docs/BACKLOG.md` 1–4. tételei (alternatív `WaveFunction`-ök, önálló Height Field
  generátor-típusok, Amplitude distortion, további `Distortion`-típusok);
* GUI-implementáció — a paraméterek a meglévő `MeshSourceDescriptor`/`ParameterSpec`
  mechanizmuson (ADR-0017) keresztül válnak szerkeszthetővé, ugyanúgy, mint a Phase
  8-nál;
* preset-rendszer;
* teljesítmény-optimalizáció.

## 3. Implementációs sorrend

A hat domain-contract közötti függőségek:

```text
9.1 (Wave / WaveSet alapmodell)
 │
 ├── 9.2 (AmplitudeEnvelope: Radial + Falloff)      — független 9.3-tól, 9.4-től, 9.5-től, 9.6-tól
 ├── 9.3 (PropagationModel: Radial)                  — 9.4 előfeltétele
 │     └── 9.5 (weight szemantika, WaveSet összegzés) — 9.4 előtt, mert a WaveSourceSpec weight mezőt tartalmaz
 │           └── 9.4 (WaveSourceSpec explicit forráslista) — 9.1 ÉS 9.3 szükséges (MULTIPLE_WAVE_SOURCES.md 4. szakasz)
 └── 9.6 (Distortion: SwirlDistortion)               — önálló, opcionális, a többitől független
```

A végrehajtás sorrendje:

### 1. Wave model extension (9.1)

A `Wave`/`WaveSet` komponensalapú modell, a `WaveFunction`/`PropagationModel`/
`AmplitudeEnvelope` absztrakció bevezetése, Phase 8-kompatibilis konkrét megvalósítással
(Sinusoidal, Directional, Uniform). Ld. [WAVE_DOMAIN_MODEL.md](WAVE_DOMAIN_MODEL.md).

### 2. Spatial amplitude envelope (9.2)

`RadialAmplitudeEnvelope`, Linear/Smooth/Gaussian falloff. Ld.
[AMPLITUDE_ENVELOPE.md](AMPLITUDE_ENVELOPE.md).

### 3. Radial wave source (9.3)

`RadialPropagation`. Ld. [RADIAL_WAVE_SOURCE.md](RADIAL_WAVE_SOURCE.md).

### 4. Wave combination / weighting (9.5)

A `weight` szemantika (nulla, negatív érték) és a `WaveSet` súlyozott összegzésének
részletes lefedése. Ld. [WAVE_WEIGHTING.md](WAVE_WEIGHTING.md).

### 5. Multiple wave sources (9.4)

`WaveSourceSpec`, a kettős mechanizmus (automatikus generálás + explicit forráslista)
összefűzése. Ld. [MULTIPLE_WAVE_SOURCES.md](MULTIPLE_WAVE_SOURCES.md).

### 6. Controlled procedural distortion (9.6)

`SwirlDistortion`, mint önálló, opcionális, per-`Wave` komponens. Ld.
[PROCEDURAL_DISTORTION.md](PROCEDURAL_DISTORTION.md).

Minden lépés lezárásaként a teljes automatizált tesztkészlet és a `ruff format`/
`ruff check`/`mypy` regresszió nélkül kell, hogy lefusson, mielőtt a következő lépés
elkezdődik.

## 4. Tesztelési stratégia alfázisonként

Az implementációt a meglévő `tests/plugins/relief_generator/` konvenció szerint kell
tesztelni (l. `tests/plugins/relief_generator/generators/test_wave_generator.py`:
determinizmus-teszt, `sys.path`-kezelés a PEP 420 namespace package miatt).

### Wave model extension (9.1)

Tesztelendő: a komponensalapú `Wave` felépítése; `amplitude`/`wavelength` invariáns
(`> 0`); `WaveSet` legalább egy komponenst tartalmaz; normalizálás (`N(F)`); degenerált
normalizálás (`F_max = F_min` ⇒ `N(F) = 0`); determinizmus ismételt hívások között;
backward compatibility teszt a Phase 8 `WaveGenerator` ellenében (l. 5. szakasz).

### Spatial amplitude envelope (9.2)

Tesztelendő: Linear/Smooth/Gaussian falloff a saját képlete szerint; Linear/Smooth
`d > R` esetén `M = 0`; Gaussian `d > R` esetén `M > 0` (nincs clamp); Gaussian `k > 0`
invariáns; `k → 0+` közelítőleg Uniform viselkedés.

### Radial wave source (9.3)

Tesztelendő: `P(x,y) = √((x−x_s)² + (y−y_s)²)`; `x=x_s, y=y_s` esetén `P=0`, nincs
szingularitás.

### Wave combination / weighting (9.5)

Tesztelendő: `weight = 0` ⇒ a komponens nem járul hozzá az összeghez, de a `Wave`
érvényes marad a gyűjteményben; negatív `weight` ⇒ előjelváltás; a `weight` a
normalizálás *előtt* érvényesül.

### Multiple wave sources (9.4)

Tesztelendő: `WaveSourceSpec` (`Directional`/`Radial`) érvényesítése a típusnak
megfelelő `PropagationModel` szabályai szerint; a végső `WaveSet` az automatikus
(előbb) és az explicit (utána) komponensek determinisztikus összefűzése; üres
explicit lista ⇒ Phase 8/9.1-identikus viselkedés; két azonos centerű `Radial`
forrás érvényes konfiguráció.

### Controlled procedural distortion (9.6)

Tesztelendő: `α(d) = strength · e^(−(d/radius)²)`; `strength = 0` ⇒ identitás-
transzformáció; `radius > 0` invariáns; nincs `Distortion` ⇒ pontosan a Phase
8/9.1–9.5 viselkedés.

## 5. Backward compatibility teszt

A [WAVE_DOMAIN_MODEL.md](WAVE_DOMAIN_MODEL.md) 15. szakasza szerint kötelező: azonos
bemenetek mellett (`WaveFunction = Sinusoidal`, `Propagation = Directional`,
`Envelope = Uniform`, `weight = 1`) `H_9.1(x,y) = H_Phase8(x,y)`.

A teszt a 9.1 implementációjának részeként íródik meg — a lehető legkorábban —, majd a
9.7 zárásaként újrafuttatásra kerül, hogy a közbenső alfázisok (9.2–9.6) egyike se
okozzon regressziót.

## 6. End-to-end integrációs teszt

A teljes downstream pipeline ellenőrzése egy kevert Phase 9-konfigurációval:

```text
WaveParameters + WaveSourceSpec lista (Radial + Directional)
      ↓
WaveGenerator (Wave/WaveSet, envelope, distortion)
      ↓
HeightField
      ↓
ReliefGeometry
      ↓
MeshGenerator
      ↓
Mesh
      ↓
MeshSource
      ↓
SliceDesigner Slice Engine
```

A teszt célja annak bizonyítása, hogy a Phase 9 bővítés nem igényel változtatást a
downstream pipeline-ban — ugyanúgy, ahogyan azt a Phase 8
[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) 20. szakasza már a Phase 8 Wave
Generatorra igazolta.

## 7. Élő tesztelés

Az automatizált tesztkészlet és a `ruff`/`mypy` teljes, regresszió nélküli zöld
állapota után, a Phase 8 mintáját követve, a projektgazdával élő tesztelés zárja a
Phase 9-et.

## 8. Hatókörön kívüli, később felmerülő tételek

* `docs/BACKLOG.md` 1. tétel — alternatív `WaveFunction`-ök;
* `docs/BACKLOG.md` 2. tétel — Wave Generatortól független Height Field
  generátor-típusok;
* `docs/BACKLOG.md` 3. tétel — Amplitude distortion mint `AmplitudeEnvelope`-bővítés;
* `docs/BACKLOG.md` 4. tétel — további `Distortion`-típusok.

Ezek nem módosítják a jelen terv hatókörét.

## 9. Dokumentációs függőségek

```text
WAVE_DOMAIN_MODEL.md (9.1)
       ↓
AMPLITUDE_ENVELOPE.md (9.2)
       ↓
RADIAL_WAVE_SOURCE.md (9.3)
       ↓
WAVE_WEIGHTING.md (9.5)
       ↓
MULTIPLE_WAVE_SOURCES.md (9.4)
       ↓
PROCEDURAL_DISTORTION.md (9.6)
       ↓
WAVE_EXTENSION_IMPLEMENTATION_PLAN.md
```

## 10. Státusz

**Elfogadva.**

A dokumentum nem tartalmaz új architekturális döntést; a hat, már Elfogadva
domain-contractból vezeti le a végrehajtás sorrendjét és a tesztelési stratégiát, a
Phase 8 [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) mintáját követve.
