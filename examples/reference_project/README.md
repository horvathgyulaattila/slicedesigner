# Teljes referencia projekt

Ez a mappa a Slice Designer legösszetettebb, egyben legreálisabb bemutató projektje: egy valódi, tagolt geometria (nem primitív box/henger), mindhárom opcionális összeépítési mechanizmussal egyszerre.

## A modell

Egy "kapu"-forma: két, egymástól távol álló láb, amelyeket egy felső gerenda köt össze — mint egy egyszerű állvány vagy konzol. Három egyszerű téglatestből áll (2 láb: 30×40×72 mm; 1 gerenda: 120×40×22 mm), egyetlen, valódi watertight szilárd testté egyesítve. Teljes befoglaló méret: 120×40×94 mm.

## Tervezési döntések

* **Miért "kapu"-forma, nem box/henger?** A cél egy olyan geometria, ahol a szeletek szigetszáma **változik** a magasság mentén: a lábak tartományában (Z 0–72 mm) minden szelet 2, egymástól elkülönülő szigetet ad, a gerenda tartományában (Z 72–94 mm) 1-et. Ez a `DOMAIN_MODEL.md` Sziget-fogalmát és a régió-alapú Dowel/Gap-logikát a korábbi (box/henger) példáknál valóságosabban mutatja be.
* **Miért Boole-unió, és nem egyszerű összefűzés? (eltérés az eredeti tervtől)** Az eredetileg jóváhagyott terv `trimesh.util.concatenate()`-tel, Boole-művelet nélkül fűzte volna össze a három téglatestet, tudatosan vállalva egy nem-manifold figyelmeztetést importáláskor. A tényleges futtatás során ez a Backplate Engine-t hibával állította meg (`ValueError: Not all meshes are volumes!`): a lábak belső éle (a "kapunyílás" felőli oldalon) a gerenda alsó lapjának *belsejében* végződik (klasszikus T-illesztés/T-junction), ami a mesh-import lépés csúcspont-összevonása (vertex merge) után valódi, nem javítható non-manifold geometriát eredményez — ezen a Backplate Engine belső Boole-metszete (`_build_backplate_shape_from_mesh()`, a Backplate alakjának a modell tényleges geometriájából történő felépítéséhez) elhasal, függetlenül attól, hogy a hiba maga "szándékos bemutató" célra lett-e tervezve. Ennek feloldásaként a három téglatestet valódi, Boole-unióval (`trimesh.boolean.union()`) egyetlen watertight szilárd testté egyesítjük — ezt a projekt már meglévő `manifold3d` függősége (`pyproject.toml`) teszi lehetővé, ugyanaz, amit a Backplate Engine is belsőleg használ a saját Boole-metszeteihez. Ez a legkisebb, a geometria vizuális formáját és a paraméterezést változatlanul hagyó módosítás, ami a példát ténylegesen működővé teszi.
* **Nincs nem-manifold figyelmeztetés — a fenti javítás következménye:** mivel a Boole-unió egy valódi, watertight szilárd testet állít elő, a betöltéskor (ellentétben az eredeti tervvel) **nem** jelenik meg non-manifold figyelmeztetés. Ez a `USER_GUIDE.md` 4. szakasza szerinti figyelmeztetés-viselkedést emiatt ez a példa nem mutatja be — ehelyett azt szemlélteti, hogy egy első ránézésre "egyszerű összefűzésnek" tűnő geometria (érintkező, de nem uniózott testek) a gyakorlatban valódi Boole-uniót igényelhet, mielőtt a Backplate Engine-nel használható lenne.
* **Szeletelés (10 mm vastagság, 2 mm Gap):** a 8 szelet/7 Gap úgy illeszkedik a 94 mm teljes magasságra, hogy minden szelet egyértelműen vagy a láb-tartományba, vagy a gerenda-tartományba esik — egy szelet sem lóg át a kettő között.
* **Backplate a +Y oldalon:** ez az egyetlen tengely, ami mind a lábakon, mind a gerendán azonos (mindkettő 40 mm mély) — így a Backplate egyetlen, folytonos síkkal illeszkedik az egész modellhez.
* **Numbering a −Y oldalon, szándékosan a Backplate-tel szemben:** konkrétan mutatja be, hogy a `numbering_normal_axis` és a `backplate_normal_axis` egymástól teljesen független paraméter (`WORKFLOW.md` 2. szakasz, 5. pont).

## Mit demonstrál

* STL importálás egy összetettebb, három részből álló, ténylegesen watertight modellről (lásd fent, "Tervezési döntések").
* Szeletelés: 10 mm vastagság, 2 mm Gap — 8 szelet.
* Mindhárom opcionális mechanizmus aktív: Dowel (6 mm), Gap/Spacer (10 mm, Dowellel egyeztetve), Backplate (+Y oldal, 6 mm vastagság, 8 mm csaphossz).
* Numbering (−Y oldal, 8 mm) és Nesting (három anyag: `plywood_10mm`/`plywood_6mm`/`plywood_2mm`) mindig aktív.
* DXF export, önálló lépésként (ADR-0009).

## Tényleges futtatási eredmény

* Szeletek: 8
* Dowel-ek: 3
* Spacer-ek: 39
* Backplate: igen
* Nest-ek: 3 (anyagonként: `plywood_10mm` 1 lap, `plywood_6mm` 1 lap, `plywood_2mm` 1 lap)

## Fájlok

* `gate.stl` — a forrás modell.
* `generate_example.py` — a teljes példa reprodukálható előállítása, kézi beavatkozás nélkül.
* `reference_project.json` — a ténylegesen elmentett projektfájl.
* `plywood_10mm_sheet1.dxf`, `plywood_6mm_sheet1.dxf`, `plywood_2mm_sheet1.dxf` — a tényleges export eredménye, anyagonként külön fájl.

## Reprodukálás

A repó gyökeréből:

```
uv run python examples/reference_project/generate_example.py
```

A script felülírja a fenti kimeneti fájlokat, és a végén ellenőrzi, hogy a mentett projektfájl ténylegesen visszatölthető.

## Fontos: a `reference_project.json` gépspecifikus útvonalakat tartalmaz

A mentett projektfájl a generálás időpontjában érvényes, abszolút fájlrendszer-útvonalakat tartalmazza (`mesh_import.file_path`, `dxf_export.output_directory`). Emiatt más gépen, illetve a repó másik helyre klónozva a GUI "Projekt megnyitása" funkciójával közvetlenül nem biztos, hogy megnyitható — a példa megbízható reprodukálásához mindig a `generate_example.py` újrafuttatása a helyes út.
