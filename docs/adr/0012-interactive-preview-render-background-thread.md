# ADR-0012: A kiemelés-/nézet-váltás interaktív újraépítésének háttérszálra vitele

Dátum: 2026-08-09
Státusz: Elfogadva
Döntéshozó: Horváth Gyula Attila (projektgazda)

## Kontextus

Az ADR-0011 szándékosan hatókörön kívül hagyta a kiemelés-váltás (`_on_highlight_changed()`) és a nézet-váltás (`_on_view_switch_toggled()`, "Szeletelt összeállítás" ág) által kiváltott újraépítést — ezek a szinkron `preview_panel.py::_render_sliced_assembly()`-t hívták, ugyanazzal a teljes geometria-építési+renderelési költséggel, mint amit a Futtatás utáni útvonalnál az ADR-0011 már kiváltott.

A Projektgazda döntése ebben a körben: **egyszerűség előnyben** — nincs szükség tényleges szál-megszakításra/eldobásra (pl. `QThread.terminate()` vagy egy futó worker explicit leállítása); egy könnyű **generáció-számláló** elegendő annak biztosítására, hogy egy régebbi, később befejeződő számítás sose írja felül egy újabb eredményét a nézeten.

Kód-átvizsgálással feltárt, a "pörgetés közbeni" eseten túli korrektségi kockázat: a `MainWindow.__init__` a `PreviewPanel.assembly_render_succeeded`/`assembly_render_failed` jelzéseket a `_finish_run()`-hoz köti (a Futtatás-állapot — gomb, menü, folyamatjelző — lezárásához). A kiemelés-/nézet-váltó widgetek (spinbox, checkbox, rádiógombok) NINCSENEK letiltva egy futó Futtatás alatt (csak a `run_button`) — így egy felhasználó, miközben egy ÚJ Futtatás háttérben számol, még mindig módosíthatja a kiemelést a RÉGI, még látott összeállításon. Ha ez a régi, interaktív render később fejeződik be, mint az új Futtatás teljes (pipeline + előnézet) folyamata, és mindkettő ugyanazt a publikus jelzést sütné el, a `_finish_run()` téves időpontban (vagy duplán) futna le, illetve elméletileg felül is írhatná az új Futtatás eredményét a nézeten.

## Döntés

A szinkron `_render_sliced_assembly()` **törlésre került** — két párhuzamos renderelési út fenntartása helyett a kiemelés-váltás (`_on_highlight_changed()`) és a nézet-váltás (`_on_view_switch_toggled()`, "Szeletelt összeállítás" ág) is a meglévő `_build_sliced_assembly_geometry()`/`_PreviewComputeWorker`/`_render_geometry_bundle()` hármast hasznosítja újra — nem új gépezet, csak további hívási hely, `is_post_run=False` paraméterrel.

Egy `self._render_generation: int` számláló (`PreviewPanel.__init__()`, kezdőérték `0`) minden async-render induláskor eggyel nő — mindhárom hívási helyen (Futtatás utáni is!), enélkül egy régi, kiemelés-eredetű worker nem venné észre, hogy közben egy ÚJ Futtatás-eredetű render indult. Minden worker a saját indításkori generációját hordozza (`_PreviewComputeWorker` konstruktor-paraméter, a `succeeded`/`failed` jelzés kísérő adatában — `_PreviewRenderSucceeded`/`_PreviewRenderFailed` — utazik vissza a fő szálra).

**A két eredet eltérő kezelése**, a `PreviewPanel._on_preview_geometry_ready()`/`_on_preview_geometry_failed()` MEGOSZTOTT, mindhárom hívási helyet kiszolgáló slot-párban:

* **Futtatás utáni (post-pipeline) worker**: viselkedése VÁLTOZATLAN — mindig renderel, mindig emittálja a publikus `assembly_render_succeeded`/`assembly_render_failed`-et, staleness-ellenőrzés NÉLKÜL. Indoklás: a `run_button` a teljes Futtatás-folyamat (pipeline + előnézet) alatt letiltva marad, ezért két egyidejű Futtatás-eredetű worker strukturálisan kizárt — a generáció-ellenőrzés nála szükségtelen, felesleges komplexitás lenne.
* **Kiemelés-/nézet-váltás eredetű (interaktív) worker**: HA a nála rögzített generáció már nem egyezik `self._render_generation` aktuális értékével (mert közben — akár interaktív, akár Futtatás-eredetű — egy újabb render indult), az eredmény csendben eldobásra kerül: a bundle NEM kerül a plotterbe, a `_preview_worker`-referencia törlésén kívül más nem történik. **Semmilyen körülmények között nem emittálja** a publikus `assembly_render_succeeded`/`assembly_render_failed` jelzéseket — a `MainWindow` az interaktív renderekről nem szerez (és nem is kell, hogy szerezzen) tudomást. Ez zárja el egyszerre mindkét korrektségi kockázatot (pörgetés közbeni elavult eredmény ÉS Futtatás-közbeni kiemelés-váltás elavult eredménye).

A `main_window.py` **nem módosult** — mivel a kiemelés-/nézet-váltás sosem lép ki a `PreviewPanel`-ből a publikus jelzéseken keresztül, a `MainWindow`-nak nincs is miről tudomást szereznie.

## Mérlegelt alternatívák

* **Tényleges szál-megszakítás/eldobás** (pl. egy korábbi, még futó worker explicit leállítása egy újabb indításakor) — elvetve a Projektgazda kifejezett egyszerűség-preferenciája alapján: a `_build_sliced_assembly_geometry()` (a `render_geometry.py`-hívások) nem rendelkezik megszakítási ponttal, egy ilyen mechanizmus vagy kooperatív megszakítás-jelzést igényelne a geometria-építő kódban (ARCHITECTURE.md szerint tiszta, üzleti logikát nem tartalmazó, de emiatt "megszakítás-tudatlan" réteg), vagy a már lefutott (de eldobandó) számítás erőforrás-pazarlását kellene elfogadni — a generáció-számláló ugyanezt az erőforrás-pazarlást elfogadja, de architekturális komplexitás nélkül.
* **Ugyanaz a publikus jelzés (`assembly_render_succeeded`/`assembly_render_failed`) az interaktív workerekhez is** — elvetve: ez pontosan a Kontextusban leírt második korrektségi kockázatot okozná (a `MainWindow._finish_run()` téves időpontban/duplán futna le egy Futtatás-közbeni kiemelés-váltás miatt). Az interaktív renderek ezért architekturálisan "csendesek" maradnak — a `PreviewPanel`-en belül zajlanak le, kívülről nem megfigyelhetők.
* **Generáció-ellenőrzés a Futtatás utáni workerre is** — elvetve: a `run_button` letiltása miatt két egyidejű Futtatás-eredetű worker sosem fordulhat elő, az ellenőrzés hozzáadása csak felesleges komplexitás és potenciális hibaforrás (pl. egy éles, hosszú számítású Futtatás közben elindult interaktív render generációja "elavulttá" tehetné a Futtatás sikeres eredményét is, ha az ellenőrzés vaktában, eredet-megkülönböztetés nélkül futna).

## Következmények

* Érintett fájl: `src/slicedesigner/gui/preview_panel.py` — `_render_sliced_assembly()` törölve; `_PreviewComputeWorker` konstruktora `generation`/`is_post_run` paraméterekkel bővült; új `_PreviewRenderSucceeded`/`_PreviewRenderFailed` dataclass-ok (a `succeeded`/`failed` jelzés kísérő adatai); `_start_async_sliced_assembly_render()` mindhárom hívási helyhez közös, `is_post_run` kulcsszó-paraméterrel; `_on_preview_geometry_ready()`/`_on_preview_geometry_failed()` a fenti, eredet szerint elágazó logikával bővült; `self._render_generation` új állapot.
* `src/slicedesigner/gui/main_window.py` **nem módosult** — ez volt a tervezés egyik fő korlátja/ellenőrzőpontja: ha módosítást igényelt volna, az azt jelezte volna, hogy a jelzés-elkülönítés (interaktív renderek sosem érik el a `MainWindow`-t) nem valósult meg helyesen.
* `src/slicedesigner/gui/render_geometry.py` NEM módosult.
* A meglévő `tests/gui/test_preview_panel.py` tesztek frissültek: minden, kiemelés-/nézet-váltást kiváltó teszt determinisztikusan megvárja az interaktív render befejezését (`_preview_worker is None`, vagy — több, gyorsan egymást követő render esetén — a `_on_preview_geometry_ready()` hívásszáma), NEM a publikus jelzésre várva (az interaktív renderek sosem emittálják). Három új teszt igazolja: (1) a kiemelés-/nézet-váltás sosem emittálja a publikus jelzéseket; (2) két, egymást gyorsan követő kiemelés-váltás közül, ha a korábban induló fejeződik be később, az eredménye eldobásra kerül; (3) egy korábban induló interaktív worker, amely egy közben elindult Futtatás-eredetű render UTÁN fejeződik be, sem a plottert nem írja felül, sem a publikus jelzéseket nem váltja ki.
* A megjelenített végeredmény (rétegek, színek, opacitás, geometria) a kiemelés-/nézet-váltás útvonalán is bitre pontosan azonos maradt a korábbi, szinkron viselkedéssel — mindhárom hívási hely ugyanazt a `_build_sliced_assembly_geometry()`/`_render_geometry_bundle()` párost használja.
