# ADR-0021: Image Relief Generator — Blob-alapú régió-hozzárendelés

Dátum: 2026-09-04
Státusz: Elfogadva
Döntéshozó: Horváth Gyula Attila (projektgazda)

## Kontextus

A ROADMAP Phase 13.9 (Interaktív GUI a régió-hozzárendeléshez) tervezése közben felmerült, hogy a 13.2-ben (Elfogadva) bevezetett, színenkénti stratégia (`interpret_image()`) nem tudja megkülönböztetni két, a képen azonos színű, de térben össze nem függő, valójában független objektumot (pl. egy ház két, azonos színű ablaka) — ezeket a színenkénti stratégia mindig egyetlen, közös Regionba vonná össze, mert a Mask-ja a szín MINDEN előfordulását lefedi (`IMAGE_RELIEF_INTERPRETATION.md` 3.3 szakasz, szándékos, dokumentált tervezési döntés, nem hiba).

A leendő interaktív GUI kattintás-alapú interakciója (a felhasználó egy foltra kattint, nem egy színt választ ki egy listából) természetes módon egy **seed-pixel-alapú, összefüggő-komponens szemantikát** igényel — ez indokolja egy új, a színenkénti stratégiával egyenrangú, azt ki nem váltó, önálló interpretation-mechanizmus bevezetését.

Négy alternatív megközelítés merült fel a tervezés során, mielőtt a jelen döntésre jutottunk:

- **Globális kép-kvantálás + komponensbontás** — elvetve (l. "Mérlegelt alternatívák").
- **A 13.2 `interpret_image()` módosítása/bővítése komponens-szintű elemzéssel** — elvetve, mert egy már Elfogadva, tesztelt kontraktust módosítana anélkül, hogy a színenkénti stratégiának bármilyen ma is érvényes használati esetét (pl. a 13.8 meglévő tesztjeit) veszélyeztetné a haszna indokolná.
- **Perceptuális színtér (pl. HSV) a színtávolsághoz** — elvetve, validált szükség (pl. tényleges, megfigyelt hiba egy valós fotón) nélkül korai lenne.
- **Mesterséges méretkorlát a kijelölésre** — elvetve, mert a döntés 5. pontja (l. lent) más eszközökkel (azonnali vizuális visszajelzés, szerkeszthetőség, háttérszálas futás — ez utóbbi a 2. rész GUI-promptjának tárgya) már kezeli a kockázatot, mesterséges korlát nélkül.

## Döntés

**1. Új, önálló domain-függvény: `interpret_image_blob(image_path, assignment_path) -> tuple[Region, ...]`** (`plugins/relief_generator/domain/image_interpretation_blob.py`), ugyanazzal a kimeneti szerződéssel, mint a 13.2-es `interpret_image()`, de teljesen más bemeneti sémával és algoritmussal. A 13.2-es `interpret_image()` és a hozzá tartozó JSON-séma **egyetlen sora sem változik**.

**2. Seed-pixel-alapú JSON séma**, színek helyett:

```json
{
  "strategy": "blob",
  "regions": [
    {"seed_pixel": [34, 12], "color_tolerance": 12.0, "contribution": 0.5, "depth_behavior": "raised", "parent": null},
    {"seed_pixel": [40, 18], "color_tolerance": 5.0, "contribution": 0.2, "depth_behavior": "recessed", "parent": [34, 12]}
  ]
}
```

Nincs `background` mező — minden, egyetlen deklarált folt által sem lefedett pixel implicit "nincs hozzájárulás" (a Region Resolver/`combine` szintjén ez már ma is természetesen 0 elevation-t jelent, nincs hozzá külön mechanizmus szükséges).

**3. Flood-fill algoritmus**, a 2.2 szakaszban (l. a fő promptban) rögzített öt tervezési döntés szerint: 4-szomszédság, a seed pixel színéhez (nem az előző lépés pixeléhez) viszonyított Euklideszi RGB-távolság, folt-szintű `color_tolerance`, **iteratív** bejárás (explicit verem, nem rekurzió — egy nagy, összefüggő folt könnyen túllépné a Python rekurziós mélységi korlátját).

**4. Dispatch-mechanizmus**: a hozzárendelési fájl opcionális, top-level `"strategy"` mezője (`"color"` | `"blob"`, alapértelmezett `"color"` — ez teszi a döntést tisztán additívvá, minden meglévő, `"strategy"` mező nélküli hozzárendelési fájl változatlanul a színenkénti stratégiát futtatja). Egy új, vékony `interpret_assignment(image_path, assignment_path)` függvény (`plugins/relief_generator/domain/assignment_dispatch.py`) végzi a döntést, és hívja a megfelelő stratégiát — ez veszi át az `interpret_image()` szerepét minden, a Semantic World-öt hívó felsőbb rétegben (l. "Következmények").

**5. Hibakezelés**: nincs új kivétel-osztály — a blob-stratégia minden hibája (érvénytelen/hiányzó mező, kép határain kívüli `seed_pixel`, feloldhatatlan `parent`-hivatkozás, körkörös `parent`-lánc, ismeretlen `strategy` érték) a meglévő `ImageInterpretationError`-t használja, ugyanazon a szemantikai alapon, mint a 13.2-es stratégia hasonló hibái.

**6. Explicit `parent`-validáció, szándékos, dokumentált eltérés a 13.2-es minta implicit viselkedésétől**: a 13.2-es `interpret_image()` egy feloldhatatlan `parent`-hivatkozást (vagy egy kört) nem jelez explicit hibaként, hanem — mivel a fastruktúra kizárólag a gyökerekből (`parent is None`) épül fel lefelé — az ilyen bejegyzések egyszerűen kimaradnak a végeredményből. A blob-stratégiánál ezt **explicit hibaként** (`ImageInterpretationError`) kezeljük, mert ennek a stratégiának az elsődleges, tervezett bemeneti forrása egy élő, interaktív GUI-interakció (2. rész) — ott egy hallgatólagosan eldobott, hibás hivatkozás sokkal megtévesztőbb (a felhasználó nem venné észre, hogy egy régiója "eltűnt"), mint egy fájlszerkesztéssel előállított, batch-feldolgozott JSON esetén.

## Mérlegelt alternatívák

- **Globális kép-kvantálás + komponensbontás** (a Szoftverarchitekt eredeti javaslata) — elvetve. A kvantálás egy egész képre ható, globális lépés: ha a tolerancia miatt két, eredetileg eltérő szín ugyanabba a kvantált osztályba kerül, ennek hatása kiszámíthatatlanul terjedhet át a kép távoli, a felhasználó szándéka szerint teljesen független részeire is — ez pontosan az a fajta rejtett, nehezen belátható mellékhatás, amit a projekt módszertana kerülni igyekszik. A végül elfogadott, seed-alapú flood-fill ezzel szemben szigorúan lokális: egyetlen kattintás kizárólag a saját folt határát befolyásolja.
- **8-szomszédság** — elvetve, l. Döntés 3. pontja indoklása.
- **Kattintásonként újraszámoló, automatikus mask-frissítés tolerancia-változáskor** — ez GUI-szintű kérdés (2. rész tárgya), itt csak annyiban releváns, hogy a domain-függvény maga állapotmentes és determinisztikus — a "mikor fusson újra" kérdés a hívó felelőssége.

## Következmények

- Új domain-modul: `plugins/relief_generator/domain/image_interpretation_blob.py` (`interpret_image_blob`).
- Új domain-modul: `plugins/relief_generator/domain/assignment_dispatch.py` (`interpret_assignment`).
- Új domain-contract dokumentum: `docs/plugins/relief_generator/IMAGE_RELIEF_BLOB_INTERPRETATION.md`.
- `docs/plugins/relief_generator/IMAGE_RELIEF_INTERPRETATION.md` (13.2, Elfogadva) "Réteghatár" szakasza egy ponton pontosításra kerül: a 13.9 nem váltja ki, hanem kiegészíti a jelen dokumentumban leírt stratégiát.
- `docs/plugins/relief_generator/IMAGE_RELIEF_ORCHESTRATION.md` (13.8, Elfogadva) egy ponton pontosításra kerül: a `ImageReliefGeneratorMeshSource.get_mesh()` mostantól `interpret_assignment()`-et hív `interpret_image()` helyett.
- `plugins/relief_generator/source/image_relief_generator_mesh_source.py` (13.8, Elfogadva) egyetlen importja és egyetlen függvényhívása cserélődik — a `Mesh`-előállítás, a `raw_relief` closure, a `GeometricSurface`/`GeometricSurfaceMeshGenerator`-hívások egyetlen sora sem változik.
- A GUI-réteg (`RegionAssignmentDialog`, `ParameterSpec.editor`, önálló ADR-0022) — külön, 2. rész prompt tárgya, erre a rétegre épül.
