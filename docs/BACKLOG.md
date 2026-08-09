# Backlog

Státusz: Aktív
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-04
Utolsó módosítás: 2026-08-09
Kapcsolódó dokumentumok: [ROADMAP.md](ROADMAP.md)

## Cél

Ez a dokumentum azokat a jövőbeli tételeket (funkciókat, optimalizálásokat) sorolja fel, amelyek felmerültek a fejlesztés során, de nem tartoznak a jelenlegi fázis kilépési feltételei közé. Nem specifikáció és nem ROADMAP — kizárólag nyomon követhetőségi célt szolgál, formális elvárás (pl. SPECIFICATION_STANDARD) nélkül.

## Tételek

### 1. 2D export-előnézet

A Nesting Engine kimenetének (exportra kerülő vektorok) 2D megjelenítése ellenőrzés céljából, futtatás/export előtt.

**Eredet / indoklás:** Új funkció, nincs jelenleg dokumentációs alapja — önálló specifikáció és jóváhagyás szükséges bevezetése előtt.

### 2. `[project.scripts]` bejegyzés hozzáadása

Kényelmi parancssori indító parancs (pl. `slicedesigner`) bevezetése a jelenlegi, teljes `uv run python -m slicedesigner.gui.app` parancs helyett/mellett.

**Eredet / indoklás:** A 6.1 (`USER_GUIDE.md`) és 6.4 (`RELEASE_NOTES.md`) tételek dokumentálása során azonosított hiány. Kódváltoztatást (`pyproject.toml`) igényel, ezért nem valósítható meg Phase 6 dokumentációs tételként.

### 3. Dedikált "Példák megnyitása" GUI-funkció

Jelenleg a példaprojektek (`examples/`) kizárólag az általános "Fájl → Projekt megnyitása..." fájl-választó dialógussal, kézzel navigálva nyithatók meg — nincs dedikált menü/gomb, ami az `examples/` mappát vagy annak tartalmát közvetlenül felkínálná.

**Eredet / indoklás:** A ROADMAP Phase 6, 6.5 tétel (Alap példaprojekt) végrehajtása közben merült fel; a projektgazda döntése alapján nem Phase 6 hatóköre, hanem külön, jövőbeli funkció — önálló specifikáció és jóváhagyás szükséges bevezetése előtt.
