# Slice Designer

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-07-30
Utolsó módosítás: 2026-08-29
Kapcsolódó dokumentumok: [docs/PROJECT_CONSTITUTION.md](docs/PROJECT_CONSTITUTION.md), [docs/ROADMAP.md](docs/ROADMAP.md), [docs/PROJECT_VISION.md](docs/PROJECT_VISION.md), [docs/USER_GUIDE.md](docs/USER_GUIDE.md), [docs/WORKFLOW.md](docs/WORKFLOW.md), [docs/RELEASE_NOTES.md](docs/RELEASE_NOTES.md), [docs/ENGINEERING_PRINCIPLES.md](docs/ENGINEERING_PRINCIPLES.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md), [docs/CODING_STANDARDS.md](docs/CODING_STANDARDS.md), [docs/AI_WORKFLOW.md](docs/AI_WORKFLOW.md), [docs/PROMPT_STANDARD.md](docs/PROMPT_STANDARD.md), [docs/DOMAIN_MODEL.md](docs/DOMAIN_MODEL.md), [docs/SPECIFICATION_STANDARD.md](docs/SPECIFICATION_STANDARD.md)

## Cél

A Slice Designer egy desktop alkalmazás, amely 3D modellekből (első körben STL) gyártásra előkészített, szeletelt alkatrészeket készít. A program nem CAD rendszer, hanem egy célzott, technológia-független gyártás-előkészítő eszköz.

## Jelenlegi állapot

A projekt mind a nyolc ROADMAP-fázisát (Phase 0–8) lezárta. A nyolc domain engine, a Project-réteg (pipeline-vezérlés, mentés/betöltés) és a teljes PySide6 GUI elkészült, automatizált teszttel lefedve; a felhasználói dokumentáció, a workflow-leírás, a release dokumentáció és a négy reprodukálható példaprojekt (`examples/`) a Phase 6-ban véglegesült; a Phase 7 a GUI-t kiegészítő funkciókkal (2D export-előnézet, "Példák megnyitása", true-shape Nesting, fülsávos paraméter-panel) bővült. A Phase 8 az első opcionális MeshSource plugint, a parametrikus Relief Generatort vezette be (`plugins/relief_generator/`) — a SliceDesigner core plugin nélkül is teljes értékű marad (ADR-0014, ADR-0015), a plugin discovery entry-point alapú (ADR-0017), valódi Qt GUI-integrációval (Forrás-választó, generikus paraméter-form, "Generálás" gomb) a "Mesh Import" fülön.

A Phase 9 (Wave Extension) a hullám-alapú Wave Generatort amplitúdó-modulációval (Envelope: Radial/Noise), koordináta-torzítással (Distortion: Swirl/Noise) és több, egyénileg paraméterezhető, egyidejű hullámforrással bővítette. A Phase 10 további hullámalakokat (Sinusoidal/Triangle/Sawtooth/Square), explicit hullámforrásonkénti szabálytalanságot/komplexitást, és egy megosztott, procedurális zajmező-primitívet (`GradientNoiseField`/`VoronoiNoiseField`) vezetett be. A Phase 11 erre a primitívre építve négy új, önálló procedurális Height Field receptet adott a Wave Generator mellé — Voronoi-felszín, Holdkráter-felszín, Dűne-felszín és Faerezet-felszín —, mindegyik egy közös `generator_type` GUI-választón keresztül, feltételesen megjelenő, csak a kiválasztott generátorra vonatkozó paraméter-csoportokkal (ADR-0017 kiegészítés, `ParameterSpec.visible_when`). A Relief Generator plugin ma öt generátor-típust kínál (`"Wave"`/`"Voronoi"`/`"Crater"`/`"Dune"`/`"WoodGrain"`).

A Phase 12 (folyamatban) a dokumentáció Phase 9–11 utáni frissítését, valamint két, korábban jövőbeli irányként jelzett `BACKLOG.md`-tétel megtervezését és megvalósítását célozza.

## Hogyan érdemes olvasni a dokumentációt

Javasolt sorrend első olvasásra:

1. `docs/PROJECT_CONSTITUTION.md` – a projekt legfelső szintű szabályrendszere
2. `docs/ROADMAP.md` – a fejlesztési fázisok sorrendje és jelenlegi állapota
3. `docs/USER_GUIDE.md` – hogyan telepítsd, indítsd és használd a kész alkalmazást
4. `docs/WORKFLOW.md` – milyen sorrendben és miért érdemes a funkciókat használni
5. `docs/RELEASE_NOTES.md` – verziószám, rendszerkövetelmények, ismert korlátozások és a fejlesztési előzmények
6. `docs/PROJECT_VISION.md` – mi a projekt célja, és mi nem tartozik bele
7. `docs/ENGINEERING_PRINCIPLES.md` – milyen alapelvek mentén készül a szoftver
8. `docs/ARCHITECTURE.md` – a tervezett rendszerfelépítés
9. `docs/PROJECT_STRUCTURE.md` – a könyvtárszerkezet és az egyes mappák szerepe
10. `docs/CODING_STANDARDS.md` – kódolási elvárások
11. `docs/AI_WORKFLOW.md` – hogyan zajlik a fejlesztés AI közreműködésével
12. `docs/PROMPT_STANDARD.md` – sablon jövőbeni implementációs feladatokhoz
13. `docs/DOMAIN_MODEL.md` – a projekt közös fogalomrendszere
14. `docs/SPECIFICATION_STANDARD.md` – sablon a funkcionális specifikációkhoz

A `docs/adr/` mappa a projekt architekturális döntéseit (ADR-0001–ADR-0017), a `docs/specifications/` pedig a nyolc engine részletes, jóváhagyott specifikációját tartalmazza. A `docs/plugins/` az opcionális pluginok (elsőként a Relief Generator, `docs/plugins/relief_generator/`) saját dokumentációját gyűjti; a hozzájuk tartozó forráskód a `plugins/` könyvtárban van, a `src/slicedesigner/` mellett (PROJECT_STRUCTURE.md 10–11. szakasz).

## Filozófia

A dokumentáció az elsődleges igazságforrás. A tervezés megelőzi az implementációt. A projekt letisztultságra és egyértelműségre törekszik, túlbonyolítás nélkül.
