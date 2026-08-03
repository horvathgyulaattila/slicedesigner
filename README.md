# Slice Designer

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-07-30
Utolsó módosítás: 2026-08-03
Kapcsolódó dokumentumok: [docs/PROJECT_CONSTITUTION.md](docs/PROJECT_CONSTITUTION.md), [docs/ROADMAP.md](docs/ROADMAP.md), [docs/PROJECT_VISION.md](docs/PROJECT_VISION.md), [docs/ENGINEERING_PRINCIPLES.md](docs/ENGINEERING_PRINCIPLES.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md), [docs/CODING_STANDARDS.md](docs/CODING_STANDARDS.md), [docs/AI_WORKFLOW.md](docs/AI_WORKFLOW.md), [docs/PROMPT_STANDARD.md](docs/PROMPT_STANDARD.md), [docs/DOMAIN_MODEL.md](docs/DOMAIN_MODEL.md), [docs/SPECIFICATION_STANDARD.md](docs/SPECIFICATION_STANDARD.md)

## Cél

A Slice Designer egy desktop alkalmazás, amely 3D modellekből (első körben STL) gyártásra előkészített, szeletelt alkatrészeket készít. A program nem CAD rendszer, hanem egy célzott, technológia-független gyártás-előkészítő eszköz.

## Jelenlegi állapot

A projekt a Phase 4 (Implementation) lezárásánál tart: mind a nyolc domain engine (Mesh Import, Slice Engine, Dowel System, Gap System, Backplate, Numbering, Nesting, DXF Export) elkészült, és automatizált teszttel (89 teszt) le van fedve. A következő fázis (Phase 5, Integration) a modulok `Project`-en keresztüli összekapcsolása és a GUI.

## Hogyan érdemes olvasni a dokumentációt

Javasolt sorrend első olvasásra:

1. `docs/PROJECT_CONSTITUTION.md` – a projekt legfelső szintű szabályrendszere
2. `docs/ROADMAP.md` – a fejlesztési fázisok sorrendje és jelenlegi állapota
3. `docs/PROJECT_VISION.md` – mi a projekt célja, és mi nem tartozik bele
4. `docs/ENGINEERING_PRINCIPLES.md` – milyen alapelvek mentén készül a szoftver
5. `docs/ARCHITECTURE.md` – a tervezett rendszerfelépítés
6. `docs/PROJECT_STRUCTURE.md` – a könyvtárszerkezet és az egyes mappák szerepe
7. `docs/CODING_STANDARDS.md` – kódolási elvárások
8. `docs/AI_WORKFLOW.md` – hogyan zajlik a fejlesztés AI közreműködésével
9. `docs/PROMPT_STANDARD.md` – sablon jövőbeni implementációs feladatokhoz
10. `docs/DOMAIN_MODEL.md` – a projekt közös fogalomrendszere
11. `docs/SPECIFICATION_STANDARD.md` – sablon a funkcionális specifikációkhoz

A `docs/adr/` mappa a projekt architekturális döntéseit (ADR-0001–ADR-0008), a `docs/specifications/` pedig a nyolc engine részletes, jóváhagyott specifikációját tartalmazza.

## Filozófia

A dokumentáció az elsődleges igazságforrás. A tervezés megelőzi az implementációt. A projekt letisztultságra és egyértelműségre törekszik, túlbonyolítás nélkül.
