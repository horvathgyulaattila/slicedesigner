# Felhasználói kézikönyv

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-09
Utolsó módosítás: 2026-08-29
Kapcsolódó dokumentumok: [PROJECT_VISION.md](PROJECT_VISION.md), [WORKFLOW.md](WORKFLOW.md), [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

## Cél

Ez a dokumentum a Slice Designer végfelhasználói kézikönyve: hogyan telepítsd, indítsd és használd az alkalmazást egy STL modelltől a gyártásra kész DXF exportig. A funkciók mögötti pontos szabályokat a `docs/specifications/` alatti specifikációk rögzítik — ez a kézikönyv azokra épül, de felhasználói nézőpontból, a szükséges részletességgel mutatja be őket.

## 1. Telepítés és indítás

A Slice Designer egy Python csomag, `uv` csomagkezelővel.

**Előfeltételek:** Python 3.11 vagy újabb, `uv` telepítve.

**Telepítés (a repó gyökeréből):**

```
uv sync
```

Ez létrehozza a virtuális környezetet és telepíti az összes függőséget (PySide6, trimesh, ezdxf, shapely és a többi).

**Indítás:**

```
uv run python -m slicedesigner.gui.app
```

Ez megnyitja a Slice Designer főablakát.

**Opcionális plugin — Relief Generator:**

A Slice Designer plugin nélkül is teljes értékű. Az opcionális Relief Generator plugin (parametrikus, procedurális modellgenerátor) külön telepíthető:

```
uv pip install -e plugins/relief_generator
```

Ezután az alkalmazás (újra)indításakor a "Mesh Import" fülön megjelenik egy "Forrás" legördülő, "STL fájl" mellett "Relief Generator" opcióval — l. 4.1 szakasz. A plugin öt, egymástól teljesen eltérő procedurális generátort kínál, egy belső "Generátor" legördülőn választva: **Automatikus hullám** (az eredeti, hullámhossz/amplitúdó/irány-alapú recept, opcionális amplitúdó-modulációval, koordináta-torzítással és több hullámforrással), **Voronoi-felszín**, **Holdkráter-felszín**, **Dűne-felszín** és **Faerezet-felszín** — mindegyiknek saját, csak rá vonatkozó paraméter-csoportjai vannak, amik csak az adott generátor kiválasztásakor jelennek meg.

A plugin eltávolítása: `uv pip uninstall slicedesigner-relief-generator`, vagy egyszerűen `uv sync` (ami a venv-et a lockfile szerinti, plugin nélküli állapotra állítja vissza, mivel a plugin telepítése nem a lockfile-on keresztül történik).

## 2. A felület áttekintése

A főablak három fő területre oszlik:

* **Bal oldali paraméter-panel** — itt állítod be a Mesh Import, Szeletelés (Slice), Dowel, Gap, Backplate, Numbering és Nesting paramétereit.
* **Középső 3D előnézet** — a betöltött modell, illetve a Futtatás után az összeállítás (szeletek, Dowel-ek, Spacer-ek, Backplate) forgatható, zoomolható megjelenítése. Egy-egy szelet a listából kiválasztva külön kiemelhető.
* **Alsó futtatás/export/állapot-panel** — a Futtatás gomb, a DXF Export gomb (kezdetben letiltva, amíg nincs sikeres Futtatás), és egy állapotnapló, amely a folyamat üzeneteit és a figyelmeztetéseket/hibákat írja ki.

## 3. Első projekt létrehozása

Ajánlott, a teljes pipeline sorrendjét követő menet:

1. **STL importálása** — lásd 4. szakasz. Az importált modell azonnal megjelenik a 3D előnézetben.
2. **Szeletelési beállítások megadása** — lásd 5. szakasz (kötelező: szeletvastagság).
3. *(opcionális)* **Dowel, Gap, Backplate bekapcsolása és paraméterezése** — lásd 6. szakasz. Legalább egyet (Dowel, Gap/Spacer vagy Backplate) be kell kapcsolni, különben a Futtatás konfigurációs hibával leáll.
4. **Numbering és Nesting paraméterek megadása** — lásd 6. szakasz; ezek mindig lefutnak, nincs be/kikapcsoló gombjuk.
5. **Futtatás** — a pipeline végigfut, az eredmény megjelenik a 3D előnézetben.
6. **DXF Export** — lásd 7. szakasz, önálló lépésként, a Futtatás után.
7. *(opcionális)* **Projekt mentése** — lásd 8. szakasz, hogy később folytathasd.

A teljes ajánlott munkafolyamatot (mit érdemes milyen sorrendben csinálni, milyen bemenetből milyen kimenet várható, CNC-szempontú korlátozások) a `WORKFLOW.md` részletezi.

## 4. STL importálása

A Slice Designer kizárólag **STL** formátumot fogad el — ASCII és bináris változatot egyaránt, automatikus felismeréssel.

Betöltéskor a rendszer:

* felépíti a háromszöghálót (akkor is, ha a fájl több, egymással nem összefüggő testet tartalmaz);
* kiszámítja a modell befoglaló dobozát (bounding box);
* ellenőrzi a geometria épségét (nem-vízzáró/nem-manifold geometria esetén **figyelmeztetést** ad, de nem blokkolja a betöltést);
* ellenőrzi, hogy a modell mérete plauzibilis-e (alapértelmezetten 1–3000 mm között bármely tengelyen) — ha nem, **figyelmeztetést** ad (tipikusan rossz mértékegységben exportált STL jele).

**Ami hibát okoz (a betöltés leáll):** a fájl nem található vagy nem olvasható; a tartalom sem ASCII, sem bináris STL-ként nem ismerhető fel; a geometria üres vagy nulla méretű.

### 4.1 Alternatív modellforrás: MeshSource pluginok (opcionális)

Ha van telepített MeshSource plugin (l. 1. szakasz, "Opcionális plugin"), a "Mesh Import" fül tetején megjelenik egy "Forrás" legördülő, "STL fájl" mellett a plugin nevével (pl. "Relief Generator").

Plugin kiválasztásakor a fájl-választó helyett a plugin paraméterei jelennek meg, a plugin által megadott formában. A Relief Generator esetén ez első lépésben egy "Generátor" legördülőt jelent (Automatikus hullám / Voronoi / Holdkráter / Dűne / Faerezet), majd a kiválasztott generátorra jellemző mezőket (a nem releváns mezők/mezőcsoportok automatikusan rejtve maradnak). A paraméterek kitöltése után a "Generálás" gomb elindítja a modell előállítását — ez a 3D előnézetben ugyanúgy megjelenik, mint egy importált STL. A generálás egy háttérszálon fut; amíg tart, a "Generálás" és a "Futtatás" gomb, valamint a "Fájl" menü letiltott.

A "Futtatás" gomb ekkor a legutóbb sikeresen generált modellt használja — ha még nem volt sikeres generálás, a Futtatás konfigurációs hibával leáll ("Nincs generált modell — előbb kattints a 'Generálás' gombra."). Paraméter módosítása után újra rá kell kattintani a "Generálás" gombra, hogy az új értékek érvényesüljenek.

**Fontos korlátozás:** egy plugin által generált modellt tartalmazó projekt jelenleg **nem menthető** — l. 8. szakasz.

## 5. Szeletelési beállítások

A szeletelés (Slice Engine) a Mesh keresztmetszeteit állítja elő a választott tengely mentén.

| Paraméter | Alapérték | Jelentés |
|---|---|---|
| Szeletelési tengely (`slice_axis`) | Z | X, Y vagy Z — melyik tengely mentén készülnek a keresztmetszetek. |
| Szeletvastagság (`slice_thickness_mm`) | *(kötelező megadni)* | Az egyes szeletek vastagsága, mm-ben. |
| Gap (`gap_mm`) | 0 | A szeletek között tervezett, egységes hézag mérete. Ha 0, nincs Spacer sem (lásd 6.2). |

A rendszer a szeletek számát úgy határozza meg, hogy a szeletek és a köztük lévő Gap-ek együtt pontosan a modell méretét adják ki a szeletelési tengely mentén. Ha ehhez a modellt egységesen (mindhárom tengelyen azonos arányban) kellene kicsinyíteni/nagyítani, ez legfeljebb 2%-os eltérésig (`max_scale_tolerance`) automatikusan megtörténik — efölött a Futtatás hibával leáll, jelezve, hogy a szeletvastagság/Gap kombináció nem illeszkedik a modellre.

## 6. Gap / Dowel / Backplate / Numbering / Nesting használata

**Fontos különbség:** a Dowel, a Gap (Spacer) és a Backplate **opcionális, be/kikapcsolható** funkciók (a paraméter-panelen egy-egy jelölőnégyzettel) — legalább egyet be kell kapcsolni. A Numbering és a Nesting ezzel szemben **mindig lefut**, nincs saját be/kikapcsolójuk — ezek paramétereit mindig ki kell tölteni.

A pipeline tényleges sorrendje: Szeletelés → Dowel → Gap → Backplate → Numbering → Nesting.

### 6.1 Dowel (illesztőcsap)

A Dowel a szeletek egymáshoz illesztését szolgáló, a modellen átfűzött rúd/pálca; a hozzá tartozó furat (Dowel Hole) automatikusan kimetszésre kerül minden érintett szeletből.

| Paraméter | Alapérték | Jelentés |
|---|---|---|
| Dowel átmérő (`dowel_diameter_mm`) | *(kötelező)* | A Dowel és a hozzá tartozó furatok átmérője. |
| Él-távolság (`min_edge_clearance_mm`) | fél Dowel-/Spacer-átmérő | Minimális biztonsági távolság a szelet külső szélétől. |
| Cél-darabszám régiónként (`dowel_count_per_region`) | 3 | Hány Dowel kerüljön egy összefüggő anyagrégióba (ennél több is lehet, ha egy szigetet csak így lehet lefedni). |
| Minimum régiónként (`min_dowels_per_region`) | 1 | Ennél kevesebb esetén a Futtatás hibával leáll. |
| Vak furat zárómérete (`blind_hole_cap_mm`) | szeletvastagság 30%-a | Ha egy furat nem megy át a teljes szeleten, mennyi anyag maradjon a záró oldalon. |
| Kézi pozíciók (`manual_dowel_positions`) | — | Tetszőleges számú, kézzel megadott, elsőbbséget élvező Dowel-pozíció. |

Az automatikus elhelyezés törekszik arra, hogy minden érintett szigetet lefedjen legalább egy Dowel, és a Dowel-eket a régió teljes kiterjedésén szétszórja (nem egyetlen sarokba/élre zsúfolja).

### 6.2 Gap (Spacer)

A Gap Engine a szeletek közötti hézagot (a Gap Engine spec szerint: `gap_mm`, lásd 5. szakasz) ténylegesen kitöltő, henger alakú Spacer-eket helyezi el.

| Paraméter | Alapérték | Jelentés |
|---|---|---|
| Spacer átmérő (`spacer_diameter_mm`) | *(kötelező)* | Ha Dowel is aktív, ennek meg kell egyeznie a Dowel paneljén megadott Spacer-átmérővel — a program ellenőrzi, és eltérés esetén konfigurációs hibát jelez. |
| Cél-darabszám réstenként (`spacer_count_per_gap`) | 3 | Hány Spacer kerüljön egy-egy metszet-régióba. |
| Minimum réstenként (`min_spacers_per_region`) | 1 | `0`-ra állítva explicit megengedi, hogy egy (pl. apró, Dowel-lel önmagában megtámasztott) régióban ne legyen Spacer. |

A rendszer előnyben részesíti a már meghatározott Dowel-pozíciókat (ott automatikusan furatos Spacer kerül a Dowel-re) — önálló Spacer-pozíciót csak a hiányzó darabszámig generál.

### 6.3 Backplate (hátlap)

A Backplate egy, a modell egyik oldalára illesztett hátlap, amelyhez a szeletek csapos kapcsolattal illeszkednek.

| Paraméter | Alapérték | Jelentés |
|---|---|---|
| Irány (`backplate_normal_axis`) | *(kötelező)* | Melyik oldalra kerüljön a Backplate (a szeletelési tengelytől eltérő 2 tengely egyike, előjellel). |
| Vastagság (`backplate_thickness_mm`) | *(kötelező)* | A Backplate saját vastagsága — egyben a csapok mélysége. |
| Csaphossz (`tab_length_mm`) | *(kötelező)* | Egy csap alapértelmezett hossza. |
| Sík-tolerancia (`backplate_plane_tolerance_mm`) | 0,1 mm | Mekkora eltérést fogad el a rendszer a "közös sík" felismerésekor. |
| Margó (`backplate_margin_mm`) | 0 | A Backplate körvonalának eltolása (pozitív: kifelé nagyobb, negatív: befelé kisebb). |
| Csap-köz (`tab_spacing_mm`) | 700 mm | Célzott távolság két csap között. |
| Csap-szegély (`tab_edge_margin_mm`) | = csaphossz | Egy csap kezdete az érintkező szakasz szélétől. |

A rendszer automatikusan felismeri, mely szigetek érintkeznek egy közös síkkal (ez lesz a Backplate síkja) — az ettől eltérő szigetek figyelmeztetéssel kimaradnak a Backplate-kapcsolódásból, a modell geometriája egyébként nem sérül. Egyedi szigetek kézzel is kizárhatók, illetve szigetenként felülbírálhatók a csap-paraméterek és -pozíciók.

### 6.4 Numbering (azonosítás)

A Numbering minden szeletet egyedi azonosítóval lát el (bevésve/kivágva a geometriájába), hogy az összeszerelés hibamentes legyen. Egyetlen sziget esetén az azonosító `"N"` (a szelet sorszáma); több sziget esetén `"N/Betű"` (A-tól kezdődő betűjel). Ha van Backplate, minden hozzá kapcsolódó szigethez a Backplate megfelelő, rejtett pozícióján is elhelyezésre kerül ugyanaz az azonosító.

| Paraméter | Alapérték | Jelentés |
|---|---|---|
| "Hátulsó" irány (`numbering_normal_axis`) | *(kötelező)* | Melyik oldalra kerüljön az azonosító (a Backplate-től függetlenül is beállítandó). |
| "Alsó" irány / betűrend (`numbering_direction_axis_sign`) | *(kötelező)* | A szigetek A/B/C sorrendjét és az azonosító "alsó" irányát határozza meg. |
| Célmagasság (`numbering_height_mm`) | *(kötelező)* | Az azonosító célzott, kényelmesen olvasható magassága. |
| Minimum magasság (`numbering_min_height_mm`) | célmagasság fele | Ha a cél nem fér el, ez az elfogadható minimum. |
| Margó (`numbering_margin_mm`) | célmagasság negyede | Az azonosító távolsága a legközelebbi élektől. |

Ha egy szigeten még a minimális méret sem fér el, az azonosító onnan kimarad — ez figyelmeztetés, nem hiba, a Futtatás nem áll le miatta.

### 6.5 Nesting (elrendezés)

A Nesting Engine az összes elkészült alkatrészt (szeletek, Backplate, Spacer-korongok) anyagonként a rendelkezésre álló lapokra rendezi, a lapnál nagyobb alkatrészeket szükség esetén toldva.

| Paraméter | Alapérték | Jelentés |
|---|---|---|
| Anyagok táblázata (`material_definitions`) | *(kötelező, legalább 1 sor)* | Minden sor: anyagazonosító, vastagság (mm), lap szélessége/magassága (mm), vágási rés — kerf (mm). |
| Szeletek anyaga (`slice_material_id`) | *(kötelező)* | Melyik anyaghoz tartoznak a szeletek — vastagságának egyeznie kell a szeletvastagsággal. |
| Backplate anyaga (`backplate_material_id`) | — | Kötelező, ha van Backplate; vastagságának egyeznie kell a Backplate vastagságával. |
| Spacer anyaga (`spacer_material_id`) | — | Kötelező, ha van Spacer. |
| Forgatás (`nesting_rotation_mode`) | Ortogonális | Nincs forgatás / csak 0°-90° / szabad szögű. |
| Toldás-jelölés magassága (`seam_marking_height_mm`) | *(kötelező)* | A toldott darabokra kerülő al-azonosító (pl. "3-1", "3-2") célzott magassága. |

**Fontos, reális elvárás:** a jelenlegi elrendezési algoritmus tengelyfüggő befoglaló téglalapokkal dolgozik (nem valódi kontúr szerinti, "true-shape" illesztéssel) — ez különösen erősen konkáv vagy egyenetlen alakú alkatrészeknél rosszabb lapkihasználtságot eredményezhet, mint egy ipari nesting szoftver. Ha egy alkatrész sehogy sem fér el egy lapon, a rendszer automatikusan, egyenes vágásvonallal toldja — a varrat pusztán vágásvonal, az összeillesztéshez szükséges kiegészítő geometriát (pl. saját illesztőfurat) nem ad hozzá, ez kézi, gyártás utáni lépés.

## 7. DXF export

A DXF Export **önálló lépés**, a Futtatástól elválasztva: csak a legutóbbi sikeres Futtatás eredményét exportálja, a Futtatás gomb újbóli megnyomása nélkül is tetszőlegesen sokszor, ha csak az export-paramétereket (pl. kimeneti könyvtárat) módosítod.

| Paraméter | Alapérték | Jelentés |
|---|---|---|
| Kimeneti könyvtár | *(kötelező kiválasztani)* | Hova kerüljenek a DXF fájlok. |
| DXF verzió (`dxf_version`) | R12 | A legszélesebb körben kompatibilis. |
| Vágási réteg neve/színe | CUT / piros | — |
| Gravírozási réteg neve/színe | ENGRAVE / kék | — |
| Fájlnév-minta (`output_filename_pattern`) | `{material_id}_sheet{sheet_number}` | `{material_id}` és `{sheet_number}` helyettesítőkkel. |

Minden anyaglaphoz külön DXF fájl készül, két réteggel: a **CUT** rétegen minden vágandó vonal (külső kontúr, furatok, csap/fészek-kivágás, toldási varratvonal), az **ENGRAVE** rétegen a Numbering-azonosítók és a toldási al-azonosítók.

## 8. Projekt mentése és visszatöltése

A `Fájl` menüben:

* **Projekt mentése...** — a teljes aktuális beállítás (minden paraméter-panel érték) elmentése egy `.json` fájlba.
* **Projekt megnyitása...** — egy korábban mentett `.json` visszatöltése; a paraméter-panel az összes widgetet a mentett értékekre állítja.

Ha egy megnyitott projektfájl felülír olyan beállítást, ami eltér attól, ami korábban a felületen volt, a program figyelmeztetést ír az állapotnaplóba ("Figyelem: N beállítás felülírva"). Ha a fájl szerkezetileg hibás vagy értelmezhetetlen, "Konfigurációs hiba" üzenettel jelzi, és a felület állapota változatlan marad.

**Fontos korlátozás:** ha az aktuális modell egy MeshSource plugin generálásából származik (l. 4.1 szakasz), a "Projekt mentése..." elutasítja a mentést, konfigurációs hiba üzenettel — ilyen projekt csak az aktuális munkamenetben használható. Ez ismert, dokumentált korlátozás (`RELEASE_NOTES.md` §4).

## 9. Beállítások

A Slice Designernek **nincs külön "Beállítások" képernyője.** Ehelyett a teljes paraméter-panel és futtatás-panel állapotát a program automatikusan elmenti bezáráskor, és visszatölti a következő induláskor — a `~/.slicedesigner/settings.json` fájlba, a projektmentéssel megegyező formátumban.

Ez azt jelenti, hogy nem kell minden indításkor újra beállítani a gyakran használt paramétereket (pl. a szokásos anyagtáblázatot) — a program mindig ott folytatja, ahol legutóbb abbahagytad. Ha ez a fájl sérült vagy hiányzik, a program figyelmeztetést naplóz, és a beépített alapértékekkel indul — sosem akadályozza az indulást vagy a bezárást.

## 10. Gyakori hibák / problémák

A Slice Designer minden hibát *fail-fast* elven jelez: érvénytelen vagy hiányos beállítás esetén megáll és pontosan megmondja, mi hiányzik vagy mi érvénytelen — nem próbál "kitalálni" egy valószínű, de nem kért eredményt.

| Helyzet | Tipikus ok | Teendő |
|---|---|---|
| "Legalább egy összeépítési kapcsolónak be kell kapcsolva lennie." | Sem Dowel, sem Gap/Spacer, sem Backplate nincs bekapcsolva. | Kapcsolj be legalább egyet a háromból. |
| Spacer-átmérő eltérés hiba a Dowel és a Gap panel között | A Dowel panel Spacer-átmérője és a Gap panel Spacer-átmérője nem egyezik. | Állítsd egyenlővé a két értéket. |
| A Futtatás a szeletelésnél áll le, skálázási hibával | A megadott szeletvastagság/Gap kombináció csak 2%-nál nagyobb torzítással illeszthető a modellre. | Módosítsd a szeletvastagságot vagy a Gap-et, hogy jobban illeszkedjen a modell méretéhez. |
| Dowel/Spacer "nem helyezhető el legalább N db" hiba | A régió túl kicsi a kért minimális darabszámhoz. | Csökkentsd a minimum darabszámot, vagy növeld a régió méretét (vastagabb szelet, más geometria). |
| "Nem található egyértelmű közös Backplate-sík" | A szigetek több, egymáshoz közel egyenlő méretű síkcsoportra oszlanak, egyik sem többségi. | Ellenőrizd a modell geometriáját, vagy zárj ki kézzel néhány szigetet (`non_backplate_islands`). |
| Egy azonosító vagy toldás-jelölés hiányzik a végeredményből | A hely nem elég nagy még a minimális méretnek sem — ez csak figyelmeztetés, a Futtatás lefut. | Nézd át az állapotnaplót; szükség esetén csökkentsd a célmagasságot vagy nagyítsd a szigetet. |
| "Az `output_filename_pattern` alapján két lap azonos fájlnevet kapna" | A fájlnév-minta nem tartalmazza a `{sheet_number}`-t, miközben egy anyagból több lap is készül. | Egészítsd ki a mintát `{sheet_number}`-rel. |
| Egység-plauzibilitási figyelmeztetés STL betöltésekor | A modell mérete kívül esik az 1–3000 mm tartományon — gyakran méter/hüvelyk egységben exportált fájl jele. | Ellenőrizd a forrás CAD-szoftver exportálási mértékegységét. |

Minden itt fel nem sorolt hiba is ugyanezt a mintát követi: az állapotnapló pontosan megnevezi az érintett paramétert és az érvényességi tartományát.
