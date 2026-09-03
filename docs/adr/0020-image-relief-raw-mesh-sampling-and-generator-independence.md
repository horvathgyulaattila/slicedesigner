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

## Kiegészítés (2026-09-03): a `raw_relief` closure pixel-mapping képlete

A ROADMAP Phase 13.8 (Orchestration) lezárta a jelen ADR által nyitva hagyott
kérdést — a normalizált `(x_norm, y_norm) ∈ [0,1]²` → kép abszolút
pixel-koordináta `(px, py)` leképezés pontos képletét:

```text
px = x_norm * (image_width - 1)
py = y_norm * (image_height - 1)
```

**Szemantika.** A Raw Mesh normalizált mintapontjai a kép diszkrét
pixel-rácsának **határpontjaihoz** vannak leképezve: `x_norm = 0` az első
pixelre, `x_norm = 1` az utolsó pixelre esik, közte lineárisan — nem egy
folytonos `[0, image_width)` cella-tartomány mintájára (ami `x_norm = 1`-nél
`px = image_width`-et adna, egy érvénytelen indexet, clamp-et igényelve).

**Indoklás:**

1. **Konzisztencia a Raw Mesh saját rács-konvenciójával.** A Raw Mesh már a
   fizikai vertex-koordinátákra is pontosan ezt az elvet alkalmazza
   (`IMAGE_RELIEF_RAW_MESH.md` 3. szakasz: `X_i = x_norm · width`,
   `x_norm = 0` a panel bal szélét, `x_norm = 1` a jobb szélét jelenti) — a
   kép diszkrét pixel-rácsát ugyanezen elv szerint kezelve nincs kétféle
   rács-szemantika a rendszerben.
2. **Nincs szegély-kivétel.** A képlet minden `x_norm ∈ [0,1]`-re érvényes,
   `[0, image_width−1]`-en belüli eredményt ad — nincs szükség clamp-re vagy
   külön kezelt szegély-esetre a pontos `x_norm = 1.0` határon.
3. **Degenerált eset (1 pixel széles/magas kép) helyesen viselkedik.**
   `image_width − 1 = 0` esetén `px = 0` minden `x_norm`-ra — szorzás, nem
   osztás, nullával osztás nélkül.
4. **A `Mask` Protocol réteghatára megmarad.** Az Orchestration folytonos
   `px`/`py` értéket ad át a `relief_representation`/`combine`-nak — nem
   kerekít vagy csonkol maga. Az egész-pixel értelmezés
   (`PixelSetMask.member`: `(int(x), int(y)) in pixels`) továbbra is
   Image Interpretation belső, backend-specifikus döntés marad (l.
   `region.py`, `Mask` Protocol docstring).

Ez a jelen ADR "Döntés" 1. pontjának ("Az Image Relief Generator esetében a
normalizált `(x,y)` → kép abszolút pixel-koordináta leképezés az
Orchestration felelőssége") közvetlen konkretizálása, nem felülbírálása —
ezért kiegészítés, nem új ADR (a `list`/`group`/`visible_when` ADR-0017
kiegészítés-precedens mintáját követve).

### Következmények

- `plugins/relief_generator/source/image_relief_generator_mesh_source.py`
  (`ImageReliefGeneratorMeshSource`, Phase 13.8) a fenti képletet
  implementálja a `raw_relief` closure-ben.
- `docs/plugins/relief_generator/IMAGE_RELIEF_ORCHESTRATION.md` (Phase 13.8,
  új dokumentum) a végleges closure-kódot és ezt az indoklást tartalmazza.
- A Raw Mesh réteg (13.7, Elfogadva) és a `GeometricSurface` (13.6,
  Elfogadva) kontraktusa változatlan — a képlet kizárólag az Orchestration
  belső implementációja.
