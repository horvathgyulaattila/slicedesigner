# Image Relief Generator — Effect Processing

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-09-02
Kapcsolódó dokumentumok: [IMAGE_RELIEF_REGION_RESOLUTION.md](IMAGE_RELIEF_REGION_RESOLUTION.md), tervezési előzmény: `docs/drafts/image_relief_generator/IMAGE_RELIEF_GENERATOR_PLANNING.md` (9–10., 12. szakasz, 17.4 tervezési lépés)

## Cél

Ez a dokumentum rögzíti a `combine` algoritmust — az EffectSpec[] egyetlen `ReliefValue`-vá (itt: `float`) történő kombinálását egy adott ponton — a ROADMAP Phase 13.4 alfázis kimenete. Ezzel lezárul a Semantic World réteg.

## 1. Kontextus és hatókör

```text
Image
  ↓
Image Interpretation
  ↓
Region hierarchy
  ↓
Region Resolver
  ↓
EffectSpec[]
  ↓
Effect Processing (`combine`)   ← ez a dokumentum
  ↓
Relief Representation (Phase 13.5)
```

Nem tárgya: a Relief Representation formális kontraktusa (Phase 13.5), a Falloff (opcionális, réteg-utáni transzformáció, csak jövőbeli igazolt igény esetén), a Geometry World fogalmai.

## 2. A `combine` függvény

```text
active(p)  := { s ∈ EffectSpec[] : s.Mask.member(p) }
S'(p)      := { s ∈ active(p) : nincs s-nek active(p)-ben lévő leszármazottja (ParentRef-lánc mentén) }

combine(p) :=
    0                        ha S'(p) = ∅
    elevation(az egy tag)    ha |S'(p)| = 1
    envelope(S'(p))          ha egyetlen irányban (nincs valódi pos/neg konfliktus S'(p)-ben)
    tiebreak(S'(p))          ha valódi, nem-rokon, ellentétes irányú ütközés
```

## 3. `S'` szűrő — lineage-menti occlusion

Az `S'` szűrő ("nincs aktív leszármazottja") **automatikusan** megoldja a lineage-menti occlusiont (ADR-0019) — nincs rá külön, irány-feltételes lépés: mivel az `elevation` már additívan felhalmozott (l. `IMAGE_RELIEF_REGION_RESOLUTION.md`), egy leszármazott elevation-je már tartalmazza az ős hatását, ezért az ős kizárása a `combine` bemenetéből nem veszít információt.

## 4. `envelope` — azonos irányú, nem-rokon átfedés

```text
envelope(specs) := elevation(s), ahol s az a tag, amelyre |elevation(s)| maximális
```

Az összeadás (nettósítás) helyett — az összeadás mesterséges "lépcső"-artefaktumot hozna létre nem-rokon, testvér/cross-branch átfedésnél. Egyenlő `|elevation|` esetén a bemeneti sorrend (a Region Resolver preorder bejárásából származó, stabil sorrend) dönt determinisztikusan az első előfordulás javára.

## 5. `tiebreak` — a maradék eset

Miután a lineage-menti occlusion (`S'` szűrő) és az azonos irányú, nem-rokon átfedés (`envelope`) kezelve van, egyetlen eset marad: `S'(p)`-ben legalább egy pozitív és legalább egy negatív `elevation`-ű, egymással nem rokon tag van egyszerre aktív.

```text
tiebreak(S'(p)):
    pos := { s ∈ S'(p) : elevation(s) > 0 }
    neg := { s ∈ S'(p) : elevation(s) < 0 }
    ha pos = ∅ vagy neg = ∅:
        combine(p) := envelope(S'(p))     # nem valódi ütközés (a nulla-elevationű tagok itt is részt vesznek)
    különben:
        érintettek := pos ∪ neg
        ha ∃! s ∈ érintettek, s.TieBreakPriority definiált és egyértelműen maximális:
            combine(p) := elevation(s)
        különben:
            KONFLIKTUS — l. 6.1
```

**Nincs hallgatólagos alapérték** (sem nettósítás, sem magnitúdó-dominancia) erre az esetre.

## 6. Implementációs döntések

*(a tervezési dokumentum ezeket explicit "implementációs kérdésnek, nem architekturális döntésnek" jelöli, analóg a Mask konkrét reprezentációjával)*

### 6.1 A konfliktus jelzésének mechanizmusa

A `combine()` a konkrét ponton, ahol a konfliktus fennáll, `EffectProcessingConflictError`-t dob — fail-fast, nincs hallgatólagos fallback.

### 6.2 Azonos, maximális `TieBreakPriority` — is konfliktus

Ha két vagy több, ellentétes irányú, érintett tag rendelkezik azonos, a többiek között maximális `TieBreakPriority`-val, nincs egyértelmű győztes — ezt is `EffectProcessingConflictError` jelzi. A tervezési dokumentum ezt az esetet nem definiálja explicit; ez a Szoftverarchitekt kiegészítése, a "nincs hallgatólagos alapérték" elv következetes alkalmazásaként.

## 7. Kötelező tulajdonságok

- **Determinisztikusság a bemeneti *halmazra* nézve**: a `combine(p)` kimenete kizárólag az `active(p)` halmaztól és a statikus `ParentRef`/`TieBreakPriority` struktúrától függ.
- **Monotonitás azonos irányú átfedésre**: ha `S'(p)`-ben minden nem-nulla tag azonos irányú, a kombinált hatás sosem kisebb, mint bármelyik önálló tag `|elevation|`-je — triviálisan teljesül, mivel az `envelope` maga a legnagyobb magnitúdójú tag értéke.

## 8. Réteghatár — mit NEM dönt el ez a dokumentum

- A Relief Representation formális kontraktusa ("pont → ReliefValue" függvény-típus névvel, tulajdonságokkal) — Phase 13.5.
- A Falloff/simítás — opcionális, csak jövőbeli igazolt igény esetén, a `combine` kimenetén végzett, utólagos transzformációként.
- Geometry World fogalmai.

## 9. Visszafelé kompatibilitás

Tisztán additív — új, plugin-belső modul. A meglévő öt generátor-típus és a core érintetlen.

## 10. Státusz

**Elfogadva.**
