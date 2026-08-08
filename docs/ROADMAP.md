# Roadmap

Státusz: Aktív
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-07-31
Utolsó módosítás: 2026-08-08
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
* ~~optimalizálás — Dowel automatikus pozíciókeresés teljesítmény-javítása~~ — kész
* végső tesztelés — 🟡 folyamatban, ld. lentebb (lezárt és nyitott tételek)
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

A `_TO_2D_ROTATION` javítása után a projektgazda élő tesztelésnél továbbra is tükrözöttnek jelezte a szelet-kontúrt a DXF-ben. A Szoftverarchitekt akkor azt állította, hogy ez nem hiba, hanem a lapos alkatrész másik oldaláról nézés természetes következménye — ezt a projektgazda **elfogadta, de kifejezetten nem megerősítésként**, hanem mert akkor nem tartotta elég fontosnak, hogy tovább vitatkozzon róla. **Ez az állítás soha nem lett független bizonyítékkal alátámasztva** (szemben pl. a `_TO_2D_ROTATION`-nal, amit mátrix-elemzés és empirikus teszt is igazolt). Mivel a Backplate-nél egy hasonló, "nézőpont kérdésének" beállított jelenség a végén egy valódi, javítatlan hibának (`_glyph_point_rect`) bizonyult, ez a korábbi magyarázat **gyanús, és újra, ezúttal bizonyítékkal (nem érveléssel) megvizsgálandó** — nem szabad lezártként kezelni, amíg ez meg nem történik.

**2. Numbering Engine — Backplate-feliratok karakter-szintű tükröződése.**

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

**Nyitva maradó kérdés, amit élő teszteléssel kell megerősíteni, miután a fenti javítás megtörtént:** a projektgazda a Backplate **kontúrját** (nem csak a feliratait) is tükrözöttnek jelezte. A Szoftverarchitekt minden elérhető ellenőrzése (szintetikus aszimmetrikus teszt-alakzat a tényleges vetítési képlettel; a teljes lánc valódi modellen történő összevetése a szeletek saját adataival) a kontúrt helyesnek mutatta — lehetséges, hogy a "tükrözöttnek tűnés" részben vagy egészben a fenti, ténylegesen tükrözött feliratból eredt. **Ezt a fenti javítás után, a feliratoktól függetlenül (pl. a puszta vágási vonalat nézve), élőben külön meg kell erősíteni.**

---

## Általános szabályok

* Egyszerre csak egy fázis lehet aktív.
* A következő fázis csak az előző lezárása után kezdhető meg.
* Locked állapotú fázis kizárólag Architecture Decision Record alapján módosítható.
* A ROADMAP a projekt fejlesztési sorrendjének hivatalos nyilvántartása.
