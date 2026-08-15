# IMPLEMENTATION_PLAN.md

## 1. Cél

A dokumentum célja a parametrikus relief-generátor első implementációjának végrehajtható tervvé alakítása.

A terv kizárólag a már elfogadott architekturális és domain döntésekből indul ki.

Nem vezet be új architekturális döntést.

A cél az első működő rendszer:

```text
Wave Generator
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

A parametrikus relief-generátor opcionális plugin marad. A SliceDesigner core működéséhez nem szükséges. Ez összhangban van a `MeshSource` döntéssel. 

---

# 2. Hatókör

Az első implementáció kizárólag:

* matematikai Wave Generatort;
* annak Height Field kimenetét;
* `ReliefGeometry` modellt;
* szabályos sampling alapú Mesh Generatort;
* watertight relief mesh előállítást;
* `MeshSource` integrációt;
* minimális plugin-integrációt

valósít meg.

Nem cél az első implementációban:

* image generator;
* heightmap generator;
* vector generator;
* adaptív mesh;
* mesh optimization;
* mesh repair;
* összetett CAD-geometria;
* lyukakat tartalmazó relief;
* bútor- vagy tárgygenerátor;
* önálló alkalmazás.

Ezek későbbi bővítési lehetőségek.

---

# 3. Meglévő architektúrához való illeszkedés

A SliceDesigner meglévő háromrétegű modellje nem változik:

```text
GUI
 ↓
Project
 ↓
Domain
```

A `MeshSource` a Domain rétegen belül helyezkedik el.

Az új pipeline:

```text
GUI
 ↓
Project
 ↓
MeshSource
 ↓
Mesh
 ↓
Slice Engine
 ↓
további engine-ek
```

A downstream pipeline-nak nem kell tudnia, hogy a Mesh STL-ből vagy generátorból származik. 

---

# 4. Plugin-határ

A parametrikus relief-generátor külön Python package-ként kezelendő.

A plugin:

* nem kerül a SliceDesigner core-ba;
* saját domain logikával rendelkezik;
* saját generátorokat tartalmazhat;
* a `MeshSource` contracton keresztül kapcsolódik a core-hoz;
* közvetlenül `Mesh`-t ad a core számára.

A plugin hiánya nem okozhat hibát a SliceDesigner működésében. 

---

# 5. Implementációs rétegek

Az első implementáció négy fő belső részből áll.

```text
relief plugin
│
├── surface
│   └── Wave Generator
│
├── geometry
│   └── ReliefGeometry
│
├── mesh
│   └── Mesh Generator
│
└── source
    └── MeshSource adapter
```

A pontos Python package- és könyvtárstruktúrát az aktuális repository struktúrájához kell igazítani.

Nem cél önálló, párhuzamos architektúra létrehozása a SliceDesigner meglévő szerkezete mellett.

---

# 6. Wave Generator

## 6.1. Feladat

A Wave Generator feladata egy matematikai függvényből Height Field előállítása.

Az első implementáció alapfüggvénye:

[
F(x,y)=
\sum_{i=1}^{n}
A_i
\sin
\left(
\lambda_i 2\pi
(x\cos\theta_i+y\sin\theta_i)
+\phi_i
\right)
]

ahol:

* (A_i) — amplitúdó;
* (\lambda_i) — hullámhosszhez kapcsolódó frekvenciaparaméter;
* (\theta_i) — hullám iránya;
* (\phi_i) — fázis;
* (n) — komponensek száma.

---

# 7. Direction Spread

A Wave Generator támogatja a direction spread paramétert.

Ez nem változtatja meg a hullámfüggvény alapvető szerkezetét.

A direction spread a komponensek (\theta_i) irányértékeinek eloszlását szabályozza.

Ez lehetővé teszi:

```text
szabályos párhuzamos hullámok
          ↓
enyhén változó irányú hullámok
          ↓
összetettebb természetes hullámstruktúra
```

A direction spread kezelése a Wave Generator felelőssége.

A Geometry Layer erről semmit nem tud.

---

# 8. Wave Generator kimenete

A Wave Generator nem Mesh-t állít elő.

Kimenete egy Height Field.

```text
Wave parameters
      ↓
Wave Generator
      ↓
Height Field
```

Ez fontos architekturális határ.

A Wave Generator nem tartalmazhat:

* base thickness logikát;
* fizikai testgenerálást;
* oldalfal-generálást;
* STL-exportot;
* Mesh-topológiai logikát.

---

# 9. Height Field

A Height Field a Surface Generator és a Geometry Layer közötti közös reprezentáció.

Az első implementációban:

[
H(x,y)\in[0,1]
]

A normalizálás biztosítja, hogy a geometriai magasságot később a `relief_height` paraméter szabályozhassa.

```text
raw wave
   ↓
normalization
   ↓
Height Field [0,1]
```

A Height Field nem lehet Wave Generator-specifikus.

Ez teszi lehetővé később:

```text
Wave
Heightmap
Image
Vector
...
   ↓
Height Field
```

pipeline kialakítását.

---

# 10. ReliefGeometry

A Geometry Layer bemenete:

```text
Height Field
```

Kimenete:

```text
ReliefGeometry
```

Az első modell:

```text
ReliefGeometry
├── width
├── height
├── base_thickness
├── relief_height
└── top_surface
      └── HeightField
```

A felső felület:

[
Z_{top}(x,y)
============

base_thickness
+
H(x,y)\cdot relief_height
]

A modell alsó síkja:

[
Z=0
]

A relief tehát soha nem megy negatívba.

---

# 11. Mesh Generation

A Mesh Generator feladata:

```text
ReliefGeometry
      ↓
Mesh
```

Az első implementáció:

* szabályos XY rácsot használ;
* explicit resolution paramétert használ;
* a felső felületet triangulálja;
* létrehozza az alsó síkot;
* létrehozza a négy oldalfalat;
* zárt mesh-t állít elő.

Az adaptív sampling nem része az első implementációnak.

---

# 12. Sampling

A Mesh Generator két dimenzióban mintavételez:

```text
Nx × Ny
```

A fizikai lépésköz:

[
\Delta x=\frac{width}{N_x-1}
]

[
\Delta y=\frac{height}{N_y-1}
]

A fizikai méret és a resolution egymástól független.

Ez különösen fontos nagy falpanelek esetében.

Egy nagy fizikai méretű modell nem kell automatikusan nagyobb mesh-sűrűséget jelentsen.

---

# 13. Mesh felépítése

A mesh logikailag:

```text
Top Surface
Bottom Surface
Side Wall X-
Side Wall X+
Side Wall Y-
Side Wall Y+
```

A felső felület minden cellája két háromszögből áll.

A bottom és side surfaces szintén háromszögekből épülnek.

A face-orientációknak kifelé mutató normálokat kell eredményezniük.

---

# 14. Watertight követelmény

A parametrikus relief-generátor első implementációjának kimenete zárt, watertight Mesh.

A Mesh nem adható át a SliceDesignernek tudottan hibás állapotban.

Ez összhangban van a `MeshSource` fail-fast követelményével. 

A validáció külön felelősség.

```text
Mesh Generator
      ↓
Mesh
      ↓
Validator
      ↓
valid / error
```

A generátor nem tartalmaz általános mesh-repair rendszert.

---

# 15. MeshSource adapter

A plugin MeshSource rétege a plugin belső generálási láncát a SliceDesigner contractjához illeszti.

```text
parameters
     ↓
Wave Generator
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
```

A SliceDesigner felé kizárólag a contract által meghatározott Mesh jelenik meg.

A downstream pipeline nem kap plugin-specifikus objektumokat.

---

# 16. Paraméterváltozás

Az első generátor determinisztikus és újragenerálható.

Ha a felhasználó módosít egy generátorparamétert:

```text
parameter change
      ↓
new generation
      ↓
new Height Field
      ↓
new ReliefGeometry
      ↓
new Mesh
```

Nem cél az első implementációban részleges mesh-frissítés vagy inkrementális újraszámítás.

A teljes újragenerálás egyszerűbb és stabilabb.

---

# 17. Validáció

A validációt két szinten kell kezelni.

## Input validation

A generálás előtt ellenőrizni kell például:

* pozitív fizikai méretek;
* érvényes amplitúdók;
* érvényes hullámhosszok;
* érvényes resolution;
* érvényes base thickness;
* érvényes relief height.

## Mesh validation

A generálás után ellenőrizhető:

* watertight állapot;
* boundary edge-ek;
* degenerált face-ek;
* topológiai konzisztencia;
* normálirányok;
* geometriai határok.

---

# 18. Hibakezelés

A generálás fail-fast.

Érvénytelen bemenet esetén:

```text
invalid input
     ↓
explicit error
```

Nem:

```text
invalid input
     ↓
automatikus, dokumentálatlan korrekció
     ↓
valamilyen Mesh
```

Ez összhangban van a projekt determinisztikus és fail-fast működési elveivel, amelyeket a `MeshSource` contract is rögzít. 

---

# 19. Tesztelési stratégia

Az implementációt rétegenként kell tesztelni.

## Wave Generator

Tesztelendő:

* determinisztikus kimenet;
* paraméterek hatása;
* normalization;
* direction;
* direction spread;
* több hullámkomponens.

## Height Field

Tesztelendő:

* értéktartomány;
* koordinátakezelés;
* determinisztikus lekérdezés.

## ReliefGeometry

Tesztelendő:

* fizikai méretezés;
* Z minimum;
* Z maximum;
* base thickness;
* relief height;
* bemélyedések nem mennek az alap alá.

## Mesh Generator

Tesztelendő:

* vertexszám;
* face-szám;
* trianguláció;
* bounding box;
* topológiai zártság;
* watertight állapot;
* normálirányok.

## MeshSource

Tesztelendő:

* contract kompatibilitás;
* közvetlen Mesh-kimenet;
* plugin nélküli core működés;
* determinisztikus eredmény;
* hibakezelés.

---

# 20. Integrációs teszt

A minimális végponttól végpontig teszt:

```text
Wave Parameters
      ↓
Wave Generator
      ↓
Height Field
      ↓
ReliefGeometry
      ↓
Mesh Generator
      ↓
Validator
      ↓
MeshSource
      ↓
SliceDesigner
      ↓
Slice Engine
```

A teszt célja annak bizonyítása, hogy az új modellforrás nem igényel külön slicing pipeline-t.

Ez közvetlenül követi a `MeshSource` architekturális döntését. 

---

# 21. Implementáció sorrendje

A tényleges fejlesztés sorrendje:

### 1. Height Field alap

A közös felületi reprezentáció minimális implementációja.

### 2. Wave Generator

Az első matematikai generátor implementálása.

### 3. ReliefGeometry

A Height Field fizikai relief-geometriává alakítása.

### 4. Mesh Generator

A ReliefGeometry szabályos rácsos mesh-é alakítása.

### 5. Mesh Validation

A létrejövő mesh alapvető érvényességének ellenőrzése.

### 6. MeshSource adapter

A plugin csatlakoztatása a SliceDesigner contractjához.

### 7. Minimális GUI-integráció

A generátor kiválasztása és paramétereinek megadása.

### 8. End-to-end teszt

A teljes pipeline ellenőrzése.

---

# 22. GUI első változata

Az első GUI nem célja a teljes generátor-rendszer kialakítása.

A minimális felület csak a szükséges paramétereket tegye elérhetővé.

Például:

```text
Generator:
[ Wave ▼ ]

Width:
[       ]

Height:
[       ]

Base thickness:
[       ]

Relief height:
[       ]

Resolution:
[       ]

Wave parameters:
...
```

A későbbi:

```text
Wave
Heightmap
Image
Vector
...
```

generátorválasztás ugyanebbe az általános struktúrába illeszthető.

---

# 23. Nem implementálandó optimalizációk

Az első implementáció során nem kerülhetnek be „mellékesen”:

* adaptív sampling;
* cache-rendszer;
* GPU-gyorsítás;
* mesh decimation;
* automatikus remeshing;
* párhuzamosított generálás;
* bonyolult preview-optimalizáció;
* automatikus mesh repair.

Ezek külön backlog-elemek.

Ez fontos a projekt végrehajtási szabálya miatt: az optimalizáció nem változtathatja meg az aktuális implementációs feladat fókuszát.

---

# 24. Első implementáció elfogadási kritériumai

Az első implementáció akkor tekinthető funkcionálisan késznek, ha:

* a Wave Generator determinisztikusan Height Fieldet állít elő;
* a Height Field `[0,1]` tartományba normalizálható;
* a ReliefGeometry fizikai méretekkel rendelkezik;
* a relief nem kerül az alaptest alá;
* a Mesh Generator zárt mesh-t állít elő;
* a mesh watertight;
* a mesh közvetlenül `Mesh` formában továbbítható;
* nincs STL-köztes lépés;
* a MeshSource contract teljesül;
* a SliceDesigner plugin nélkül továbbra is működik;
* a plugin külön telepíthető;
* a teljes pipeline végigtesztelhető;
* az első generátor módosítható paraméterekkel újragenerálható.

---

# 25. Dokumentációs függőségek

Az implementáció az alábbi elfogadott dokumentumokra támaszkodik:

```text
MESH_SOURCE.md
       ↓
ADR_MESH_SOURCE.md
       ↓
plugin architecture
       ↓
RELIEF_GENERATOR_DOMAIN.md
       ↓
RELIEF_GEOMETRY_MODEL.md
       ↓
MESH_GENERATION_MODEL.md
       ↓
IMPLEMENTATION_PLAN.md
```

A `MeshSource` contract már rögzíti, hogy a plugin saját domain logikája nem kerülhet a core-ba, és a relief-generátor első opcionális MeshSource lesz. 

---

# 26. Hatókörön kívüli későbbi fejlesztések

A jelen tervből később backlogként származhat:

* Heightmap Generator;
* Image Generator;
* Vector Generator;
* koncentrikus/radiális hullámforrások;
* összetettebb hullámforrás-modellek;
* több hullámforrás;
* természetesebb noise-alapú felületek;
* adaptív sampling;
* curvature-based resolution;
* nagy modellek optimalizált kezelése;
* komplex relief-geometriák;
* lyukakkal rendelkező modellek;
* használati tárgyak;
* bútorgeometriák.

Ezek nem módosítják az első implementáció feladatát.

---

# 27. Végállapot

Az első implementáció végén a következő architektúrának kell működnie:

```text
                    SliceDesigner Core
                           │
                           │ MeshSource
                           │
                  ┌────────▼────────┐
                  │ Relief Plugin   │
                  │                 │
                  │ Wave Generator  │
                  │       ↓         │
                  │ Height Field    │
                  │       ↓         │
                  │ ReliefGeometry  │
                  │       ↓         │
                  │ Mesh Generator  │
                  │       ↓         │
                  │      Mesh       │
                  └────────┬────────┘
                           │
                           ▼
                         Mesh
                           │
                           ▼
                     Slice Engine
```

A plugin egyetlen, jól definiált ponton kapcsolódik a core-hoz:

```text
Relief Plugin → MeshSource → Mesh
```

A plugin belső felépítése a SliceDesigner downstream engine-jeitől független.

---

# 28. Státusz

**Tervezet — implementáció előtt jóváhagyásra vár.**

A dokumentum nem tartalmaz új architekturális döntést; az eddig elfogadott `MeshSource`, relief domain, geometry és mesh-generation döntésekből vezeti le a végrehajtás sorrendjét.

**Ezzel a dokumentummal a tervezési szakasz lényegében eljutott az első implementálható ponthoz.** A következő projektgazdai döntés már ennek a tervnek az elfogadása, utána pedig jöhet az implementációs munka.
