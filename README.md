# Slice Designer

Státusz: Piszkozat
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-07-30
Utolsó módosítás: 2026-08-01
Kapcsolódó dokumentumok: [docs/PROJECT_CONSTITUTION.md](docs/PROJECT_CONSTITUTION.md), [docs/ROADMAP.md](docs/ROADMAP.md), [docs/PROJECT_VISION.md](docs/PROJECT_VISION.md), [docs/ENGINEERING_PRINCIPLES.md](docs/ENGINEERING_PRINCIPLES.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/AI_WORKFLOW.md](docs/AI_WORKFLOW.md), [docs/DOMAIN_MODEL.md](docs/DOMAIN_MODEL.md)

## Cél

A Slice Designer egy desktop alkalmazás, amely 3D modellekből (első körben STL) CNC-re előkészített szeletelt alkatrészeket készít. A program nem CAD rendszer, hanem egy célzott gyártás-előkészítő eszköz.

## Jelenlegi állapot

A projekt jelenleg a kezdeti fázisban van: a könyvtárszerkezet és a dokumentációs keretrendszer jött létre. Alkalmazáskód és geometriai algoritmusok még nem készültek.

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

A `docs/adr/` mappa a jövőbeni architekturális döntéseket, a `docs/specifications/` a részletes specifikációkat, a `docs/prompts/` pedig a konkrét implementációs promptokat fogja tartalmazni.

## Filozófia

A dokumentáció az elsődleges igazságforrás. A tervezés megelőzi az implementációt. A projekt letisztultságra és egyértelműségre törekszik, túlbonyolítás nélkül.
