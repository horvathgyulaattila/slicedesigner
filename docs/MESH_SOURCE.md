# MESH_SOURCE.md

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-07
Utolsó módosítás: 2026-08-15
Kapcsolódó dokumentumok: [ARCHITECTURE.md](ARCHITECTURE.md), [DOMAIN_MODEL.md](DOMAIN_MODEL.md), [PROJECT_CONSTITUTION.md](PROJECT_CONSTITUTION.md), [ENGINEERING_PRINCIPLES.md](ENGINEERING_PRINCIPLES.md), [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md), [0014-meshsource-abstraction.md](adr/0014-meshsource-abstraction.md)

## Cél

Ez a dokumentum a Slice Designer modellforrásainak közös architekturális
szerződését, a `MeshSource` fogalmat és az opcionális külső
modellforrásokhoz szükséges határvonalat rögzíti.

A cél az, hogy a Slice Designer a modell előállításának módjától
függetlenül ugyanazon `Mesh` domain objektumon keresztül tudja fogadni a
feldolgozandó geometriát.

A `MeshSource` nem új geometriai feldolgozó pipeline, és nem módosítja a
Mesh után következő feldolgozási lépéseket.

## 1. Alapvető döntések

A `MeshSource` architekturális absztrakció, amely minden olyan komponens
közös szerződése, amely a Slice Designer számára feldolgozható `Mesh`-t
állít elő.

Ennek megfelelően:

-   a jelenlegi STL-import is `MeshSource` megvalósításnak tekintendő;
-   későbbi import- vagy generáló források ugyanebbe az absztrakcióba
    illeszkednek;
-   a downstream pipeline nem különböztetheti meg a `Mesh` eredetét;
-   a `MeshSource` kimenete mindig a meglévő `Mesh` domain objektum;
-   a `MeshSource` nem tartalmaz slicing, assembly, nesting vagy export
    logikát;
-   a Slice Designer core nem függhet opcionális külső `MeshSource`
    megvalósításoktól;
-   egy opcionális plugin hiánya nem változtathatja meg a Slice Designer
    core működőképességét.

A kívánt adatfolyam:

``` text
MeshSource
    ↓
Mesh
    ↓
Slice Engine
    ↓
további pipeline
```

A `MeshSource` határa tehát a modell előállításánál, a `Mesh`
létrehozásánál húzódik.

## 2. Felelősségi határok

### MeshSource felelőssége

A `MeshSource` felelőssége:

-   a saját bemeneti paramétereinek értelmezése;
-   a saját forrás-specifikus geometriai logika végrehajtása;
-   érvényes `Mesh` előállítása;
-   a saját bemenetének érvényességi ellenőrzése;
-   hibás vagy hiányos bemenet esetén explicit hiba jelzése;
-   a determinisztikus működés biztosítása az Engineering Principles
    szerint.

A `MeshSource` nem felelős:

-   a modell szeleteléséért;
-   a szeletek illesztéséért;
-   a Gap, Dowel vagy Backplate kezeléséért;
-   a Numbering vagy Nesting feladatokért;
-   a DXF exportért;
-   a GUI megjelenítéséért.

### Project felelőssége

A Project koordinálja a `MeshSource` használatát és továbbítja annak
eredményét a pipeline következő lépései felé.

A Project nem tartalmazhatja egy adott MeshSource geometriai logikáját.

### GUI felelőssége

A GUI a MeshSource kiválasztásához és konfigurálásához szükséges
felhasználói interakcióért felelhet, de nem tartalmazhat
forrás-specifikus geometriai vagy üzleti logikát.

A MeshSource contract jelen dokumentumban nem határoz meg
GUI-szerződést.

### Downstream engine-ek felelőssége

A `Mesh`-et fogadó engine-ek a Mesh eredetétől függetlenül működnek.

A Slice Engine és az utána következő engine-ek nem hívhatják közvetlenül
a MeshSource-t, és nem lehetnek attól függőek, hogy a Mesh importból
vagy generálásból származott.

## 3. A MeshSource contract szemantikája

A contract minimális szemantikai követelménye:

``` text
source-specific parameters
        ↓
    MeshSource
        ↓
       Mesh
```

A contract nem határozza meg, hogy a paraméterek milyen konkrét
technikai formában jutnak el a forráshoz.

Minden MeshSource saját, forrás-specifikus paramétermodellt használ. Ez
összhangban van a Slice Designer meglévő paraméterezési elvével: egy
adott komponens működését szabályozó paraméterek az adott komponenshez
tartoznak.

A contractnak nem szabad egy adott MeshSource --- például a parametrikus
relief-generátor --- paramétereit a core számára kötelezővé tennie.

## 4. Kimeneti szerződés

Minden MeshSource egyetlen lényegi eredménye egy érvényes `Mesh` domain
objektum.

A downstream rendszer számára az alábbi tulajdonságok számítanak:

-   a Mesh topológiája;
-   a Mesh geometriája;
-   a Mesh validitása;
-   a Mesh domain modellben meghatározott egyéb attribútumai.

A Mesh eredete nem része a downstream feldolgozás döntési logikájának.

### Watertight követelmény

A MeshSource által előállított Mesh-nek meg kell felelnie a forrásra
vonatkozó geometriai validációs követelményeknek.

A parametrikus relief-generátor esetében a generátor szerződésének része
lesz a watertight, zárt Mesh előállítása. Ennek részletes követelményeit
a relief-specifikus dokumentáció fogja rögzíteni.

A `MeshSource` általános contractja nem kényszerít minden lehetséges
forrásra azonos geometriai tulajdonságokat azon túl, amit a `Mesh`
domain modell és az adott source specifikációja előír.

## 5. Forrásazonosítás és eredet

A `Mesh` domain objektum `source_path` attribútuma opcionális.

Ez azért szükséges, mert egy importált Mesh rendelkezhet fizikai
forrásfájllal, míg egy generált Mesh esetében nem feltétlenül létezik
ilyen fájl.

Ennek következménye:

-   fájlból importált Mesh esetén a `source_path` tartalmazhatja a
    forrásfájl helyét;
-   generált Mesh esetén a `source_path` értéke `None` lehet;
-   a `source_path` hiánya nem jelent érvénytelen Mesh-et;
-   a downstream geometriai feldolgozás nem alapozhatja működését arra,
    hogy minden Mesh-hez tartozik forrásfájl.

A `source_path` módosításának konkrét domain-modelbeli implementációja
külön módosításként kezelendő; jelen dokumentum a szükséges szemantikát
rögzíti.

## 6. Opcionális pluginok

A Slice Designer core támogatja opcionális külső `MeshSource`
megvalósítások használatát.

Egy ilyen plugin:

-   külön telepíthető Python package;
-   a Slice Designer core nélkül is külön fejleszthető;
-   a `MeshSource` contractot kell megvalósítania;
-   a core számára felfedezhető és regisztrálható kell legyen;
-   hiánya nem okozhat hibát a core működésében.

A parametrikus relief-generátor első ilyen opcionális plugin lesz.

A plugin saját domain logikája és belső szerkezete nem kerülhet be a
Slice Designer core-ba pusztán azért, hogy a plugin használható legyen.

## 7. Plugin és core határa

A core és a plugin közötti szerződés kizárólag a szükséges közös
fogalmakra korlátozandó.

A pluginnek nincs szüksége:

-   a Slice Engine belső működésének ismeretére;
-   a Dowel, Gap, Backplate, Numbering vagy Nesting engine-ek
    ismeretére;
-   a GUI belső működésének ismeretére;
-   a pipeline geometriai logikájának ismeretére.

A core oldalán ugyanígy nem jelenhet meg a parametrikus relief-generátor
konkrét algoritmusa vagy annak forrás-specifikus paramétere.

## 8. Determinizmus

A MeshSource minden futtatása determinisztikus kell legyen.

Azonos:

-   source-specifikus paraméterek,
-   bemenetek,
-   környezeti feltételek és
-   dokumentált seed

esetén az eredménynek reprodukálhatónak kell lennie.

Amennyiben egy MeshSource véletlenszerűséget használ, azt kizárólag
dokumentált és reprodukálható seed segítségével teheti.

Ez különösen releváns a parametrikus relief-generátor számára.

## 9. Hibakezelés

A MeshSource fail-fast módon működik.

Érvénytelen, hiányos vagy ellentmondásos bemenet esetén:

-   nem készíthet tetszőleges vagy részben érvényes Mesh-et;
-   nem alkalmazhat csendes korrekciót;
-   explicit hibát kell jeleznie.

A MeshSource nem adhat át a downstream pipeline-nak olyan eredményt,
amelyről tudható, hogy nem felel meg a saját specifikációjának.

A konkrét kivételosztályok és technikai hibakezelési mechanizmusok nem
tartoznak e dokumentum hatókörébe.

## 10. Verziózás és kompatibilitás

A `MeshSource` contract verziózott architekturális interfész.

A cél az, hogy egy külső plugin kompatibilitása ne implicit
feltételezésen alapuljon.

A contract verziója és a plugin által támogatott contract-verzió közötti
kompatibilitásnak explicit módon ellenőrizhetőnek kell lennie.

Jelen dokumentum csak ezt a követelményt rögzíti. A konkrét
verziókezelési mechanizmus és kompatibilitási algoritmus későbbi
implementációs döntés.

## 11. GUI-szerződés határa

A `MeshSource` contract nem definiálja:

-   milyen widgeteket használ a plugin;
-   hogyan jelennek meg a source-specifikus paraméterek;
-   milyen preview-t biztosít;
-   milyen interakciókkal állítja be a felhasználó a paramétereket.

Ezek külön prezentációs kérdések.

A geometriai és domain logika azonban minden esetben a GUI-n kívül
marad.

## 12. Architektúrába illeszkedés

A `MeshSource` bevezetése nem változtatja meg a Slice Designer
háromrétegű alapmodelljét:

``` text
GUI → Project → Domain
```

A `MeshSource` a Domain réteghez tartozó modell-előállítási felelősség.

A Project továbbra is koordinációs réteg marad.

A GUI továbbra is prezentációs réteg marad.

A downstream engine-ek továbbra is egymástól függetlenek, és a Project
által továbbított Domain Model fogalmakon keresztül kommunikálnak.

A változás kizárólag a jelenlegi "Mesh Import állítja elő a Mesh-et"
feltételezés általánosítása:

``` text
korábban:

Mesh Import → Mesh → Slice Engine


ezután:

MeshSource → Mesh → Slice Engine
   ↑
   ├── STL Source
   ├── további import Source-ok
   └── opcionális generáló pluginok
```

## 13. Hatókörön kívül

A jelen dokumentum nem határozza meg:

-   a plugin discovery konkrét technikai mechanizmusát;
-   a plugin telepítésének technikai folyamatát;
-   a plugin GUI contractját;
-   a parametrikus relief-generálás algoritmusát;
-   a HeightField domain modelljét;
-   a relief-generátor saját paramétereit;
-   a MeshBuilder implementációját;
-   a watertight relief-generálás algoritmusát;
-   a plugin csomagolásának konkrét build- és release-folyamatát.

Ezek csak a jelen contract elfogadása után, erre a dokumentumra
támaszkodva tervezhetők tovább.

## 14. Következő dokumentációs lépések

A `MeshSource` contract elfogadása után, az itt rögzített döntésekből
következő sorrend:

1.  A `MeshSource` architekturális változásának ADR-ben történő
    rögzítése.
2.  Az `ARCHITECTURE.md` frissítése.
3.  A `DOMAIN_MODEL.md` szükséges módosítása, különösen a
    `Mesh.source_path` szemantikája miatt.
4.  A plugin-architektúra és a discovery/regisztráció dokumentálása.
5.  A parametrikus relief plugin domain modelljének dokumentálása.
6.  A HeightField koncepció és contract dokumentálása.
7.  A konkrét relief-generátorok specifikációja.
8.  Csak ezután implementáció.

A későbbi dokumentumok és implementációk nem írhatják felül a jelen
contractot annak előzetes módosítása nélkül.

## 15. Elfogadási kritériumok

A dokumentum akkor tekinthető késznek, ha:

-   egyértelműen meghatározza a `MeshSource` célját és hatókörét;
-   egyértelműen meghatározza a MeshSource → Mesh kimeneti szerződést;
-   rögzíti, hogy az STL-import is MeshSource;
-   rögzíti az opcionális külső pluginok használatát;
-   rögzíti, hogy a plugin hiánya nem akadályozhatja a core működését;
-   rögzíti a source-specifikus paramétermodellek használatát;
-   rögzíti, hogy a contract nem tartalmaz GUI-szerződést;
-   rögzíti a determinisztikus működés követelményét;
-   rögzíti a fail-fast hibakezelést;
-   rögzíti a contract verziózásának szükségességét;
-   rendezi a `source_path` opcionális szemantikáját;
-   nem tartalmaz implementációs döntést olyan kérdésben, amelyet a
    contractnak nem szükséges eldöntenie;
-   összhangban van a PROJECT_CONSTITUTION.md, ARCHITECTURE.md és
    ENGINEERING_PRINCIPLES.md alapelveivel.

## 16. Státusz

**Elfogadva.**

Ez a dokumentum a `MeshSource` architekturális szerződés elfogadott
verziója. Az itt szereplő döntések a későbbi dokumentáció és
implementáció alapjául véglegesnek tekintendők.
