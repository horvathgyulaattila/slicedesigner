# ADR-0018: Image Relief Generator — `GeometricSurface` kontraktus

Dátum: 2026-09-03
Státusz: Elfogadva
Döntéshozó: Horváth Gyula Attila (projektgazda)

## Kontextus

A Relief Representation (Phase 13.5) egy előjeles skalár `ReliefValue` függvényt (`(x,y) -> ReliefValue`) definiál, amelyben pozitív érték Raised, negatív Recessed irányú nettó hatást jelent. Ezt fizikai `Z`-koordinátává kell alakítani, mielőtt a Geometry → Raw Mesh lépés (Phase 13.7) mintavételezhetné.

A meglévő, öt generátor-típus (Wave/Voronoi/Crater/Dune/WoodGrain) közös rétege, a `HeightField`/`ReliefGeometry` (Phase 8–11, lezárva), `HeightField.query(x,y) -> [0,1]` — előjel nélküli, önmagában kész, `[0,1]`-re normalizált értéket ad, amit a `ReliefGeometry.top_z` egyetlen `base_thickness + H(x,y) * relief_height` képlettel fizikai magassággá alakít. Ez a kontraktus strukturálisan nem alkalmas az előjeles `ReliefValue` befogadására: egy `[0,1]`-re szoruló érték nem tudja kifejezni a Raised/Recessed független, kétirányú skálázását.

A Szoftverarchitekt ezt a Phase 13 megnyitásakor (folytatás 61) azonosította a legnagyobb architekturális eltérésként a meglévő öt generátor-típus egységes mintájától (l. `RELIEF_GENERATOR_DOMAIN.md` 29. szakasza: "új közös geometriai absztrakció") — innen az ADR.

## Döntés

Új, önálló, a meglévő `HeightField`/`ReliefGeometry` melletti, azzal párhuzamos kontraktus: `GeometricSurface`. Funkcionális, materializáció nélküli, két részre bomlik:

```text
raw_relief: (x,y) -> ReliefValue                # pass-through a Relief Representationből
physical_z(raw_value, v_min, v_max) -> Z        # tiszta, mintavételezés-mentes képlet
```

A `v_min`/`v_max` (a ténylegesen realizált `ReliefValue`-szélsőértékek) előállítása **nem** a `GeometricSurface` felelőssége — a Geometry → Raw Mesh lépés (Phase 13.7) tárgya.

**`Z`-leképezés — nullponthoz rögzített, kétirányú, egymástól független normalizálás:**

```text
V(p) := ReliefValue(p)
V_max := max(0, sup_p V(p))
V_min := min(0, inf_p V(p))

Z(p) :=
    base_thickness                                             ha V(p) = 0
    base_thickness + (V(p)/V_max) * relief_height_raised        ha V(p) > 0   (V_max > 0 ekkor garantált)
    base_thickness − (V(p)/V_min) * relief_height_recessed      ha V(p) < 0   (V_min < 0 ekkor garantált)
```

A semleges terület (`ReliefValue = 0`) emiatt mindig pontosan `base_thickness`-en ül, függetlenül attól, hogy a kép máshol milyen szélsőséges Raised/Recessed értékeket tartalmaz.

**Fizikai paraméterek** (mind Orchestration-szintű konfigurációból érkeznek, konzisztensen a meglévő `ReliefGeometry` mintázatával):

```text
GeometricSurface
├── width, height
├── base_thickness
├── relief_height_raised
├── relief_height_recessed
└── raw_relief: (x,y) -> ReliefValue
```

**Fail-fast validáció — a réteg egyetlen kötelező fizikai kényszere:**

```text
base_thickness − relief_height_recessed > 0     (szigorú)
```

Ez konstrukciókor, tisztán a paraméterekből eldönthető — nem a kép tartalmától függő, futásidejű ellenőrzés. Mellékhatásként implicit `base_thickness > 0`-t is kikényszerít.

## Mérlegelt alternatívák

- **Meglévő `HeightField`/`ReliefGeometry` közvetlen, változtatás nélküli újrafelhasználása** — elvetve: strukturálisan alkalmatlan az előjeles `ReliefValue` befogadására (fent).
- **Egyetlen globális min–max stretch** (a Raised és Recessed irány közös skálázása) — elvetve: a semleges terület (`ReliefValue = 0`) így nem maradna garantáltan pontosan `base_thickness`-en, ha a Raised/Recessed szélsőértékek aszimmetrikusak.
- **`relief_height_recessed` automatikus levezetése `base_thickness`-ből** — elvetve: a paraméter explicit, kötelező marad, mert a fail-fast kényszer csak a kettő együttes ismeretében értelmezhető.
- **Nyomtatási/gyártási magasságkorlát bevezetése ezen a rétegen** — elvetve: downstream (pl. Slicing/Nesting) réteg felelőssége.
- **A `ReliefGeometry` mintáját követő, teljes körű fail-fast validáció** (`width > 0`, `height > 0`, `relief_height_raised ≥ 0`, `relief_height_recessed ≥ 0`, a 14.6 kényszere mellett) — mérlegelve, projektgazda által explicit elvetve: a réteg tudatosan kizárólag a bizonyítottan szükséges, egyetlen kényszert érvényesíti; a Recessed irány szándékosan a `base_thickness` alá mehet, ez a réteg lényegi funkciója, nem hibaeset. Ha a jövőben konkrét hibaeset igazolja a szükségességét, ez külön döntés tárgya lesz.

## Következmények

- Új domain-contract dokumentum: `docs/plugins/relief_generator/IMAGE_RELIEF_GEOMETRIC_SURFACE.md`.
- Új kód: `plugins/relief_generator/domain/geometric_surface.py` (`GeometricSurface`), `GeometricSurfaceValueError` kivétel.
- A meglévő `HeightField`/`ReliefGeometry` és mind az öt meglévő generátor-típus (Wave/Voronoi/Crater/Dune/WoodGrain) érintetlen — tisztán additív bővítés.
- Nyitva marad: `width`/`height`/`relief_height_raised`/`relief_height_recessed` értékkészlete ezen a rétegen nincs korlátozva.
- `v_min`/`v_max` előállítása (Phase 13.7) és a footprint/mask kérdés (`BACKLOG.md` 1. tétele) továbbra is más réteg/jövőbeli döntés felelőssége.
