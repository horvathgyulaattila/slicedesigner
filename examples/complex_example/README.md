# Összetett példaprojekt

Ez a mappa a Slice Designer fő funkcióinak együttes működését mutatja be: Dowel, Gap (Spacer) és Backplate egyszerre aktív, a Numbering és a Nesting mellett.

## Mit demonstrál

* STL importálás egy procedurálisan generált téglatestről (100×60×80 mm).
* Szeletelés: 10 mm-es szeletvastagság, 4 mm-es Gap — 6 szelet, 5 Gap.
* Mindhárom opcionális összeépítési mechanizmus aktív:
  * **Dowel** (6 mm átmérő)
  * **Gap / Spacer** (20 mm átmérő — meg kell egyeznie a Dowel panel Spacer-átmérőjével)
  * **Backplate** (+X oldal, 6 mm vastagság, 15 mm csaphossz)
* Numbering (mindig aktív): mind a 6 szelet számozva, a Backplate-en is.
* Nesting (mindig aktív): három különböző anyag/vastagság (szeletek, Backplate, Spacer-ek), külön Nest-enként.
* DXF export, önálló lépésként (ADR-0009).

## Egy figyelemre méltó részlet

Mivel a Dowel és a Gap célszáma is 3 (alapértéken), és a téglatest egyetlen, folytonos régiót alkot mind a 6 szeleten át, az összes Spacer a Dowel-pozíciókra kerül, furattal — nincs önálló Spacer-pozíció. Ez a `WORKFLOW.md`-ben leírt "a Spacer a Dowel-pozícióhoz igazodik" szabályt mutatja be a gyakorlatban.

## Fájlok

* `box.stl` — a forrás modell.
* `generate_example.py` — a teljes példa reprodukálható előállítása, kézi beavatkozás nélkül.
* `complex_example.json` — a ténylegesen elmentett projektfájl.
* `plywood_10mm_sheet1.dxf`, `plywood_6mm_sheet1.dxf`, `plywood_4mm_sheet1.dxf` — a tényleges export eredménye, anyagonként külön fájl.

## Reprodukálás

A repó gyökeréből:

```
uv run python examples/complex_example/generate_example.py
```

A script felülírja a fenti kimeneti fájlokat, és a végén ellenőrzi, hogy a mentett projektfájl ténylegesen visszatölthető.

## Fontos: a `complex_example.json` gépspecifikus útvonalakat tartalmaz

A mentett projektfájl a generálás időpontjában érvényes, abszolút fájlrendszer-útvonalakat tartalmazza (`mesh_import.file_path`, `dxf_export.output_directory`). Emiatt más gépen, illetve a repó másik helyre klónozva a GUI "Projekt megnyitása" funkciójával közvetlenül nem biztos, hogy megnyitható — a példa megbízható reprodukálásához mindig a `generate_example.py` újrafuttatása a helyes út.
