# ADR-0020: Image Relief Generator — Raw Mesh mintavételezési konvenció és önálló GeometricSurfaceMeshGenerator

Dátum: 2026-09-03
Státusz: Elfogadva
Döntéshozó: Horváth Gyula Attila (projektgazda)

## Kontextus

A ROADMAP Phase 13.7 (Geometry → Raw Mesh) tervezése közben két, egymással összefüggő kérdés merült fel.

**Első kérdés — a `raw_relief` doménje korábban nem volt rögzítve.** A `GeometricSurface.raw_relief: (x,y) -> ReliefValue` kontraktus (Phase 13.6, `IMAGE_RELIEF_GEOMETRIC_SURFACE.md`) sosem mondta ki explicit, milyen `(x,y)` tartományt vár. Ez valódi ellentmondáshoz vezetett: a már implementált, Elfogadva `Mask.member(x,y)` (Phase 13.1–13.2) a kép abszolút, nem normalizált pixel-koordinátarendszerében értelmezett; ezzel szemben a tervezési dokumentum 15.2/17.7 szakasza explicit kimondja és a REJECTED listán rögzíti, hogy a Raw Mesh réteg (13.7) nem ismerheti a kép natív pixel-felbontását; a tervezési dokumentum 16.3 szakaszában bemutatott Orchestration-closure pedig egy egyszerű, változtatás nélküli `(x,y)` pass-through, ami nem oldja fel ezt az ellentmondást.

**Második kérdés — a Raw Mesh generátor kódjának viszonya a meglévő `MeshGenerator`-hoz.** A triangulációs séma és a vertex-indexelés szó szerint azonos a meglévő, `ReliefGeometry`-t mesh-é alakító `MeshGenerator`-éval (`MESH_GENERATION_MODEL.md` §36) — egyedül a Z-érték forrása tér el (`top_z` helyett `physical_z`).

## Döntés

**1. `raw_relief` doménje normalizált `[0,1] × [0,1]`**, a meglévő `HeightField.query(x,y) -> [0,1]` mintáját követve. A fizikai skálázás (`X = x·width`, `Y = y·height`) kizárólag a Raw Mesh réteg vertex-építésének felelőssége, nem a `GeometricSurface`-é.

Az Image Relief Generator esetében a normalizált `(x,y)` → kép abszolút pixel-koordináta (`px,py`) leképezés **az Orchestration (Phase 13.8) felelőssége**, a `raw_relief` closure belsejében elrejtve:

```text
Raw Mesh mintavételezés
        │  normalizált (x,y) ∈ [0,1]²
        ▼
GeometricSurface.raw_relief(x,y)
        │  Orchestration-szintű koordináta-leképezés (13.8)
        ▼
image-space (px,py)
        │
        ▼
Effect Processing / Mask.member(px,py)
```

Ezzel a 17.7 STABLE/REJECTED döntése (a Raw Mesh nem ismerheti a kép natív pixel-felbontását) változatlanul érvényben marad — a Raw Mesh réteg (13.7) semmilyen kép-specifikus információt nem kap és nem igényel.

**2. `GeometricSurfaceMeshGenerator`** (`plugins/relief_generator/mesh/geometric_surface_mesh_generator.py`) **teljesen önálló implementáció**, nem osztja meg a triangulációs/vertex-indexelési logikát a meglévő `MeshGenerator`-ral. Kizárólag a már geometria-független, kimeneti típusokat használja újra: `GeneratedMesh` és `MeshValidator`/`MeshValidationError`.

## Mérlegelt alternatívák

- **Fizikai mm domén `raw_relief`-hez** (a normalizált helyett) — elvetve: eltérne a bevált `HeightField`-mintától, és közvetetté, a fizikai `width`/`height`-től függővé tenné az Orchestration-mappinget anélkül, hogy ebből bármi nyerhető lenne.
- **A Raw Mesh réteg ismerje a kép pixel-felbontását** — elvetve: ellentmondana a már lezárt 17.7 STABLE/REJECTED döntéseknek, és feleslegesen kötné össze a Geometry World-öt az Image Relief Generator-specifikus Semantic World-részletekkel.
- **Közös triangulációs/vertex-indexelési segédfüggvények kiemelése a meglévő `MeshGenerator`-ral** — mérlegelve, elvetve: a jövőbeli "áttört" relief-testek (`BACKLOG.md` 1. tétele) valószínűleg pontosan ezen a ponton (topológia, perem) térnének el, egy korai megosztás a bizonytalan formájú jövőbeli igény miatt rossz irányba generalizálna; a jövőbeli Vector Relief Generator geometria-rétege bizonytalan formájú, esetleg nem is ide kapcsolódna.
- **Protocol-alapú egységesítés** (egy `top_z`-szerű, egységes `(x,y) -> Z` interfész mindkét generátor bemenetére) — elvetve: strukturálisan nem illeszkedik, mert a `physical_z` a `v_min`/`v_max`-tól függ, ami csak a teljes mintavételezési kör UTÁN áll elő (kétlépéses folyamat), míg a `top_z` önmagában elégséges, egylépéses függvény — ez a különbség a triangulációs döntéstől függetlenül is kizárja az egyszerű interfész-egységesítést.

## Következmények

- `docs/plugins/relief_generator/IMAGE_RELIEF_GEOMETRIC_SURFACE.md` (Phase 13.6, már Elfogadva) egy ponton kiegészül: a `raw_relief` doménje explicit rögzítve normalizált `[0,1]×[0,1]`-ként. Ez korábban egyszerűen nem volt rögzítve (nem felülbírálás) — a Sprint szabály szerint indokolt kiegészítés (ellentmondás feloldása + projektgazda kifejezett kérése).
- `docs/drafts/image_relief_generator/IMAGE_RELIEF_GENERATOR_PLANNING.md` 16.3 szakasza mellé egy jegyzet kerül, ami elavultnak jelöli a bemutatott, pass-through closure-t — a történeti szöveg maga változatlan marad.
- Az Orchestration (Phase 13.8, még nem tervezett) explicit felelősséget kap: a normalizált → kép-pixel-koordináta leképezés felépítése a `raw_relief` closure-ben.
- Új domain-contract dokumentum: `docs/plugins/relief_generator/IMAGE_RELIEF_RAW_MESH.md` (Phase 13.7).
- Új kód: `plugins/relief_generator/mesh/geometric_surface_mesh_generator.py` (`GeometricSurfaceMeshGenerator`), `GeometricSurfaceMeshGenerationError` kivétel.
- A meglévő `MeshGenerator`, `HeightField`, `ReliefGeometry` és mind az öt meglévő generátor-típus (Wave/Voronoi/Crater/Dune/WoodGrain) érintetlen — tisztán additív bővítés.
