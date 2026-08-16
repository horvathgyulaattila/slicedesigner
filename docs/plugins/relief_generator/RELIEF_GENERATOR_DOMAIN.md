# RELIEF_GENERATOR_DOMAIN.md

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-09
Utolsó módosítás: 2026-08-15
Kapcsolódó dokumentumok: [PROJECT_CONSTITUTION.md](../../PROJECT_CONSTITUTION.md), [DOMAIN_MODEL.md](../../DOMAIN_MODEL.md), [ARCHITECTURE.md](../../ARCHITECTURE.md), [0014-meshsource-abstraction.md](../../adr/0014-meshsource-abstraction.md), [0015-optional-meshsource-plugin-architecture.md](../../adr/0015-optional-meshsource-plugin-architecture.md)

**Cél:** A parametrikus Relief Generator első generációjának domainmodellje
**Típus:** opcionális `MeshSource` plugin
**Első generátor:** matematikai függvény alapú parametrikus felület

---

# 1. Cél

Ez a dokumentum a SliceDesigner első parametrikus relief-generátorának domainfogalmait, geometriai követelményeit és felelősségi határait határozza meg.

A dokumentum célja egy olyan egyszerű, jól definiált első generátor meghatározása, amely:

* matematikai függvényből állít elő relieffelületet;
* parametrikusan újragenerálható;
* fizikai méret alapján meghatározható;
* zárt, vízzáró Mesh-t állít elő;
* a meglévő `MeshSource` contracton keresztül kapcsolódik a SliceDesignerhez;
* nem igényel külön slicing pipeline-t.

A dokumentum **nem** határozza meg egy általános parametrikus felületgeneráló motor teljes architektúráját.

A hosszú távú cél egy ilyen rendszer kialakítása lehet, de ez jelenleg külön backlog-tétel.

---

# 2. Kapcsolódás a MeshSource architektúrához

A Relief Generator egy opcionális `MeshSource` plugin.

Az adatfolyam:

```text
Relief Generator parameters
          ↓
mathematical surface
          ↓
closed relief geometry
          ↓
Mesh
          ↓
Mesh validation
          ↓
SliceDesigner pipeline
```

A plugin nem módosítja a Mesh után következő feldolgozási folyamatot.

A SliceDesigner downstream rendszere kizárólag a létrehozott `Mesh` objektummal dolgozik.

Ez összhangban van a `MESH_SOURCE.md` által meghatározott szerződéssel.

---

# 3. Az első generátor hatóköre

Az első generátor kizárólag **matematikai függvény alapú parametrikus reliefet** állít elő.

Bemenete:

```text
paraméterek
```

A paraméterekből a generátor meghatároz egy felületet:

```text
z = f(x, y)
```

A felületből a generátor zárt relief-testet állít elő.

A zárt testből jön létre a `Mesh`.

---

# 4. Mi a relief?

A Relief Generator által előállított relief olyan háromdimenziós test, amelynek:

* van egy alapfelülete;
* vannak oldalfalai;
* van egy változó felső felülete;
* a felső felület adja a relief geometriai formáját.

Alapvető szerkezete:

```text
                 felső felület
             ~~~~~~~~~~~~~~~~~~~
          ~~~                    ~~~
       ~~~                          ~~~
      │                                │
      │                                │
      │             test               │
      │                                │
      └────────────────────────────────┘
                  alap
```

A felső felület lehet:

* hullámos;
* dűneszerű;
* összetett;
* bemélyedéseket tartalmazó.

A relief nem köteles minden pontján pozitív kiemelkedést mutatni.

A bemélyedések megengedettek, de az első generátor esetében a felső felület nem kerülhet az alapfelület alá.

---

# 5. Geometriai koordinátarendszer

Az első generátor lokális geometriai modellje:

```text
          Z
          ↑
          │
          │       top surface
          │      ~~~~~~~~~~~~
          │    ~~~
          │  ~~
          │
          └──────────────────→ X
         /
        /
       Y
```

A relief alapfelülete egy meghatározott sík.

A generátor ezen síkhoz képest számítja a felső felület magasságát.

A modell célja, hogy a relief mélysége és magassága egyértelműen értelmezhető legyen.

---

# 6. Alapfelület

Az első generátor alapfelülete sík.

Jelölése:

```text
z = 0
```

A felső felület:

```text
z = f(x,y)
```

ahol az első generátor geometriai követelménye:

```text
f(x,y) >= 0
```

A relief tehát nem nyúlhat az alapfelület mögé.

---

# 7. Bemélyedések

A bemélyedés a felső felület lokális magasságának csökkenése.

Például:

```text
magasabb       magasabb
    /\             /\
   /  \____ ____ /  \
__/          V       \__
```

A bemélyedés megengedett mindaddig, amíg a felső felület az alapfelület felett marad.

Ez azt jelenti, hogy a relief rendelkezhet negatív **relief-magasságváltozással**, de nem rendelkezhet negatív abszolút magassággal az alaphoz képest.

---

# 8. Degenerált nulla vastagság

A matematikai feltétel:

```text
f(x,y) >= 0
```

önmagában nem garantálja, hogy a létrejövő geometria érvényes szilárd test legyen.

Ha:

```text
f(x,y) = 0
```

egy területen vagy pontban, a felső felület érintheti az alapfelületet.

Ez geometriai degenerációt okozhat.

Ezért a tényleges Mesh-generálásnak biztosítania kell, hogy az előállított test megfeleljen a Mesh validáció követelményeinek.

Az első generátor specifikációjában a későbbi implementáció során külön meg kell határozni a minimális megengedett lokális vastagságot.

**Ez jelen dokumentumban nyitott technikai paraméter.**

---

# 9. A zárt test felépítése

Az első generátor geometriai kimenete három fő felülettípusból áll:

```text
1. top surface
2. bottom surface
3. side walls
```

### Top surface

A matematikai függvényből mintavételezett felső felület.

```text
z = f(x,y)
```

### Bottom surface

Sík alapfelület:

```text
z = 0
```

### Side walls

A felső felület határát az alapfelület megfelelő pontjaival összekötő oldalfalak.

---

# 10. Zárt Mesh

A három felülettípusnak egyetlen zárt geometriai testet kell alkotnia:

```text
top
 +
bottom
 +
sides
 =
closed solid
```

A Relief Generator nem adhat át nyitott felületet saját sikeres generálási eredményként.

Ez összhangban van a `MESH_SOURCE.md`-ben már rögzített relief-specifikus watertight követelménnyel.

---

# 11. Watertight követelmény

Az első Relief Generator kimeneti szerződésének része:

> A sikeresen generált relief Mesh zárt és watertight kell legyen.

Ez a követelmény a konkrét Relief Generatorra vonatkozik.

Nem jelenti azt, hogy minden jövőbeni `MeshSource` ugyanilyen forrás-specifikus geometriai követelményeket kap.

A generálási folyamat:

```text
parameters
    ↓
surface generation
    ↓
solid construction
    ↓
Mesh
    ↓
validation
    ↓
valid / error
```

---

# 12. Generátor és validátor felelőssége

A felelősségek különválnak.

## Generátor

A generátor feladata:

* a paraméterek feldolgozása;
* a matematikai felület meghatározása;
* a felület mintavétele;
* a zárt test geometriai felépítése;
* Mesh előállítása.

A generátor nem hivatkozhat arra, hogy:

> „majd a validátor kijavítja”.

A generátor saját specifikációjának megfelelő Mesh-t köteles előállítani.

## Validator

A validátor feladata:

* a Mesh érvényességének ellenőrzése;
* a zártság ellenőrzése;
* a watertight állapot ellenőrzése;
* geometriai degenerációk felismerése;
* hibás eredmény visszautasítása.

A validátor nem generálhat új geometriát a generátor hibájának csendes javításaként.

---

# 13. Hibakezelési modell

Ha a generátor nem tudja előállítani a saját specifikációjának megfelelő Mesh-t:

```text
Generator
    ↓
hiba
    ↓
nincs érvényes Mesh
```

Ha a generátor Mesh-t állított elő, de az nem felel meg a validációs követelményeknek:

```text
Generator
    ↓
Mesh
    ↓
Validator
    ↓
invalid
    ↓
hiba
```

A hibás Mesh nem kerülhet a downstream slicing pipeline-ba.

Ez összhangban van a MeshSource fail-fast működési követelményével.

---

# 14. Parametrikus működés

A Relief Generator parametrikus.

A geometria a paraméterek függvénye:

```text
parameters
    ↓
f(x,y)
    ↓
Mesh
```

Ha a paraméterek megváltoznak:

```text
old parameters
      ↓
old Mesh

new parameters
      ↓
new Mesh
```

A generátor nem módosítja inkrementálisan a korábbi Mesh-t.

Az új paraméterkészletből új geometriai eredményt állít elő.

---

# 15. Determinizmus

A Relief Generatornak követnie kell a `MeshSource` determinisztikus működési követelményét.

Azonos:

* paraméterek;
* bemenetek;
* környezeti feltételek;
* dokumentált seed

esetén reprodukálható eredményt kell előállítania.

Az első generátor lehetőleg ne használjon véletlenszerűséget.

Ha későbbi generátorverzióban randomizáció jelenik meg, annak seedje explicit és reprodukálható kell legyen.

---

# 16. Paraméterek

Az első generátor paraméterei két csoportba sorolhatók.

## Geometriai paraméterek

Ezek a létrejövő relief méretét és formáját határozzák meg.

Például:

* szélesség;
* magasság;
* alapvastagság;
* relief maximális magassága;
* felületi frekvencia;
* irány;
* fázis;
* összetettség.

A pontos paraméterkészletet a konkrét generátor-specifikáció határozza meg.

## Mintavételi / felbontási paraméterek

Ezek a matematikai felület Mesh-re történő leképezését szabályozzák.

Például:

* X irányú mintavétel;
* Y irányú mintavétel;
* vagy ezekből származtatott geometriai felbontás.

A konkrét paraméterezés még nem része ennek a dokumentumnak.

---

# 17. Fizikai méret és felbontás

A generátor fizikai mérete és a Mesh felbontása két külön fogalom.

```text
fizikai méret
      +
mintavételi felbontás
      ↓
Mesh
```

A felbontás nem lehet teljesen független a fizikai mérettől.

Ugyanakkor a felbontás meghatározásakor figyelembe kell venni a generált felület geometriai részletességét is.

---

# 18. Bemeneti információ és felbontási limit

Az első generátor matematikai függvényből dolgozik, ezért annak felbontását nem korlátozza külső képi vagy pixeles bemenet.

Ez eltér a későbbi kép- és heightmap-alapú generátoroktól.

Későbbi generátorok esetén a bemenet természetes felbontási korlátot jelenthet.

Ezért az első generátor felbontási modelljét nem szabad általános, minden későbbi generátorra kötelező szabállyá tenni.

---

# 19. Felületi modell

Az első generátor alapvető matematikai modellje:

```text
z = f(x,y)
```

A függvény meghatározza a felső felület lokális magasságát.

A generátor feladata ennek a folytonos vagy diszkrét matematikai modellnek a Mesh számára megfelelő mintavétele.

Az első generátorban a függvény típusa és paraméterezése source-specifikus.

---

# 20. Első generátor célja

Az első generátor célja nem általános tárgygenerálás.

Első körben olyan természetes jellegű felületek előállítása a cél, mint:

* hullámok;
* organikus hullámzás;
* dűneszerű formák;
* hasonló természetes reliefstruktúrák.

A generátor használati tárgyakat vagy bútorokat nem köteles előállítani.

---

# 21. Hosszú távú cél

A projekt hosszabb távú célja egy komolyabb parametrikus felületgeneráló rendszer lehet.

Ennek potenciális bemeneti forrásai:

```text
Mathematical Function
        │
Heightmap
        │
Image
        │
Vector
        │
egyéb későbbi források
```

Ezekből később közös vagy részben közös geometriai feldolgozási réteg alakulhat ki.

**Ez jelenleg nem része az első implementációnak.**

Nem hozunk létre előre olyan absztrakciót, amelyet az első generátor nem igényel.

---

# 22. Jövőbeli generátorok

A következő generátortípusok lehetnek későbbi bővítések:

* kép alapú;
* heightmap alapú;
* vektor alapú;
* egyéb parametrikus vagy algoritmikus források.

Ezek mind külön `MeshSource` megvalósításként kezelhetők.

A jelen dokumentum nem írja elő, hogy ezek milyen belső algoritmust vagy közös reprezentációt használjanak.

---

# 23. Jövőbeli általános felületgeneráló motor

A projekt hosszú távú backlogjába kerül:

> **Általános parametrikus felületgeneráló motor kialakítása, amely többféle geometriai bemenetből és generálási módszerből képes közös elvek szerint felületeket és zárt Mesh-eket előállítani.**

Ennek célja később akár:

* falpanelek;
* korlátok;
* használati tárgyak;
* bútorok;
* egyéb parametrikus geometriai objektumok

generálásának támogatása.

Ez azonban **nem része az első Relief Generator implementációjának**.

---

# 24. Topológiai korlátok az első generátorban

Az első generátor alapmodellje egy egyszerű, összefüggő, sík alapú relief-test.

Ez azt jelenti, hogy a kezdeti generátor:

* nem igényel általános lyukkezelést;
* nem igényel tetszőleges topológiai változást;
* nem igényel több különálló szilárd test kezelését.

A későbbi, általánosabb felületgeneráló rendszerben a topológiai összetettség külön döntési terület lehet.

A „lyukak” és összetett topológiák ezért hosszú távú képességként kezelendők, nem az első matematikai generátor minimális követelményeként.

---

# 25. Geometriai invariánsok

Az első Relief Generator által előállított eredménynek:

1. meghatározott fizikai méretűnek kell lennie;
2. zárt Mesh-t kell alkotnia;
3. watertight kell legyen;
4. az alapfelületnek síknak kell lennie;
5. a felső felületnek a matematikai függvényből kell származnia;
6. a felső felület nem kerülhet az alapfelület alá;
7. a Mesh nem tartalmazhat tudottan hibás vagy degenerált elemeket;
8. a Mesh alkalmas kell legyen a SliceDesigner downstream pipeline számára.

---

# 26. Felelősségi határok

## Relief Generator

Felelős:

* paraméterértelmezés;
* matematikai felület;
* mintavétel;
* top surface előállítása;
* bottom surface előállítása;
* side wall előállítása;
* zárt Mesh összeállítása.

## Mesh Validator

Felelős:

* Mesh validáció;
* watertight ellenőrzés;
* topológiai és geometriai hibák felismerése;
* hibás Mesh visszautasítása.

## Project

Felelős:

* a Relief Generator kiválasztásának koordinálása;
* paraméterek továbbítása;
* generálás eredményének pipeline-ba továbbítása.

Nem felelős a relief-geometria előállításáért.

## GUI

Felelős:

* paraméterek felhasználói megadása;
* generátor kiválasztása;
* opcionális preview megjelenítése.

Nem tartalmazhat relief-generálási logikát.

## Slice Engine és downstream engine-ek

Nem tudhatják és nem is kell tudniuk, hogy a Mesh Relief Generatorból származik.

---

# 27. Nem része a domainmodellnek

Az első Relief Generator domainmodellje nem tartalmaz:

* GUI widgeteket;
* plugin discovery mechanizmust;
* Python package struktúrát;
* STL exportot;
* FreeCAD API-t;
* konkrét Mesh library API-t;
* konkrét triangulációs algoritmust;
* konkrét matematikai függvénykönyvtárat;
* fájlformátumot;
* plugin telepítési mechanizmust.

Ezek technikai implementációs kérdések.

---

# 28. Kapcsolódó dokumentumok

A domainmodell az alábbi dokumentációkra támaszkodik:

* `../../adr/0014-meshsource-abstraction.md`
* `../../adr/0015-optional-meshsource-plugin-architecture.md`
* `../../DOMAIN_MODEL.md`
* `../../ARCHITECTURE.md`
* `../../ENGINEERING_PRINCIPLES.md`

A `MeshSource` contract (ADR-0014) már rögzíti a determinisztikus és fail-fast működés követelményeit, valamint a Relief Generatorhoz kapcsolódó watertight kimeneti elvárást. A `PLUGIN_ARCHITECTURE.md` plugin belső felépítését leíró dokumentum jelenleg még a `docs/drafts/relief_generator_plugin/` alatt van, véglegesítése külön Phase 8 tétel — a jelen dokumentum ezért ide egyelőre nem hivatkozik.

---

# 29. Impact Analysis

## Érintett dokumentumok

### Közvetlenül

* `RELIEF_GENERATOR_DOMAIN.md`

### Kapcsolódó

* `MESH_SOURCE.md`
* `adr/0015-optional-meshsource-plugin-architecture.md`
* `DOMAIN_MODEL.md`
* `ARCHITECTURE.md`

A meglévő MeshSource contractot jelen dokumentum nem módosítja.

## Érintett könyvtárak

Dokumentációs szinten:

```text
docs/
```

A plugin konkrét implementációs könyvtára jelen döntésből még nem következik.

## Szükséges dokumentummódosítások

A domainmodell elfogadása után szükség lehet:

* egy konkrét Relief Generator specification dokumentumra;
* a matematikai függvények és paraméterek specifikációjára;
* a Mesh validációs követelmények részletesítésére;
* szükség esetén a `DOMAIN_MODEL.md` kapcsolódó hivatkozásainak frissítésére.

A `MESH_SOURCE.md` módosítása jelen tervezetből nem következik.

## Szükséges ADR

**Jelen tervezet önmagában nem igényel új ADR-t**, amennyiben a benne szereplő döntések a már elfogadott `MeshSource` és plugin-architektúra keretein belül maradnak.

Új ADR akkor szükséges, ha a domainmodell kidolgozása során új architekturális döntés merül fel, például:

* új közös geometriai absztrakció;
* új domainobjektum;
* új általános felületgeneráló réteg;
* a `MeshSource` contract módosítása.

## Visszafelé kompatibilitás

A Relief Generator opcionális.

A meglévő STL-alapú workflow változatlan marad.

A downstream pipeline változatlan `Mesh` bemenetre épül.

---

# 30. Elfogadási kritériumok

A dokumentum akkor tekinthető késznek, ha:

1. egyértelműen definiálja az első Relief Generator hatókörét;
2. matematikai függvény alapú generátorként definiálja;
3. meghatározza a `z = f(x,y)` jellegű felületi modellt;
4. meghatározza a sík alapfelületet;
5. meghatározza a felső felületet;
6. meghatározza az oldalfalakat;
7. rögzíti a zárt Mesh követelményét;
8. rögzíti a watertight követelményt;
9. különválasztja a generátor és a validátor felelősségét;
10. biztosítja, hogy hibás Mesh ne kerüljön downstream feldolgozásba;
11. kezeli a bemélyedéseket;
12. megakadályozza, hogy a relief az alapfelület mögé kerüljön;
13. elkülöníti a fizikai méretet és a Mesh felbontását;
14. nem épít be szükségtelen HeightField- vagy általános Surface Engine absztrakciót;
15. lehetővé teszi a későbbi kép-, heightmap- és vektoralapú generátorok bevezetését;
16. a hosszú távú általános felületgeneráló motor célját backlogként kezeli;
17. nem módosítja a meglévő slicing pipeline architektúráját;
18. összhangban van a `MESH_SOURCE.md`-vel és a kapcsolódó ADR-ekkel (ADR-0014, ADR-0015).

---

# 31. Célállapot

Az első Relief Generator minimális architekturális modellje:

```text
                  User Parameters
                        │
                        ▼
              Parametric Function
                        │
                        ▼
                 z = f(x,y)
                        │
                        ▼
                sampled surface
                        │
             ┌──────────┼──────────┐
             │          │          │
            TOP       BOTTOM      SIDES
             │          │          │
             └──────────┼──────────┘
                        ▼
                   closed Mesh
                        │
                        ▼
                  Mesh Validator
                        │
                  ┌─────┴─────┐
                  │           │
                valid       invalid
                  │           │
                  ▼           ▼
              Slice       explicit error
              Engine
```

A hosszú távú cél ettől eltérhet:

```text
          Future Surface Generator
                    │
       ┌────────────┼────────────┐
       │            │            │
   Function      Heightmap     Vector
       │            │            │
       └────────────┼────────────┘
                    ▼
              Surface model
                    ▼
              Solid geometry
                    ▼
                  Mesh
```

A második diagram **jövőbeli irány**, nem az első implementáció célarchitektúrája.

---

# 32. Státusz

**Elfogadva.**

A dokumentum az első Relief Generator domainjének alapjait rögzíti; a konkrét matematikai függvényt, a teljes paraméterkészletet és a mintavételi algoritmust a kapcsolódó, szintén elfogadott `WAVE_FUNCTION_MODEL.md`, `PARAMETRIC_RELIEF_GENERATOR.md`, `RELIEF_GEOMETRY_MODEL.md` és `MESH_GENERATION_MODEL.md` dokumentumok részletezik.
