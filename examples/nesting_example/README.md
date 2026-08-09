# Nesting példaprojekt

Ez a mappa a Slice Designer Nesting Engine-jének viselkedését mutatja be: sok, egyenként kis alkatrész optimális elrendezése több gyártási lapon.

## Mit demonstrál

* STL importálás egy procedurálisan generált, magas, karcsú hengerről (sugár 40 mm, magasság 200 mm).
* Szeletelés: 10 mm-es szeletvastagság, Gap nélkül — 20 szelet (szándékosan sok, kis alkatrész).
* Egyetlen aktív összeépítési mechanizmus: **Dowel** (6 mm átmérő) — a hangsúly a Nesting-en van, nem az összeépítésen (azt a `complex_example` már bemutatta).
* Nesting: egyetlen `plywood_10mm` anyag, szándékosan szűkös lapméret (300×200 mm) a 80 mm átmérőjű szeletekhez képest — ez **4 lapra** kényszeríti az elrendezést.
* DXF export, önálló lépésként (ADR-0009) — anyaglaponként külön fájl.

## Fájlok

* `cylinder.stl` — a forrás modell.
* `generate_example.py` — a teljes példa reprodukálható előállítása, kézi beavatkozás nélkül.
* `nesting_example.json` — a ténylegesen elmentett projektfájl.
* `plywood_10mm_sheet1.dxf` … `plywood_10mm_sheet4.dxf` — a tényleges export eredménye, laponként külön fájl.

## Reprodukálás

A repó gyökeréből:

```
uv run python examples/nesting_example/generate_example.py
```

A script felülírja a fenti kimeneti fájlokat (a lapszám a futtatás eredményétől függően eltérhet, ha a paramétereken változtatsz), és a végén ellenőrzi, hogy a mentett projektfájl ténylegesen visszatölthető.

## Fontos: a `nesting_example.json` gépspecifikus útvonalakat tartalmaz

A mentett projektfájl a generálás időpontjában érvényes, abszolút fájlrendszer-útvonalakat tartalmazza (`mesh_import.file_path`, `dxf_export.output_directory`). Emiatt más gépen, illetve a repó másik helyre klónozva a GUI "Projekt megnyitása" funkciójával közvetlenül nem biztos, hogy megnyitható — a példa megbízható reprodukálásához mindig a `generate_example.py` újrafuttatása a helyes út.
