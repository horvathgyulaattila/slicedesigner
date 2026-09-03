# Image Relief Generator — Geometric Surface

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-09-03
Kapcsolódó dokumentumok: [IMAGE_RELIEF_RELIEF_REPRESENTATION.md](IMAGE_RELIEF_RELIEF_REPRESENTATION.md), [ADR-0018](../adr/0018-image-relief-geometric-surface-contract.md), [ADR-0020](../adr/0020-image-relief-raw-mesh-sampling-and-generator-independence.md), tervezési előzmény: `docs/drafts/image_relief_generator/IMAGE_RELIEF_GENERATOR_PLANNING.md` (14. szakasz, 17.6 tervezési lépés)

## Cél

Ez a dokumentum rögzíti a Geometric Surface kontraktusát — a Relief Representation fizikai geometriává alakítását — a ROADMAP Phase 13.6 alfázis kimenete.

## 1. Kontextus és hatókör

```text
Relief Representation (Phase 13.5)
  ↓
Geometric Surface   ← ez a dokumentum
  ↓
Raw Mesh (Phase 13.7)
```

Nem tárgya: a `v_min`/`v_max` előállítása (Phase 13.7), a mintavételezés/sampling, a topológia, a watertightness.

## 2. Definíció és felelősség

A Geometric Surface egyetlen felelőssége a Relief Representation (előjeles `ReliefValue`) fizikai geometriává alakítása: fizikai `Z`-koordinátát rendel minden ponthoz, amit a Geometry → Raw Mesh lépés mesh-építéshez felhasználhat.

## 3. Kontraktus — funkcionális forma, materializáció nélkül

Analóg a Relief Representation (13.5) és a meglévő `HeightField`/`ReliefGeometry` mintázatával:

```text
raw_relief: (x,y) -> ReliefValue                # pass-through a Relief Representationből
physical_z(raw_value, v_min, v_max) -> Z        # tiszta, mintavételezés-mentes képlet
```

A `v_min`/`v_max` (a ténylegesen realizált `ReliefValue`-szélsőértékek) előállítása **nem** a Geometric Surface felelőssége — a Geometry → Raw Mesh lépés (Phase 13.7) tárgya.

**Domén (2026-09-03, `ADR-0020` kiegészítés):** a `raw_relief` normalizált `[0,1] × [0,1]` tartományon értelmezett, a meglévő `HeightField.query(x,y) -> [0,1]` mintáját követve — nem fizikai mm-ben, és nem a kép pixel-koordinátáiban. A fizikai skálázás (`X = x·width`, `Y = y·height`) a Raw Mesh réteg (Phase 13.7) vertex-építésének felelőssége. Az Image Relief Generator esetében a normalizált koordináták kép-pixel-koordinátákra való leképezése az Orchestration (Phase 13.8) felelőssége, a `raw_relief` closure belsejében — ez korábban, e kiegészítés előtt, nem volt explicit rögzítve.

## 4. Fizikai paraméterek

```text
GeometricSurface
├── width, height             # fizikai XY kiterjedés
├── base_thickness             # a relief "nulla" síkja
├── relief_height_raised       # Raised irány terjedelme
├── relief_height_recessed     # Recessed irány terjedelme
└── raw_relief: (x,y) -> ReliefValue
```

Mind az öt skalár paraméter Orchestration-szintű konfigurációból érkezik, konzisztensen a meglévő `ReliefGeometry` mintázatával.

## 5. `ReliefValue` → fizikai `Z` — nullponthoz rögzített, kétirányú leképezés

```text
V(p) := ReliefValue(p)
V_max := max(0, sup_p V(p))
V_min := min(0, inf_p V(p))

Z(p) :=
    base_thickness                                             ha V(p) = 0
    base_thickness + (V(p)/V_max) * relief_height_raised        ha V(p) > 0   (V_max > 0 ekkor garantált)
    base_thickness − (V(p)/V_min) * relief_height_recessed      ha V(p) < 0   (V_min < 0 ekkor garantált)
```

A semleges terület (`ReliefValue = 0` — pl. a `combine(∅) := 0` peremfeltétel szerinti maszkolatlan háttér) emiatt mindig pontosan `base_thickness`-en ül, függetlenül attól, hogy a kép máshol milyen szélsőséges Raised/Recessed értékeket tartalmaz — a felfelé és lefelé irányuló skálázás egymástól függetlenül normalizált, nem egyetlen közös, globális stretch.

## 6. Fail-fast validáció — a réteg egyetlen kötelező fizikai kényszere

```text
base_thickness − relief_height_recessed > 0     (szigorú)
```

Ez konstrukciókor, tisztán a paraméterekből eldönthető — nem futásidejű, nem a kép tartalmától függő ellenőrzés. Mellékhatásként implicit `base_thickness > 0`-t is kikényszerít.

**A réteg tudatosan kizárólag ezt az egy kényszert érvényesíti.** Nincs explicit `width`/`height`/`relief_height_raised`/`relief_height_recessed` nem-negativitási vagy pozitivitási ellenőrzés ezen felül — projektgazdai döntés (l. `ADR-0018` "Mérlegelt alternatívák"). A Recessed irány szándékosan a `base_thickness` alá mehet; ez a réteg lényegi funkciója, nem hibaeset.

## 7. Viszony a meglévő Geometry World-höz

A meglévő, implementált `HeightField`/`ReliefGeometry` kontraktus (Phase 8–11, lezárva) változatlan marad. Az Image Relief Generator Geometric Surface-e egy azzal párhuzamos, hasonló szerepű, de eltérő alakú, önálló kontraktus, nem a meglévő típusok újrafelhasználása vagy kiterjesztése. Az eltérés oka: a meglévő `HeightField.query(x,y) -> [0,1]` előjel nélküli, önmagában kész értéket ad, míg a Relief Representation (13.5) tudatosan **előjeles** `ReliefValue`-t definiált — ez a két kontraktus strukturálisan nem azonos.

## 8. Réteghatár — mit NEM dönt el ez a dokumentum

- Az eredeti EffectSpec-eket és a Region-hierarchiát.
- A `combine` belső algoritmusát.
- A Mask konkrét reprezentációját.
- A `v_min`/`v_max` előállítását (Phase 13.7).
- A Footprint/mask kérdést (`BACKLOG.md` 1. tétele) — tudatosan nyitva marad ezen a rétegen is.

## 9. Státusz

**Elfogadva.**
