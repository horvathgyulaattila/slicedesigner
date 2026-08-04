# ADR-0009: A DXF Export leválasztása a Futtatásról

Dátum: 2026-08-04
Státusz: Elfogadva
Döntéshozó: Horváth Gyula Attila (projektgazda)

## Kontextus

A `run_pipeline()` jelenleg minden "Futtatás" alkalmával automatikusan DXF fájlokat ír a lemezre. Élő, iteratív teszteléskor (paraméterek finomhangolása, sok egymást követő Futtatás) ez feleslegesen sok, azonnal elavuló fájlt hoz létre a kimeneti könyvtárban. A Nesting Engine önmagában nem ír lemezre, kizárólag számol — a lemez-"szemetelést" kizárólag a DXF Export (fájlírás) okozza. A 3D-előnézet a Nesting eredményét (Nest-eket) nem használja, ezért a Nesting továbbra is indokoltan lefuthat a Futtatás részeként.

## Döntés

A Nesting továbbra is automatikusan lefut a Futtatás részeként. A DXF-fájlírás ezzel szemben önálló, explicit felhasználói interakcióvá válik: a `run_panel.py` kimenet-paneljén elhelyezett "DXF Export" gombbal indítható, kizárólag a legutóbbi sikeres Futtatás Nest-jein. A gomb kezdetben, és minden új Futtatás indításakor letiltott állapotba kerül, majd csak a Futtatás sikeres befejezése után válik újra engedélyezetté — a legutóbbi Nest-ek egy új Futtatás elindításával érvényüket vesztik.

## Mérlegelt alternatívák

* **Változatlan, automatikus export** (jelenlegi/eredeti architektúra) — elvetve, ez a jelen probléma forrása (felesleges, azonnal elavuló DXF fájlok élő tesztelés közben).
* **A Nesting is opcionális/külön indítású legyen** — elvetve, mert a 3D-előnézet (és a BACKLOG.md-ben rögzített, jövőbeli 2D export-előnézet) igényli a Nesting eredményét; a Nesting fájlt nem ír, így az automatikus lefutása nem okozza az eredeti problémát.
* **Export-gomb a "Fájl" menübe** — elvetve, a projektgazda döntése szerint az export logikailag a Futtatás kimenetéhez tartozik, ezért a kimenet-panelen (`run_panel.py`) a helye.

## Következmények

* A `PipelineResult` már nem tartalmaz automatikusan előállított exportot (`exports` mező törölve) — a DXF Export a `pipeline.py` egy önálló, vékony wrapperén (`export_pipeline_result_to_dxf()`) keresztül, a GUI explicit kérésére fut le.
* Az `ARCHITECTURE.md` pipeline-leírása pontosításra kerül: a Nesting Engine-ig a Futtatás automatikusan lefut, a DXF Export (fájlírás) viszont önálló, explicit felhasználói interakció.
* A `run_panel.py` egy új "DXF Export" gombot kap; a `MainWindow` a legutóbbi sikeres Futtatás Nest-jeit tárolja, és ezekhez köti a gomb engedélyezett/letiltott állapotát.
