# Roadmap

Státusz: Aktív
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-07-31
Utolsó módosítás: 2026-08-04
Kapcsolódó dokumentumok: [PROJECT_CONSTITUTION.md](PROJECT_CONSTITUTION.md), [AI_WORKFLOW.md](AI_WORKFLOW.md), [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md), [DOMAIN_MODEL.md](DOMAIN_MODEL.md)

## Cél

Ez a dokumentum meghatározza a Slice Designer fejlesztési fázisainak sorrendjét, célját és jelenlegi állapotát.

## Leírás

A ROADMAP nem backlog, nem feladatlista és nem specifikáció. A célja, hogy bármelyik AI vagy új fejlesztő azonnal lássa, hol tart a projekt, mely fázisok készültek el, mi a következő lépés, és mely dokumentumok tekinthetők lezártnak. A ROADMAP kizárólag a fejlesztési folyamatot írja le, technikai megoldásokat nem.

> **Megjegyzés (2026-08-01):** A Phase 0 korábbi ✅ Approved jelölése tévesen került rögzítésre — a kilépési feltétel ("A projekt dokumentációja önmagában értelmezhető") ténylegesen nem teljesült, mivel több Phase 0-hoz tartozó dokumentum vázlat állapotban maradt. A Phase 0 ezért 🟡 In Progress-re, a rá épülő Phase 1 pedig ⬜ Not Started-ra lett visszaminősítve.
>
> **Megjegyzés (2026-08-01, folytatás):** A Phase 0-hoz tartozó mind a hét dokumentum (PROJECT_VISION, ENGINEERING_PRINCIPLES, ARCHITECTURE, PROJECT_STRUCTURE, CODING_STANDARDS, AI_WORKFLOW, PROMPT_STANDARD) érdemi tartalommal elkészült és a projektgazda jóváhagyta — a kilépési feltétel teljesült. A Phase 0 ezért ✅ Approved-ra, a Phase 1 pedig 🟡 In Progress-re került, mivel a DOMAIN_MODEL.md már tartalmaz érdemi munkát (a Numbering-kivétel révén).
>
> **Megjegyzés (2026-08-01, folytatás 2):** A Phase 1 (Domain Design) kilépési feltétele teljesült — a DOMAIN_MODEL.md tartalmazza a koordinátarendszert, a mértékegységeket, valamint mind a 14 fogalom attribútum-szintű kiegészítését; a projektgazda a Claude Code általi végrehajtás után review-olta és jóváhagyta. A Phase 1 ezért ✅ Approved-ra, a Phase 2 (Functional Specifications) pedig 🟡 In Progress-re került.
>
> **Megjegyzés (2026-08-01, folytatás 3):** A Phase 2 (Functional Specifications) mind a nyolc tervezett specifikációja (Mesh Import, Slice Engine, Gap System, Dowel System, Backplate, Numbering, Nesting, DXF Export) elkészült és a projektgazda jóváhagyta — a kilépési feltétel teljesült. A munka során több, korábban elfogadott specifikáció és architekturális döntés is felülvizsgálatra és pontosításra került (ADR-0003–0005), amikor a részletes kidolgozás új, korábban fel nem ismert függőségeket vagy ellentmondásokat tárt fel. A Phase 2 ezért ✅ Approved-ra, a Phase 3 (Architecture Freeze) pedig 🟡 In Progress-re került.
>
> **Megjegyzés (2026-08-01, folytatás 4):** A Phase 3 (Architecture Freeze) kilépési feltétele teljesült — az architektúra és a nyolc specifikáció rendszerezett áttekintése megtörtént (ARCHITECTURE.md belső konzisztencia, DOMAIN_MODEL.md kereszthivatkozások, szétszórt backlog-bejegyzések rendezése, a teljes pipeline adatszerződéseinek végigfuttatása), a feltárt hiányosságok javításra kerültek, és a projektgazda jóváhagyta. A Phase 3 ezért ✅ Approved-ra, a Phase 4 (Implementation) pedig 🟡 In Progress-re került.
>
> **Megjegyzés (2026-08-03, folytatás 5):** A Phase 4 (Implementation) mind a nyolc, ROADMAP Phase 2-ben rögzített engine-je (Mesh Import, Slice Engine, Dowel System, Gap System, Backplate, Numbering, Nesting, DXF Export) elkészült, review-n átment, és a projektgazda jóváhagyta (89/89 automatizált teszt, `PYTHONHASHSEED=0 uv run pytest`). A munka során két, a specifikációk által Phase 4-re hagyott, keresztmetsző implementációs döntés (kontúr körüljárási irány, ADR-0007; Nesting Engine csomagolási algoritmus, ADR-0008) ADR-ben rögzítésre került. A Phase 4 ezért ✅ Approved-ra, a Phase 5 (Integration) pedig 🟡 In Progress-re került.
>
> **Megjegyzés (2026-08-04, folytatás 6):** A Phase 5 (Integration) eredeti öt tétele (modulok összekapcsolása, GUI, teljes workflow, projektmentés, beállítások) elkészült. Ezeken felül a GUI-t lezáró négy kiegészítő tétel (automatikus Mesh-előnézet, Dowel/Spacer/Backplate 3D-megjelenítés, szeletenkénti kiemelés) és két, élő tesztelés során feltárt és megvalósított javítás (Dowel automatikus pozíciókeresés térbeli szórása, Numbering Slice-oldali szigorúságának figyelmeztetés-alapúra enyhítése) is a fázis részeként valósult meg. A projektgazda jóváhagyta. A Phase 5 ezért ✅ Approved-ra, a Phase 6 (Release Candidate) pedig 🟡 In Progress-re került, első tételeként a DXF export Futtatásról való leválasztásával (önálló interakció, Döntési javaslat és Impact Analysis alatt).
>
> **Megjegyzés (2026-08-04, folytatás 7):** A Phase 6 első tétele (DXF export leválasztása a Futtatásról) a teljes munkafolyamaton átment — Döntési javaslat, Hatásvizsgálat, projektgazdai jóváhagyás, majd ADR-0009 és az ARCHITECTURE.md módosítása, ezt követően a Claude Code általi implementáció (200/200 automatizált teszt) —, és a projektgazda élő teszteléssel is megerősítette. A Phase 6 többi tétele (végső tesztelés, optimalizálás, dokumentáció, példaprojektek) még nyitott, a fázis ezért továbbra is 🟡 In Progress.

## Állapotjelölések

| Jelölés | Jelentés |
|---|---|
| ⬜ Not Started | A fázis még nem kezdődött el. |
| 🟡 In Progress | A fázis folyamatban van. |
| 🟢 Review | A fázis eredménye elkészült, felülvizsgálat alatt áll. |
| ✅ Approved | A fázis eredményét a projektgazda jóváhagyta. |
| 🔒 Locked | A fázis lezárva; kizárólag ADR alapján módosítható. |

## Fázisok

### Phase 0 – Project Foundation

Állapot: ✅ Approved

Feladata:

* projektstruktúra
* README
* PROJECT_CONSTITUTION
* PROJECT_VISION
* ENGINEERING_PRINCIPLES
* ARCHITECTURE
* PROJECT_STRUCTURE
* CODING_STANDARDS
* AI_WORKFLOW
* PROMPT_STANDARD

Kilépési feltétel: A projekt dokumentációja önmagában értelmezhető.

---

### Phase 1 – Domain Design

Állapot: ✅ Approved

Feladata:

* DOMAIN_MODEL (aktív dokumentum)
* koordinátarendszer
* mértékegységek
* alapvető objektummodell
* anyagmodell
* szeletmodell
* összeállítási modell

Kilépési feltétel: A projekt egységes fogalomrendszerrel rendelkezik.

---

### Phase 2 – Functional Specifications

Állapot: ✅ Approved

Minden fő funkció külön specifikációban készül, például:

* Mesh Import
* Slice Engine
* Gap System
* Dowel System
* Backplate
* Numbering
* Nesting
* DXF Export

Kilépési feltétel: Minden fő funkció rendelkezik jóváhagyott specifikációval.

---

### Phase 3 – Architecture Freeze

Állapot: ✅ Approved

Feladata:

* dokumentáció review
* architektúra véglegesítése
* hiányosságok javítása

Új funkció nem kerülhet be.

Kilépési feltétel: Az architektúra Approved állapotú.

---

### Phase 4 – Implementation

Állapot: ✅ Approved

A fejlesztés kizárólag jóváhagyott specifikáció alapján történt. Mind a nyolc engine (Mesh Import, Slice Engine, Dowel System, Gap System, Backplate, Numbering, Nesting, DXF Export) elkészült, automatizált teszttel (89 teszt) lefedve.

---

### Phase 5 – Integration

Állapot: ✅ Approved

Feladata:

* modulok összekapcsolása
* GUI
* teljes workflow
* projektmentés
* beállítások

Megjegyzés: az eredeti öt tételen felül a GUI-t lezáró négy kiegészítő tétel (automatikus Mesh-előnézet, Dowel/Spacer/Backplate 3D-megjelenítés, szeletenkénti kiemelés) és két, élő teszteléskor feltárt javítás (Dowel automatikus pozíciókeresés térbeli szórása, Numbering figyelmeztetés-alapú kezelése) is a fázis részeként valósult meg.

---

### Phase 6 – Release Candidate

Állapot: 🟡 In Progress

Feladata:

* ~~DXF export leválasztása a Futtatásról (önálló interakció)~~ — kész (ADR-0009)
* végső tesztelés
* optimalizálás
* dokumentáció
* példaprojektek

---

## Általános szabályok

* Egyszerre csak egy fázis lehet aktív.
* A következő fázis csak az előző lezárása után kezdhető meg.
* Locked állapotú fázis kizárólag Architecture Decision Record alapján módosítható.
* A ROADMAP a projekt fejlesztési sorrendjének hivatalos nyilvántartása.
