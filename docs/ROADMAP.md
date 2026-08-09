# Roadmap

Státusz: Aktív
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-07-31
Utolsó módosítás: 2026-08-09
Kapcsolódó dokumentumok: [PROJECT_CONSTITUTION.md](PROJECT_CONSTITUTION.md), [AI_WORKFLOW.md](AI_WORKFLOW.md), [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md), [DOMAIN_MODEL.md](DOMAIN_MODEL.md)

## Cél

Ez a dokumentum meghatározza a Slice Designer fejlesztési fázisainak sorrendjét, célját és jelenlegi állapotát.

## Leírás

A ROADMAP nem backlog, nem feladatlista és nem specifikáció. A célja, hogy bármelyik AI vagy új fejlesztő azonnal lássa, hol tart a projekt, mely fázisok készültek el, mi a következő lépés, és mely dokumentumok tekinthetők lezártnak. A ROADMAP kizárólag a fejlesztési folyamatot írja le, technikai megoldásokat nem.

> **Megjegyzés (2026-08-01):** A Phase 0 korábbi ✅ Approved jelölése tévesen került rögzítésre — a kilépési feltétel ("A projekt dokumentációja önmagában értelmezhető") ténylegesen nem teljesült, mivel több Phase 0-hoz tartozó dokumentum vázlat állapotban maradt. A Phase 0 ezért 🟡 In Progress-re, a rá épülő Phase 1 pedig ⬜ Not Started-ra lett visszaminősítve.
>
> **Megjegyzés (2026-08-01, folytatás):** A Phase 0-hoz tartozó mind a hét dokumentum (PROJECT_VISION, ENGINEERING_PRINCIPLES, ARCHITECTURE, PROJECT_STRUCTURE, CODING_STANDARDS, AI_WORKFLOW, PROMPT_STANDARD) érdemi tartalommal elkészült és a projektgazda jóváhagyta — a kilépési feltétel teljesült. A Phase 0 ezért ✅ Approved-ra, a Phase 1 pedig 🟡 In Progress-re került, mivel a DOMAIN_MODEL.md már tartalmaz érdemi munkát (a Numbering-kivétel révén).
>
> **Megjegyzés (2026-08-01, folytatás 2):** A Phase 1 (Domain Design) kilépési feltétele teljesült — a DOMAIN_MODEL.md tartalmazza a koordinátarendszert, a mértékegységeket, valamint mind a 14 fogalom attribútum-szintű kiegészítését; a projektgazda a Claude Code általi végrehajtás után review-olta és jóváhagyta. A Phase 1 ezért ✅ Approved-ra, a Phase 2 (Functional Specifications) pedig 🟡 In Progress-re került.
>
> **Megjegyzés (2026-08-01, folytatás 3):** A Phase 2 (Functional Specifications) mind a nyolc tervezett specifikációja (Mesh Import, Slice Engine, Gap System, Dowel System, Backplate, Numbering, Nesting, DXF Export) elkészült és a projektgazda jóváhagyta — a kilépési feltétel teljesült. A munka során több, korábban elfogadott specifikáció és architekturális döntés is felülvizsgálatra és pontosításra került (ADR-0003–0005), amikor a részletes kidolgozás új, korábban fel nem ismert függőségeket vagy ellentmondásokat tárt fel. A Phase 2 ezért ✅ Approved-ra, a Phase 3 (Architecture Freeze) pedig 🟡 In Progress-re került.
>
> **Megjegyzés (2026-08-01, folytatás 4):** A Phase 3 (Architecture Freeze) kilépési feltétele teljesült — az architektúra és a nyolc specifikáció rendszerezett áttekintése megtörtént (ARCHITECTURE.md belső konzisztencia, DOMAIN_MODEL.md kereszthivatkozások, szétszórt backlog-bejegyzések rendezése, a teljes pipeline adatszerződéseinek végigfuttatása), a feltárt hiányosságok javításra kerültek, és a projektgazda jóváhagyta. A Phase 3 ezért ✅ Approved-ra, a Phase 4 (Implementation) pedig 🟡 In Progress-re került.
>
> **Megjegyzés (2026-08-03, folytatás 5):** A Phase 4 (Implementation) mind a nyolc, ROADMAP Phase 2-ben rögzített engine-je (Mesh Import, Slice Engine, Dowel System, Gap System, Backplate, Numbering, Nesting, DXF Export) elkészült, review-n átment, és a projektgazda jóváhagyta (89/89 automatizált teszt, `PYTHONHASHSEED=0 uv run pytest`). A munka során két, a specifikációk által Phase 4-re hagyott, keresztmetsző implementációs döntés (kontúr körüljárási irány, ADR-0007; Nesting Engine csomagolási algoritmus, ADR-0008) ADR-ben rögzítésre került. A Phase 4 ezért ✅ Approved-ra, a Phase 5 (Integration) pedig 🟡 In Progress-re került.
>
> **Megjegyzés (2026-08-04, folytatás 6):** A Phase 5 (Integration) eredeti öt tétele (modulok összekapcsolása, GUI, teljes workflow, projektmentés, beállítások) elkészült. Ezeken felül a GUI-t lezáró négy kiegészítő tétel (automatikus Mesh-előnézet, Dowel/Spacer/Backplate 3D-megjelenítés, szeletenkénti kiemelés) és két, élő tesztelés során feltárt és megvalósított javítás (Dowel automatikus pozíciókeresés térbeli szórása, Numbering Slice-oldali szigorúságának figyelmeztetés-alapúra enyhítése) is a fázis részeként valósult meg. A projektgazda jóváhagyta. A Phase 5 ezért ✅ Approved-ra, a Phase 6 (Release Candidate) pedig 🟡 In Progress-re került, első tételeként a DXF export Futtatásról való leválasztásával (önálló interakció, Döntési javaslat és Impact Analysis alatt).
>
> **Megjegyzés (2026-08-04, folytatás 7):** A Phase 6 első tétele (DXF export leválasztása a Futtatásról) a teljes munkafolyamaton átment — Döntési javaslat, Hatásvizsgálat, projektgazdai jóváhagyás, majd ADR-0009 és az ARCHITECTURE.md módosítása, ezt követően a Claude Code általi implementáció (200/200 automatizált teszt) —, és a projektgazda élő teszteléssel is megerősítette. A Phase 6 többi tétele (végső tesztelés, optimalizálás, dokumentáció, példaprojektek) még nyitott, a fázis ezért továbbra is 🟡 In Progress.
>
> **Megjegyzés (2026-08-04, folytatás 8):** A Phase 6 "optimalizálás" tétele eredetileg általános teljesítmény-átvizsgálásként szerepelt; a projektgazda pontosítása alapján a tétel elsődleges és jelenleg egyetlen tartalma a Dowel automatikus pozíciókeresés teljesítményproblémájának javítása (korábban a BACKLOG.md 2. tételeként nyilvántartva, élő tesztelés során feltárt lassúság miatt). Mivel a javítás érdemben befolyásolhatja a rendszer futásidejét és viselkedését, a projektgazda döntése alapján a "végső tesztelés" tétel ez után következik a Feladata-listán, nem előtte. A BACKLOG.md 2. tétele ezzel a ROADMAP Phase 6 hatókörébe kerül és törlésre kerül a Backlogból.
>
> **Megjegyzés (2026-08-04, folytatás 9):** A Phase 6 "optimalizálás" tétele (Dowel automatikus pozíciókeresés teljesítmény-javítása) lezárult. A megoldás: (1) a rácspontonkénti kör-poligon építés (`buffer().within()`) cseréje régiónkénti, egyszeri Minkowski-erózió-előszámításra és olcsó pont-tartalmazás tesztre, egy explicit, dokumentált tangencia-tolerancia (`_EROSION_TANGENCY_EPSILON_MM`) bevezetésével a karakterizációs teszt bit-pontos megőrzéséhez; (2) a `DOWEL_SYSTEM_SPEC.md` 6. szakaszának kiegészítése egy teljes sziget-lefedettségi szabállyal — a legszűkösebb (legkevesebb érvényes jelölttel rendelkező) szigetek elsőbbséget élveznek a lefedésben, felső korlát nélkül, majd a fennmaradó helyek a célszámig (`dowel_count_per_region`) sűrűsödnek; a soha le nem fedhető, illetve a szűkösségi verseny miatt kiszorult szigetek külön, megkülönböztetett figyelmeztetést kapnak (nem hibát); (3) elágazás-detektálással a drágább, szigetenkénti számítás csak ott fut, ahol ténylegesen szükséges (elágazás-mentes régióban olcsó, poligon-teszt nélküli szűréssel helyettesítve). A Claude Code általi implementáció (203/203 automatizált teszt, ebből 3 új a lefedettségi logikára) és a projektgazda élő tesztelése egyaránt megerősítette a működést.
>
> **Megjegyzés (2026-08-08, folytatás 10):** Egy rendkívül hosszú, egyetlen munkamenetben lezajlott "végső tesztelés" valódi felhasználói modelleken (elsősorban "Wobbly Toad" és "face-in-the-brick-wall" STL) végzett élő tesztelése számos valódi hibát tárt fel és javított ki a Slice/Numbering/Gap/Backplate Engine-ekben — a részletes felsorolás a Phase 6 szakaszban található. Egy tétel nyitva maradt: a Backplate-feliratok karakter-szintű tükröződése (`numbering_engine.py::_glyph_point_rect()`), amely ugyanabba a hibaosztályba tartozik, mint a már javított szelet-oldali `_glyph_to_local()`, de önálló, korábban sosem javított duplikátum. A gyökérok azonosítva, a javítás megtervezve és sandbox-környezetben vizuálisan ellenőrizve, de Claude Code-nak még nem lett átadva végrehajtásra — ez az azonnali következő lépés egy új beszélgetésben. Emellett a szelet-kontúr korábbi, a projektgazda által soha nem megerősített "nézőpont" magyarázata (miszerint a DXF-en látott tükröződés csak a lap másik oldaláról nézés természetes következménye) validálatlan marad, és a Backplate-felirat hibájának fényében újra, bizonyítékkal (nem érveléssel) megvizsgálandó. A Phase 6 állapota emiatt továbbra is 🟡 In Progress.
>
> **Megjegyzés (2026-08-08, folytatás 11 — a "NYITOTT" tételek gyökérok-javítása):** Egy célzott, kizárólag erre a témára fókuszáló audit (nem egy általános "rendszerszintű" átvizsgálás) mérve és levezetve (nem feltételezve) azonosította a szelet-kontúr és a Backplate (kontúr ÉS felirat) tükröződésének közös gyökérokát: a `slice_engine.py::_TO_2D_ROTATION` a "folytatás 7" bejegyzésben leírt korábbi javítás során SZÁNDÉKOSAN, dokumentáltan csak forgatást (determináns +1) tartalmazott, tükrözés nélkül — ez maga volt a hiba, nem a "nézőpont" (lap másik oldaláról nézés). Egy diagnosztikai script és a projektgazda saját, korábbi (javítás előtti) kódverziója egyaránt igazolta, hogy a helyes vetítéshez pontosan egy tükrözés szükséges. Emellett az audit egy **korrekciót** is rögzít a "folytatás 10" bejegyzés (illetve az azt megelőző "rendszerszintű audit") állításával szemben: az akkori audit azt állította, hogy a glyph-tükrözési hibaosztálynak **kizárólag két** előfordulása van (`numbering_engine.py::_glyph_to_local`, `numbering_engine.py::_glyph_point_rect`) — ez tévedés volt. A jelen audit egy **harmadik, korábban fel nem ismert előfordulást** is talált: `nesting_engine.py::_glyph_point_rect()` (a toldási/seam al-azonosítók rajzolásánál), amelynek `non-upright` ága szintén determináns -1 (tükrözött) volt — ez azért maradhatott korábban észrevétlen, mert a meglévő tesztek csak a szöveg illeszkedését ellenőrizték, nem a tükrözöttségét. A gyökérok-javítás (ADR-0010) részeként: (1) a `_TO_2D_ROTATION` mindhárom mátrixa szándékos, egységes tükrözést kapott; (2) a korábban egymástól függetlenül duplikált `_SLICE_AXIS_CONTOUR_ORDER`/`_NORMAL_AXIS_WORLD` táblák egyetlen, megosztott forrásra kerültek (`slice_engine.py`, illetve `backplate_engine.py`); (3) a `backplate_engine.py::_build_backplate_shape_from_mesh()` mostantól ténylegesen felhasználja a `backplate_normal_axis` előjelét (korábban explicit módon eldobta — `_sign`, nem használt változó), ugyanezt az előjelet alkalmazva a fészek-kivágásnál és a Backplate-oldali azonosító horgonypont-számításánál is (`apply_numbering_to_backplate()` emiatt új, kötelező `backplate_normal_axis` paramétert kapott); (4) a Backplate-oldali és a most felismert seam-oldali `_glyph_point_rect()` mindkettő javítva, determináns +1-re. A Claude Code általi implementáció (229/229 automatizált teszt, ebből 5 új a determináns-/tükrözés-regresszióra) megtörtént. Ezzel a Phase 6 "NYITOTT" szakaszának mindkét tétele (1. a szelet-kontúr "nézőpont" kérdése — cáfolva, a valódi gyökérok azonosítva és javítva; 2. a Backplate-felirat tükröződése — javítva, plusz egy harmadik, korábban fel nem ismert előfordulás is javítva) implementációs szempontból lezártnak tekinthető, a projektgazdai élő tesztelés (a DXF export puszta vágási vonalán és feliratain, a fizikai modellel összevetve) megerősítésére várva — ezt a projektgazda a review lépésben erősíti meg. A Phase 6 állapota emiatt továbbra is 🟡 In Progress (a "dokumentáció" és "példaprojektek" tételek is nyitottak maradnak).

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

Állapot: ✅ Approved

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

Állapot: ✅ Approved

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

Állapot: ✅ Approved

Minden fő funkció külön specifikációban készül, például:

* Mesh Import
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

Állapot: ✅ Approved

Feladata:

* dokumentáció review
* architektúra véglegesítése
* hiányosságok javítása

Új funkció nem kerülhet be.

Kilépési feltétel: Az architektúra Approved állapotú.

---

### Phase 4 – Implementation

Állapot: ✅ Approved

A fejlesztés kizárólag jóváhagyott specifikáció alapján történt. Mind a nyolc engine (Mesh Import, Slice Engine, Dowel System, Gap System, Backplate, Numbering, Nesting, DXF Export) elkészült, automatizált teszttel (89 teszt) lefedve.

---

### Phase 5 – Integration

Állapot: ✅ Approved

Feladata:

* modulok összekapcsolása
* GUI
* teljes workflow
* projektmentés
* beállítások

Megjegyzés: az eredeti öt tételen felül a GUI-t lezáró négy kiegészítő tétel (automatikus Mesh-előnézet, Dowel/Spacer/Backplate 3D-megjelenítés, szeletenkénti kiemelés) és két, élő teszteléskor feltárt javítás (Dowel automatikus pozíciókeresés térbeli szórása, Numbering figyelmeztetés-alapú kezelése) is a fázis részeként valósult meg.

---

### Phase 6 – Release Candidate

Állapot: 🟡 In Progress

Feladata:

* ~~DXF export leválasztása a Futtatásról (önálló interakció)~~ — kész (ADR-0009)
* ~~optimalizálás — Dowel automatikus pozíciókeresés teljesítmény-javítása (1. kör)~~ — kész
* ~~optimalizálás — 2. kör (Numbering, Dowel, GUI-előnézet szálkezelés)~~ — kész, ld. lentebb
* ~~végső tesztelés~~ — kész, ld. lentebb
* dokumentáció
* példaprojektek

#### Végső tesztelés — 2026-08-07-ig lezárt tételek

Egyetlen, hosszú munkamenetben, valódi felhasználói modelleken (elsősorban "Wobbly Toad" és "face-in-the-brick-wall" STL) végzett élő tesztelés az alábbi, ténylegesen kijavított és Claude Code által végrehajtott hibákat tárta fel:

**Slice Engine**

* X/Y tengelyű szeletelésnél a `trimesh` belső, dokumentálatlan vetítési konvenciója (mátrix-elemzéssel és két független, aszimmetrikus doboz-teszttel igazoltan) eltért attól, amit a kód (`_SLICE_AXIS_CONTOUR_ORDER`) feltételezett — ez egy önmagában, függetlenül bizonyított és javított hiba, explicit, kézzel megkonstruált `_TO_2D_ROTATION` mátrixokkal.
* **Fontos, pontosan rögzítendő korlát:** ez a javítás **nem** oldotta meg a projektgazda eredeti, élő tesztelésnél jelentett panaszát, hogy a DXF-en a szelet-kontúr tükrözve jelenik meg — a panasz a javítás után is fennállt. Az akkori magyarázat (a Szoftverarchitekt részéről: "a lap másik oldaláról nézed") **soha nem lett bizonyítva** — a projektgazda csak elfogadta, mert akkor nem tartotta elég fontosnak a további vitát, nem azért, mert megalapozottnak találta. Ez tehát **nem lezárt tétel**, ld. a NYITOTT szakaszt.

**Numbering Engine (szelet-oldal)**

* `_glyph_to_local()`: karakter-szintű tükröződés bizonyos tengely/előjel-kombinációknál — javítva egy, az indextől/előjeltől teljesen független, vizuálisan ellenőrzött újratervezéssel.
* `_search_best_anchor()`: a fenti javítás után a keresés gyors útja gyakorlatilag mindig a teljes rácsos bejárásra esett vissza — visszaállítva a teljesítmény négy gyors sarok-jelölt próbájával (~186×-os `_fits()`-hívás csökkenés egy valós teszt-fixture-nél).

**Gap Engine**

* `region_id` a teljes Slice Set-en át folyamatosan növekedett, nem Gap-enként — a hibaüzenetek megtalálhatatlan régiókra mutattak; javítva Gap-enkénti újraindítással.
* `min_spacers_per_region` csak `≥1` lehetett, ezért egy apró, fizikailag Spacer-re alkalmatlan régió leállította a teljes feldolgozást — bővítve `0`-ra (explicit, tudatos beállítás, figyelmeztetéssel).

**Backplate Engine — a legnagyobb terjedelmű téma**

* A közös Backplate-sík felismerése régen egyetlen kilógó szigetet is hibaként kezelt — lecserélve automatikus, lánc-alapú klaszterezésre (domináns csoport + szigorú többségi biztonsági feltétel); a klaszterezésen kívül eső szigetek automatikusan, figyelmeztetéssel kizárásra kerülnek.
* `usable_length ≤ 0` egy érintkező szakaszon szintén hiba volt — figyelmeztetéssé enyhítve (a sziget más szakaszain/más szigeteken a feldolgozás folytatódik).
* A `Backplate` objektum nem tárolta a közös sík world-koordinátáját — ez okozta a 3D előnézet hibás pozícióját (a klaszterezés bevezetése után egy korábbi, közelítő GUI-számítás elavulttá vált). Megoldás: új `Backplate.common_plane_mm` mező, a GUI a közelítés helyett közvetlenül ezt olvassa.
* A Backplate alakja eredetileg a teljes 3D modell nyers Mesh-ből vetített sziluettje volt — ez (a) fizikailag túl nagy volt (a teljes test árnyéka, nem a tényleges érintkezési terület), és (b) a nyers, újra nem bázisolt Mesh-koordinátákat használta, ami inkonzisztens volt a pipeline többi részének `position_mm`-alapú rendszerével (ez okozta, hogy a Backplate az összeállítás mellett, rossz pozícióban jelent meg a DXF exportban). Két lépésben javítva: először a már meglévő, domináns-klaszterbeli érintkező szakaszokból épített téglalap-unióra (helyes pozíció, de lépcsőzetes alak), majd — a projektgazda kifejezett kérésére, mert a szeletelés is a modell tényleges geometriájából dolgozik — egy valódi, a Slice Engine-nel megegyezően skálázott Mesh térbeli Boole-metszetére (`manifold3d` új függőség, ADR-0006 kiegészítve). A metszetnek szükségszerűen egy tűrés-sávot kell használnia (nem nulla-vastagságú síkot), mert egy enyhén nem-sík felületnél (pl. kerekített talp) egy egzakt metszet szinte semmit nem fogna ki — ezt a valódi modellen empirikusan igazoltuk.

**Numbering Engine (Backplate-oldal)**

* `apply_numbering_to_backplate()` saját, önálló `axis_min`-számítást végzett a nyers Mesh-ből, ami a Backplate `position_mm`-alapú koordinátarendszerével nem volt kompatibilis (a Backplate-javítás előtt ez rejtve maradt, mert a Backplate saját, akkor még szintén hibás sziluettje véletlenül konzisztens volt vele) — javítva, `axis_min` elhagyásával.

#### Végső tesztelés — NYITOTT, folyamatban lévő tételek

**1. Validálatlan feltételezés a szelet-kontúr "nézőpont" magyarázatáról — újra megvizsgálandó, NEM tekinthető lezártnak.**

> **2026-08-08-i frissítés ("folytatás 11"):** a "nézőpont" magyarázat cáfolva — a valódi gyökérok a `_TO_2D_ROTATION` szándékos, de hibás "csak forgatás" tervezési elve volt (ld. ADR-0010). A javítás megtörtént; a projektgazdai élő tesztelés (a puszta vágási vonalon, feliratok nélkül) megerősítésére vár.

A `_TO_2D_ROTATION` javítása után a projektgazda élő tesztelésnél továbbra is tükrözöttnek jelezte a szelet-kontúrt a DXF-ben. A Szoftverarchitekt akkor azt állította, hogy ez nem hiba, hanem a lapos alkatrész másik oldaláról nézés természetes következménye — ezt a projektgazda **elfogadta, de kifejezetten nem megerősítésként**, hanem mert akkor nem tartotta elég fontosnak, hogy tovább vitatkozzon róla. **Ez az állítás soha nem lett független bizonyítékkal alátámasztva** (szemben pl. a `_TO_2D_ROTATION`-nal, amit mátrix-elemzés és empirikus teszt is igazolt). Mivel a Backplate-nél egy hasonló, "nézőpont kérdésének" beállított jelenség a végén egy valódi, javítatlan hibának (`_glyph_point_rect`) bizonyult, ez a korábbi magyarázat **gyanús, és újra, ezúttal bizonyítékkal (nem érveléssel) megvizsgálandó** — nem szabad lezártként kezelni, amíg ez meg nem történik.

**2. Numbering Engine — Backplate-feliratok karakter-szintű tükröződése.**

> **2026-08-08-i frissítés ("folytatás 11"):** javítva (ld. ADR-0010) — az alábbi tervezett javítás változatlan formában végrehajtásra került, és emellett egy **harmadik, korábban fel nem ismert előfordulás** is javításra került: `nesting_engine.py::_glyph_point_rect()` (seam-oldal) — ld. az alábbi "Rendszerszintű audit" bekezdéshez fűzött korrekciót. A projektgazdai élő tesztelés megerősítésére vár.

Élő tesztelés (a `face-in-the-brick-wall` modellen, mert az kellően aszimmetrikus/jellegzetes ahhoz, hogy a tükröződés egyértelműen megállapítható legyen) feltárta, hogy a Backplate-en elhelyezett azonosítók (pl. "2/A") karakter-szinten tükrözve jelennek meg — ugyanaz a hibaosztály, mint amit a szelet-oldali `_glyph_to_local()`-nál már javítottunk, de egy **külön, önálló, korábban sosem javított duplikátumban**: `numbering_engine.py::_glyph_point_rect()`.

**A gyökérok pontosan azonosítva, a javítás megtervezve és — egy Szoftverarchitekt-oldali, ideiglenes sandbox-másolaton — vizuálisan ellenőrizve (a hibás és javított verzió egymás mellett kirajzolva, valódi karakter-adatokkal), DE MÉG NEM lett átadva Claude Code-nak végrehajtásra.** Ez az azonnali következő lépés egy új beszélgetésben.

A hibás kód (`upright=True` ág):

```python
def _glyph_point_rect(gx, gy, upright, anchor_x, anchor_y):
    if upright:
        return (anchor_x + gx, anchor_y - gy)  # <- tükrözés, det=-1
    return (anchor_x + gy, anchor_y - gx)      # <- ez az ág helyes, det=+1
```

A javítás (ellenőrizve, det=+1, a karakterek helyesen olvashatók):

```python
def _glyph_point_rect(gx, gy, upright, anchor_x, anchor_y, height_mm):
    if upright:
        return (anchor_x + gx, anchor_y - height_mm + gy)
    return (anchor_x + gy, anchor_y - gx)
```

(A `height_mm` új paraméter, a hívó `_build_text_strokes_rect()`-ből egyenesen továbbadható, mivel az már megkapja.)

**Rendszerszintű audit is megtörtént** (nem csak ez az egy hely lett ellenőrizve): a teljes `src/slicedesigner/engines/` és `src/slicedesigner/gui/` alatt átnézve, kizárólag ez a két függvény (`_glyph_to_local`, `_glyph_point_rect`) tartalmazott "horgonypont + glyph-eltolás" jellegű, kézzel írt koordináta-számítást — minden más, koordinátát összeállító függvény vagy a már bizonyítottan helyes, közös `_AXIS_MAPPING`/`_TO_2D_ROTATION` konvenciót használja, vagy egyszerű, számítás nélküli index-hozzárendelést végez.
>
> **Korrekció (2026-08-08, "folytatás 11"):** ez az állítás TÉVES volt. Egy későbbi, célzott audit egy **harmadik, önálló előfordulást** is talált: `nesting_engine.py::_glyph_point_rect()` (a toldási/seam al-azonosítók rajzolásánál), amelynek `non-upright` ága szintén determináns -1 (tükrözött) volt. Ez azért maradhatott észrevétlen a fenti "rendszerszintű audit" során is, mert a meglévő tesztek csak a szöveg illeszkedését ("elfér-e a rendelkezésre álló területen"), nem a tükrözöttségét ellenőrizték — ez a hibaosztály tehát vizuális/geometriai ellenőrzés nélkül, pusztán kód-átvizsgálással nem volt megbízhatóan kiszűrhető. Javítva, ld. ADR-0010.

**Nyitva maradó kérdés, amit élő teszteléssel kell megerősíteni, miután a fenti javítás megtörtént:** a projektgazda a Backplate **kontúrját** (nem csak a feliratait) is tükrözöttnek jelezte. A Szoftverarchitekt minden elérhető ellenőrzése (szintetikus aszimmetrikus teszt-alakzat a tényleges vetítési képlettel; a teljes lánc valódi modellen történő összevetése a szeletek saját adataival) a kontúrt helyesnek mutatta — lehetséges, hogy a "tükrözöttnek tűnés" részben vagy egészben a fenti, ténylegesen tükrözött feliratból eredt. **Ezt a fenti javítás után, a feliratoktól függetlenül (pl. a puszta vágási vonalat nézve), élőben külön meg kell erősíteni.**

> **Élő megerősítés (2026-08-08):** A `render_geometry.py::_AXIS_MAPPING`/`_backplate_third_axis_sign` GUI-oldali szinkronizálása, majd a `_backplate_third_axis_sign()` levezetésében talált hibás nézőpont-feltevés javítása (a teljes visszatérési érték globális előjel-megfordítása, ld. ADR-0010 "Frissítés (2026-08-08)" szakasza) után a projektgazda mindhárom szeletelési tengelyen (X, Y, Z) elvégezte az élő tesztelést, és megerősítette: a szelet-kontúr, a Backplate-kontúr és a Backplate-felirat egyaránt helyesen, tükrözés nélkül jelenik meg — mind a 3D előnézetben, mind az exportált DXF-en. A fentebb (a Phase 6 "NYITOTT" szakasz 1. tételében) leírt, korábban validálatlan "nézőpont" magyarázat ezzel okafogyottá vált: nem azért zárul le a kérdés, mert az az érvelés helyesnek bizonyult volna, hanem mert a tényleges gyökérokot (a Slice Engine vetítéséből hiányzó, majd az ADR-0010-zel bevezetett szándékos tükrözés, és annak Backplate-re és a GUI-ra kiterjedő teljes utókövetése) azonosítottuk és javítottuk. A "Végső tesztelés" tétel e vonatkozásban — a teljes tükrözési hibaosztály (szelet-kontúr, Backplate-kontúr, Backplate-felirat) — lezárva; a Phase 6 egyéb, még hátralévő tételei (dokumentáció, példaprojektek) miatt maga a Phase 6 továbbra is 🟡 In Progress marad.

#### Végső tesztelés — 2026-08-09-ig lezárt kiegészítő tételek

* **ADR-0010 tükröződés-javítás élő tesztelése megerősítve** — a "folytatás 11" bejegyzésben leírt gyökérok-javítást a projektgazda élesben, fizikai modellel összevetve megerősítette. Ezzel a szelet-kontúr és a Backplate (kontúr és felirat) tükröződési hibaosztálya véglegesen lezárva.
* **Backplate-csapok külön alkatrészként jelentek meg a DXF exportban, a hozzájuk tartozó szelet helyett/mellett** — gyökérok: a `backplate_engine.py::_apply_tab_geometry()` a csap-téglalapot a sziget tényleges (a `backplate_plane_tolerance_mm` tűrésen belül ingadozó) pereméhez képest pontatlanul illesztette, ami `unary_union()` után `MultiPolygon`-t (két külön szigetet) eredményezett nem tökéletesen sík érintkezési határnál. Javítás: a csap belső élének garantált átfedéssel történő illesztése (`_TAB_OVERLAP_SAFETY_EPSILON_MM`, a Dowel Engine tolerancia-mintájára). 236/236 automatizált teszt, élő teszttel megerősítve.
* **A Spacer-korongok közepén nem volt furat a rajtuk átmenő Dowel számára** — ez dokumentációs hiány is volt, nem csak implementációs: a `GAP_SYSTEM_SPEC.md`/`DOMAIN_MODEL.md` nem tartalmazott furat-attribútumot a Spacer-en. Javítás: a Dowel-re fűzött Spacer-ek új, opcionális `dowel_diameter_mm` attribútumot kapnak (a rajtuk átmenő Dowel átmérőjével), amiből a Nesting Engine a korong furatát vágja; az önálló (nem Dowel-alapú) Spacer-ek tömörek maradnak. `GAP_SYSTEM_SPEC.md`, `DOMAIN_MODEL.md`, `NESTING_SPEC.md` kiegészítve. 240/240 automatizált teszt, élő teszttel megerősítve.

#### Optimalizálás — 2. kör (2026-08-09)

Élő tesztelés közben jelzett, jelentős futásidő-panasz nyomán szisztematikus, szakaszonkénti időmérési diagnosztika (nem találgatás) tárta fel a tényleges szűk keresztmetszeteket — ezek egyike sem esett egybe az eredetileg gyanított pontokkal (Gap/Backplate Engine), ami alátámasztja a mérés-előbb-javítás-utóbb elvet:

* **Numbering Engine** — a kimerítő fallback-keresés (amikor a gyors sarok-illesztés nem talál pozíciót) sorrend-vak, teljes rácsot bejáró implementációja akár egyszerű modelleknél is a teljes futásidő 80%-át tette ki. Javítás: távolság szerint táguló, korai megállásos bejárás (`_iter_grid_points_by_distance()`), bizonyítottan azonos kimenettel. ~53× gyorsulás a mért forgatókönyvön.
* **Dowel Engine** — az automatikus jelölt-generálás (`_longest_run()`) rácspontonként, Python-szinten, minden szeletre egyenként tesztelt — nagy szeletszámnál ez dominált (88,7%, 19 s). Javítás: `shapely.contains_xy()`/NumPy-alapú vektorizálás, bizonyítottan azonos kimenettel (referencia-implementációval bitre pontosan összevetve). ~28× gyorsulás.
* **GUI-előnézet (ADR-0011, ADR-0012)** — a 3D-előnézet geometria-építése a fő szálon, szinkron futott, UI-fagyasztó módon — mind a Futtatás utáni első megjelenítésnél, mind a kiemelés-/nézet-váltásnál. Javítás: a geometria-építés (tiszta, Qt-független `render_geometry.py`-hívások) háttérszálra vitele; a kiemelés-/nézet-váltásnál egy könnyű generáció-számláló védi ki az elavult eredmények felülírását, publikus jelzés-elkülönítéssel a `MainWindow`-tól (elkerülve egy Futtatás-közbeni interakcióból eredő korrektségi hibát).

Mindhárom élő teszttel megerősítve. Összesített hatás a diagnosztikai forgatókönyveken: "Egyszerű, TIPIKUS" 1911 ms → 368 ms; "Komplex, TIPIKUS" 21 462 ms → 3299 ms.

---

## Általános szabályok

* Egyszerre csak egy fázis lehet aktív.
* A következő fázis csak az előző lezárása után kezdhető meg.
* Locked állapotú fázis kizárólag Architecture Decision Record alapján módosítható.
* A ROADMAP a projekt fejlesztési sorrendjének hivatalos nyilvántartása.
