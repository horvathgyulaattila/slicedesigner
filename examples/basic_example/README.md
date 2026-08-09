# Alap példaprojekt

Ez a mappa a Slice Designer legegyszerűbb, teljes körű használatát mutatja be: egy STL importálásától a DXF exportig, a lehető legkevesebb bekapcsolt funkcióval.

## Mit demonstrál

* STL importálás egy procedurálisan generált, egyszerű hengerről (sugár 50 mm, magasság 60 mm).
* Szeletelés: 6 mm-es szeletvastagság, Gap nélkül — pontosan 10 szelet.
* Egyetlen aktív összeépítési mechanizmus: **Dowel** (6 mm átmérő) — sem Gap/Spacer, sem Backplate nincs bekapcsolva.
* Numbering (mindig aktív): minden szelet 1-től 10-ig számozva.
* Nesting (mindig aktív): egyetlen `plywood_6mm` anyag, egyetlen lapra.
* DXF export, önálló lépésként (ADR-0009).

## Fájlok

* `cylinder.stl` — a forrás modell.
* `generate_example.py` — a teljes példa reprodukálható előállítása (STL generálása + pipeline futtatása + export + mentés), kézi beavatkozás nélkül.
* `basic_example.json` — a ténylegesen elmentett projektfájl (a `generate_example.py` futtatásának eredménye).
* `plywood_6mm_sheet1.dxf` — a tényleges export eredménye.

## Reprodukálás

A repó gyökeréből:

```
uv run python examples/basic_example/generate_example.py
```

A script felülírja a fenti kimeneti fájlokat, és a végén ellenőrzi, hogy a mentett projektfájl ténylegesen visszatölthető.

## Fontos: a `basic_example.json` gépspecifikus útvonalakat tartalmaz

A mentett projektfájl a generálás időpontjában érvényes, abszolút fájlrendszer-útvonalakat tartalmazza (`mesh_import.file_path`, `dxf_export.output_directory`). Emiatt a `basic_example.json` más gépen, illetve a repó másik helyre klónozva a GUI "Projekt megnyitása" funkciójával közvetlenül nem biztos, hogy megnyitható — a benne hivatkozott elérési út a generáláskor használt gépen létezik, máson nem.

A példa megbízható reprodukálásához mindig a `generate_example.py` újrafuttatása a helyes út, ne a `.json` közvetlen megnyitása egy másik gépen.
