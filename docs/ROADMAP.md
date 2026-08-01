# Roadmap

Státusz: Aktív
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-07-31
Utolsó módosítás: 2026-08-01
Kapcsolódó dokumentumok: [PROJECT_CONSTITUTION.md](PROJECT_CONSTITUTION.md), [AI_WORKFLOW.md](AI_WORKFLOW.md), [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md), [DOMAIN_MODEL.md](DOMAIN_MODEL.md)

## Cél

Ez a dokumentum meghatározza a Slice Designer fejlesztési fázisainak sorrendjét, célját és jelenlegi állapotát.

## Leírás

A ROADMAP nem backlog, nem feladatlista és nem specifikáció. A célja, hogy bármelyik AI vagy új fejlesztő azonnal lássa, hol tart a projekt, mely fázisok készültek el, mi a következő lépés, és mely dokumentumok tekinthetők lezártnak. A ROADMAP kizárólag a fejlesztési folyamatot írja le, technikai megoldásokat nem.

> **Megjegyzés (2026-08-01):** A Phase 0 korábbi ✅ Approved jelölése tévesen került rögzítésre — a kilépési feltétel ("A projekt dokumentációja önmagában értelmezhető") ténylegesen nem teljesült, mivel több Phase 0-hoz tartozó dokumentum vázlat állapotban maradt. A Phase 0 ezért 🟡 In Progress-re, a rá épülő Phase 1 pedig ⬜ Not Started-ra lett visszaminősítve.

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

Állapot: 🟡 In Progress

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

Állapot: ⬜ Not Started

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

Állapot: ⬜ Not Started

Minden fő funkció külön specifikációban készül, például:

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

Állapot: ⬜ Not Started

Feladata:

* dokumentáció review
* architektúra véglegesítése
* hiányosságok javítása

Új funkció nem kerülhet be.

Kilépési feltétel: Az architektúra Approved állapotú.

---

### Phase 4 – Implementation

Állapot: ⬜ Not Started

A fejlesztés kizárólag jóváhagyott specifikáció alapján történik. Minden modul külön implementációs ciklusban készül.

---

### Phase 5 – Integration

Állapot: ⬜ Not Started

Feladata:

* modulok összekapcsolása
* GUI
* teljes workflow
* projektmentés
* beállítások

---

### Phase 6 – Release Candidate

Állapot: ⬜ Not Started

Feladata:

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
