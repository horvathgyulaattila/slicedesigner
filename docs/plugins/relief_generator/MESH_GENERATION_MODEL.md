# MESH_GENERATION_MODEL.md

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-12
Utolsó módosítás: 2026-08-16
Kapcsolódó dokumentumok: [PROJECT_CONSTITUTION.md](../../PROJECT_CONSTITUTION.md), [RELIEF_GEOMETRY_MODEL.md](RELIEF_GEOMETRY_MODEL.md)

## 1. Cél

A Mesh Generation Layer feladata a `ReliefGeometry` domainmodellből egy, a SliceDesigner által közvetlenül felhasználható, érvényes háromdimenziós mesh előállítása.

A feldolgozási lánc:

```text
Surface Generator
        ↓
Height Field
        ↓
ReliefGeometry
        ↓
Mesh Generator
        ↓
Mesh
        ↓
MeshSource
        ↓
SliceDesigner
```

A Mesh Generation Layer nem használ STL-t köztes reprezentációként.

---

# 2. Felelősségi határ

A Mesh Generator felelős:

* a geometria mintavételezéséért;
* vertexek létrehozásáért;
* a felső felület mesh-eléséért;
* az alsó felület létrehozásáért;
* az oldalfalak létrehozásáért;
* a felületek összekapcsolásáért;
* a mesh topológiájának kialakításáért;
* a SliceDesigner által használható Mesh előállításáért.

A Mesh Generator nem felelős:

* a hullám matematikai előállításáért;
* a Height Field tartalmának meghatározásáért;
* a relief fizikai méretének meghatározásáért;
* STL exportért;
* általános mesh-javításért;
* szeletelésért.

---

# 3. Bemenet

A Mesh Generator bemenete:

```text
ReliefGeometry
```

A `ReliefGeometry` tartalmazza:

```text
width
height
base_thickness
relief_height
top_surface / HeightField
```

A Mesh Generator számára a felületet nem az eredeti WaveFunction jelenti.

A Mesh Generator kizárólag a geometriai modellt használja.

Ez biztosítja, hogy ugyanaz a Mesh Generator később más Surface Generatorok eredményét is fel tudja dolgozni.

---

# 4. Kimenet

A Mesh Generator kimenete egy SliceDesigner-kompatibilis `Mesh`.

A kimenet közvetlenül átadható a `MeshSource` rétegnek.

A feldolgozásban nincs szükség:

```text
Mesh → STL → Mesh
```

konverzióra.

Az STL kizárólag exportformátum lehet.

---

# 5. A mesh geometriai felépítése

Az első implementáció egy zárt, négyzet/ téglalap alapú relief-testet állít elő.

A mesh négy logikai felületből áll:

```text
1. Top Surface
2. Bottom Surface
3. Side Wall X-
4. Side Wall X+
5. Side Wall Y-
6. Side Wall Y+
```

A felső felület a Height Fieldből származik.

Az alsó felület sík.

A négy oldalfal függőleges.

---

# 6. Sampling modell

A Height Field matematikai/felületi reprezentációja folytonosnak tekinthető.

A Mesh Generator ezt egy szabályos XY mintavételi rácson értékeli ki.

Például:

```text
Nx × Ny
```

mintapont.

A rács:

```text
(x0,y0) ─── (x1,y0) ─── ... ─── (xN,y0)
   │            │                    │
   │            │                    │
(x0,y1) ─── (x1,y1) ─── ... ─── (xN,y1)
   │            │                    │
   ⋮            ⋮                    ⋮
(x0,yM) ─── (x1,yM) ─── ... ─── (xN,yM)
```

A mintavételi rács szabályos.

Az első implementáció nem használ adaptív samplinget.

---

# 7. Sampling és fizikai méret

A fizikai XY méret:

```text
width
height
```

A sampling sűrűsége pedig:

```text
Nx
Ny
```

A szomszédos mintapontok fizikai távolsága:

[
\Delta x = \frac{width}{N_x-1}
]

[
\Delta y = \frac{height}{N_y-1}
]

Ez biztosítja, hogy a mesh fizikai mérete pontosan megfeleljen a `ReliefGeometry` méretének.

---

# 8. Resolution kezelése

Az első implementációban a mesh felbontását a Mesh Generator kapja meg.

A felbontás nem része a Surface Generator matematikai modelljének.

Ez lehetővé teszi ugyanazon geometria különböző részletességű mesh-elését.

Például:

```text
ReliefGeometry
      ↓
Nx = 200
Ny = 100
      ↓
low resolution mesh
```

vagy:

```text
ReliefGeometry
      ↓
Nx = 1000
Ny = 500
      ↓
high resolution mesh
```

---

# 9. Resolution stratégia

Az első implementációban a resolution explicit mintaszámként kezelhető.

A későbbi rendszerben lehetőség marad fizikai mintatávolság alapján meghatározott resolution használatára.

Például:

```text
sampling_distance = 2 mm
```

alapján:

[
N_x \approx \frac{width}{2}
]

[
N_y \approx \frac{height}{2}
]

Ez azonban nem része az első implementáció kötelező API-jának.

---

# 10. Vertexek létrehozása

Minden felső felületi mintapontból egy vertex készül.

A koordináták:

[
X_i = x_i
]

[
Y_j = y_j
]

[
Z_{ij}
======

base_thickness
+
H(x_i,y_j)\cdot relief_height
]

A felső felület vertexei tehát közvetlenül a Height Field mintavételezett értékeiből származnak.

---

# 11. Alsó felület vertexei

Az alsó felület sík:

[
Z=0
]

A felső felület XY pozícióival megegyező XY koordinátákon helyezkedik el.

Az első implementációban a top és bottom vertexek külön mesh-vertexek lehetnek.

Ez lehetővé teszi a felületek egyértelmű topológiai és normálirány-kezelését.

---

# 12. Top Surface

A felső felület minden szomszédos mintapont-párja egy négyszögletes cellát alkot.

```text
v00 ───── v10
 │         │
 │         │
v01 ───── v11
```

A cellát két háromszögre kell bontani.

Például:

```text
v00
├──────── v10
│      ╱
│    ╱
│  ╱
v01 ───── v11
```

A trianguláció determinisztikus.

Az első implementációban a teljes felső felület szabályos rácsos triangulációt használ.

---

# 13. Trianguláció

Minden cella pontosan két háromszöget eredményez.

Ha a rács:

```text
Nx × Ny
```

vertexből áll, akkor a top surface celláinak száma:

[
(N_x-1)(N_y-1)
]

A top surface háromszögeinek száma:

[
2(N_x-1)(N_y-1)
]

A trianguláció során az összes cella azonos szabály szerint kerül felosztásra.

Ez biztosítja a determinisztikus topológiát.

---

# 14. Triangle diagonal

A négyszögletes cella átlója az első implementációban egységes szabály szerint kerül meghatározásra.

Nem cél adaptív diagonalválasztás.

Az adaptív trianguláció későbbi optimalizálási lehetőség.

---

# 15. Bottom Surface

Az alsó felület egy sík téglalap:

[
Z=0
]

A felső felülethez hasonló rácsos struktúrát használ.

Az alsó felület normálirányának lefelé kell mutatnia.

A vertex- és face-sorrendnek ennek megfelelőnek kell lennie.

---

# 16. Side Walls

A négy oldalfal a felső és alsó felület megfelelő peremvertexeit köti össze.

Egy oldalfali szakasz:

```text
top_a ───── top_b
 │           │
 │           │
bottom_a ── bottom_b
```

két háromszögből áll.

Az oldalfalak függőlegesek, mert a top és bottom vertexek XY koordinátája megegyezik.

---

# 17. Side Wall Topology

A négy oldalfal a top surface négy peremét követi:

```text
Top
┌──────────────────┐
│                  │
│                  │
│                  │
└──────────────────┘
```

A Mesh Generatornak minden topological boundary edge-et megfelelő oldalfallal kell lezárnia.

Nem maradhat nyitott perem.

---

# 18. Vertex megosztás

Az első implementációban a geometriai topológia egyszerűsége fontosabb, mint a minimális vertexszám.

A vertexek megosztásának szabálya:

* azonos geometriai pontok szükség esetén újrahasznosíthatók;
* de külön vertexek megengedettek ott, ahol a topológiai vagy normálirány-kezelés ezt indokolja.

A Mesh Generatornak nem célja a minimális vertexszám mindenáron történő elérése.

---

# 19. Normálirányok

A mesh face-orientációja meghatározza a normálirányt.

A kívánt irányok:

```text
Top Surface
    ↑ +Z / kifelé

Bottom Surface
    ↓ -Z / kifelé

Side Walls
    → oldalirányban kifelé
```

A mesh minden felületének kifelé mutató orientációval kell rendelkeznie.

Ez szükséges a zárt solid helyes értelmezéséhez.

---

# 20. Watertight mesh

Az első implementáció kimenetének watertight meshnek kell lennie.

A mesh nem tartalmazhat:

* boundary edge-et;
* lyukat;
* hiányzó oldalfalat;
* hiányzó alsó felületet;
* nem összekapcsolt topológiai régiót.

A Mesh Generatornak úgy kell felépítenie a topológiát, hogy a zártság konstrukciós tulajdonság legyen.

A Mesh Validator ezt utólag ellenőrzi.

---

# 21. Self-intersection

Az első geometriai modell matematikailag úgy épül fel, hogy a top surface minden pontja:

[
Z \geq base_thickness
]

Ezért az alaptesttel való metszés nem megengedett.

A Mesh Generatornak nem kell általános self-intersection repair algoritmust tartalmaznia.

A hibás vagy érvénytelen geometria felismerése a validációs réteg feladata.

---

# 22. Degenerate triangles

A Mesh Generator nem hozhat létre szándékosan degenerált háromszögeket.

Degenerált háromszög például olyan face, amelynek:

* nulla területe van;
* azonos vertexekből áll;
* vagy topológiailag érvénytelen.

A szabályos sampling rács miatt az első implementációban ezek normál működés mellett nem várhatók.

---

# 23. Resolution és teljesítmény

A mesh mérete közvetlenül függ a sampling resolutiontől.

A vertexek száma nagyságrendileg:

[
N_xN_y
]

A top surface face-einek száma:

[
2(N_x-1)(N_y-1)
]

Ehhez adódnak az alsó és oldalfali face-ek.

Ezért a resolution növelése jelentősen növeli:

* memóriahasználatot;
* számítási időt;
* mesh méretét;
* későbbi szeletelési költséget.

Az első implementáció nem alkalmaz automatikus adaptív optimalizálást.

## 23.1. `sampling_distance` paraméter

Az első implementáció a mesh felbontását nem közvetlen `Nx`/`Ny` értékként kapja, hanem egy fizikai `sampling_distance` paraméterből (mm) számítja:

```text
Nx = ceil(width / sampling_distance)
Ny = ceil(height / sampling_distance)
```

## 23.2. Erőforráskorlát

A számított mintapontszámra statikus felső korlát vonatkozik:

```text
Nx × Ny > MAX_SAMPLE_COUNT → hiba
```

Kezdeti érték: `MAX_SAMPLE_COUNT = 2 000 000` — nagyságrendi becslés, implementáció közbeni méréssel felülvizsgálandó és a review során véglegesítendő.

A rendszer túllépés esetén nem csökkenti automatikusan a felbontást, hanem egyértelmű hibát jelez (fail-fast elv, `PROJECT_CONSTITUTION.md` 7. elve).

## 23.3. Későbbi bővítés

Automatikus/adaptív sampling, a legkisebb hullámhossz alapján számított felbontás, illetve dinamikus erőforráskorlát nem része az első implementációnak — ezek későbbi backlog-tételek.

---

# 24. Nagy modellek kezelése

A rendszernek képesnek kell lennie nagy fizikai méretű reliefek kezelésére anélkül, hogy a fizikai méret önmagában indokolatlanul növelné a mesh felbontását.

A fizikai méret és a sampling resolution ezért külön fogalom.

Például:

```text
2000 × 1000 mm
```

önmagában nem jelenti azt, hogy több millió vertex szükséges.

A felhasználó által választott sampling határozza meg a geometriai részletességet.

---

# 25. Determinizmus

A Mesh Generation determinisztikus.

Azonos:

* `ReliefGeometry`;
* sampling resolution;
* triangulációs szabály

mellett azonos meshnek kell létrejönnie.

Ez biztosítja:

* reprodukálhatóságot;
* tesztelhetőséget;
* cache-elhetőséget;
* hibakeresést;
* összehasonlítható eredményeket.

---

# 26. Mesh és STL szétválasztása

A belső pipeline-ban STL nem jelenik meg.

A helyes út:

```text
ReliefGeometry
      ↓
Mesh Generator
      ↓
Mesh
      ↓
MeshSource
      ↓
SliceDesigner
```

STL export esetén:

```text
Mesh
 ↓
STL Export
```

Az STL tehát output/export formátum, nem belső domainmodell.

---

# 27. MeshSource integráció

A Mesh Generator által előállított Meshnek közvetlenül kompatibilisnek kell lennie a SliceDesigner meglévő `MeshSource` contractjával.

A plugin feladata:

```text
Generator
   ↓
ReliefGeometry
   ↓
Mesh
   ↓
MeshSource
```

A SliceDesigner nem tudhatja, hogy a Mesh:

* Wave Generatorból;
* Heightmap Generatorból;
* Image Generatorból;
* Vector Generatorból

származott.

A SliceDesigner számára kizárólag a MeshSource által biztosított mesh számít.

---

# 28. Mesh validáció

A Mesh Generator és a Mesh Validator külön komponensek.

A Mesh Generator előállítja a mesh-t.

A Validator ellenőrzi például:

* watertight állapot;
* boundary edge-ek hiánya;
* degenerált face-ek;
* topológiai konzisztencia;
* geometriai érvényesség;
* normálirányok;
* esetleges self-intersection.

A Validator hibája nem jelenti azt, hogy a Validatornak automatikusan javítania kell a mesh-t.

A repair funkció külön későbbi döntés lehet.

---

# 29. Hibakezelés

A Mesh Generatornak nem szabad csendben hibás mesh-t előállítania.

Ha a bemeneti `ReliefGeometry` vagy a sampling paraméterek érvénytelenek, a generálásnak egyértelmű hibával kell megszakadnia.

Például:

```text
width <= 0
height <= 0
relief_height < 0
base_thickness < 0
Nx < 2
Ny < 2
```

érvénytelen bemenet.

A pontos exception/error contract a későbbi implementációs terv része.

---

# 30. Első implementáció korlátai

Az első Mesh Generator:

* szabályos sampling rácsot használ;
* egyetlen relief testet kezel;
* sík alappal dolgozik;
* függőleges oldalfalakat használ;
* szabályos triangulációt alkalmaz;
* zárt mesh-t állít elő;
* közvetlenül Mesh-t ad a SliceDesignernek.

Nem támogat:

* adaptív remeshinget;
* mesh decimationt;
* curvature-based samplinget;
* arbitrary polygonal boundaries-t;
* lyukakat;
* több különálló testet;
* automatikus repairt;
* fejlett mesh-optimalizálást.

---

# 31. Későbbi bővíthetőség

A Mesh Generation Layernek úgy kell kialakulnia, hogy a későbbi Geometry Model bővítések ne kényszerítsék a Wave Generator módosítására.

Lehetséges későbbi bemenetek:

```text
ReliefGeometry
ComplexReliefGeometry
MultiSurfaceGeometry
FurnitureGeometry
ObjectGeometry
```

A Mesh Generator később több geometriai reprezentációt is támogathat.

Az első implementáció azonban kizárólag a jelenlegi `ReliefGeometry` modellre koncentrál.

---

# 32. Első implementációs geometriai pipeline

Az első megvalósítás logikája:

```text
ReliefGeometry
      │
      ├── width
      ├── height
      ├── base_thickness
      ├── relief_height
      └── HeightField
             │
             ↓
       Sampling Grid
             │
             ↓
       Top Vertices
             │
             ├──────────────┐
             ↓              ↓
       Top Triangles    Bottom Vertices
                              │
                              ↓
                        Bottom Triangles
             │
             ↓
        Side Vertices
             │
             ↓
        Side Triangles
             │
             ↓
          Mesh
             │
             ↓
         Validator
             │
             ↓
         MeshSource
```

---

# 33. Alapvető invariánsok

A Mesh Generator kimenetére vonatkozó invariánsok:

### Geometriai

```text
X ∈ [0,width]
Y ∈ [0,height]
Z ≥ 0
```

### Relief

```text
Ztop ≥ base_thickness
Ztop ≤ base_thickness + relief_height
```

### Topológiai

```text
nincs boundary edge
nincs hiányzó oldalfal
nincs nyitott bottom
```

### Determinisztikus

```text
azonos input → azonos mesh
```

### Pipeline

```text
nincs STL köztes reprezentáció
```

---

# 34. Tervezési alapelv

A Mesh Generation Layer legyen **egyszerű, determinisztikus és kiszámítható**.

Az első implementáció célja nem a lehető legjobb mesh-generáló algoritmus létrehozása, hanem egy stabil és jól definiált út létrehozása:

```text
ReliefGeometry
       ↓
valid Mesh
       ↓
SliceDesigner
```

A későbbi optimalizációk — adaptív sampling, decimation, intelligens trianguláció, curvature-based refinement stb. — külön fejlesztési feladatként kezelendők.

Ezek nem módosíthatják az első implementáció alapvető domain-szerződéseit megfelelő döntési és dokumentációs folyamat nélkül.

---

# 35. Következő lépés

A következő dokumentum már nem újabb domainmodell, hanem a tényleges megvalósítás előkészítése:

**`IMPLEMENTATION_PLAN.md`**

Ebben kell majd meghatározni:

* milyen meglévő SliceDesigner komponensek használhatók;
* milyen új modulok/fájlok szükségesek;
* milyen sorrendben történjen az implementáció;
* milyen teszteket kell létrehozni;
* hogyan kapcsolódik a plugin a meglévő `MeshSource` contracthoz;
* milyen részeket kell a plugin saját domainjében tartani;
* és pontosan milyen minimális első implementációt kell elkészíteni.

A jelen dokumentum célja ezzel lezárul: **a `ReliefGeometry → Mesh` szerződés és a mesh-előállítás alapmodellje rögzítve van.**

---

# 36. Determinisztikus vertex- és trianguláció-index séma (első implementáció)

A §12–18 nyitva hagyta a pontos vertex-indexelést és háromszög-sorrendet. Az első implementációhoz tartozó, jóváhagyott séma a következő — numerikusan verifikálva: mind a hat logikai felület (Top, Bottom, 4 oldalfal) minden háromszöge kifelé mutató normállal rendelkezik, és a teljes mesh minden éle pontosan két háromszögben szerepel (watertight).

### Rács és vertex-indexelés

`Nx`, `Ny` mintaszám mellett (§23.1), `Δx = width/(Nx-1)`, `Δy = height/(Ny-1)`:

```text
top_index(i, j)    = j·Nx + i
bottom_index(i, j) = Nx·Ny + j·Nx + i
```

A teljes vertexszám `2·Nx·Ny` — a top és bottom felület **külön** vertexkészletet kap (§11).

Egy `(i, j)` rácspont koordinátái:

```text
X_i = i·Δx
Y_j = j·Δy
Z_top    = ReliefGeometry.top_z(X_i/width, Y_j/height)
Z_bottom = ReliefGeometry.BOTTOM_Z
```

### Top Surface trianguláció

Minden `(i, j)` cellára, `i ∈ [0, Nx-2]`, `j ∈ [0, Ny-2]`, a négy sarokvertex:

```text
v00 = top_index(i, j)      v10 = top_index(i+1, j)
v01 = top_index(i, j+1)    v11 = top_index(i+1, j+1)
```

Két háromszög: **`(v00, v10, v11)`**, **`(v00, v11, v01)`**.

### Bottom Surface trianguláció

Ugyanaz a cellafelosztás, `bottom_index`-szel, **fordított sorrendben** (a lefelé mutató normál miatt):

Két háromszög: **`(v00, v11, v10)`**, **`(v00, v01, v11)`**.

### Oldalfalak trianguláció

Minden oldalfal a megfelelő perem mentén, `ta`/`tb` szomszédos top-vertexek, `ba`/`bb` a hozzájuk tartozó bottom-vertexek:

```text
X- fal (i=0),      j ∈ [0, Ny-2]: ta=top_index(0,j),    tb=top_index(0,j+1)
                                   ba=bottom_index(0,j), bb=bottom_index(0,j+1)
    háromszögek: (ba, ta, bb), (bb, ta, tb)

X+ fal (i=Nx-1),   j ∈ [0, Ny-2]: ta=top_index(Nx-1,j),    tb=top_index(Nx-1,j+1)
                                   ba=bottom_index(Nx-1,j), bb=bottom_index(Nx-1,j+1)
    háromszögek: (ba, bb, ta), (bb, tb, ta)

Y- fal (j=0),      i ∈ [0, Nx-2]: ta=top_index(i,0),    tb=top_index(i+1,0)
                                   ba=bottom_index(i,0), bb=bottom_index(i+1,0)
    háromszögek: (ba, bb, ta), (bb, tb, ta)

Y+ fal (j=Ny-1),   i ∈ [0, Nx-2]: ta=top_index(i,Ny-1),    tb=top_index(i+1,Ny-1)
                                   ba=bottom_index(i,Ny-1), bb=bottom_index(i+1,Ny-1)
    háromszögek: (ba, ta, bb), (bb, ta, tb)
```

Ez a séma garantálja a §19 szerinti kifelé mutató normálokat (Top: `+Z`, Bottom: `-Z`, X-: `-X`, X+: `+X`, Y-: `-Y`, Y+: `+Y`) és a §20 szerinti watertight zártságot, **konstrukciós tulajdonságként** (§20: *"a zártság konstrukciós tulajdonság legyen"*).

---

# 37. Hibakezelés — pontos exception-kontraktus (első implementáció)

A §29 nyitva hagyott hibakontraktusa az első implementációhoz:

* `sampling_distance ≤ 0` → hiba.
* `Nx = ⌈width / sampling_distance⌉ < 2` → hiba.
* `Ny = ⌈height / sampling_distance⌉ < 2` → hiba.
* `Nx · Ny > MAX_SAMPLE_COUNT` (kezdeti érték: `2 000 000`, §23.2) → hiba.
* A generált mesh watertight-ellenőrzése (minden rendezetlen él pontosan két háromszögben szerepel-e) sikertelen → hiba. Helyes konstrukció mellett ez elméletileg nem fordulhat elő — fail-fast védőháló, nem várt üzemi eset.

A `width ≤ 0`, `height ≤ 0`, `relief_height < 0`, `base_thickness < 0` eseteket a `ReliefGeometry` már fail-fast validálja saját konstrukciójakor (RELIEF_GEOMETRY_MODEL.md 3. lépés) — a Mesh Generatornak ezeket nem kell újra ellenőriznie.

A §28 által felsorolt további Validator-ellenőrzések (degenerált face-ek, self-intersection) a §21–22 szerint az első implementációban *"normál működés mellett nem várhatók"*, ezért ezekhez ebben a lépésben nem tartozik külön ellenőrzés vagy kivétel — ez tudatos hatókör-döntés, nem hiányosság.
