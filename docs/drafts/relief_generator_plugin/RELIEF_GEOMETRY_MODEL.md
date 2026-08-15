# RELIEF_GEOMETRY_MODEL.md

## 1. Cél

A Relief Geometry Layer feladata, hogy egy felületgenerátor által előállított, normalizált Height Fieldből fizikai méretekkel rendelkező, zárt relief-geometria leírást hozzon létre.

A réteg felelőssége a felület és a fizikai test közötti kapcsolat meghatározása.

A Relief Geometry Layer nem felelős:

* a matematikai felület előállításáért;
* a végleges mesh előállításáért;
* STL előállításáért;
* mesh-validációért;
* SliceDesigner-specifikus szeletelési műveletekért.

---

# 2. Helye a rendszerben

A teljes feldolgozási lánc:

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

A `ReliefGeometry` köztes domainmodellként működik.

Célja, hogy a felületgenerálás és a mesh-előállítás között legyen egy stabil, mesh-független geometriai reprezentáció.

---

# 3. Alapvető felelősségi határok

## Surface Generator

A Surface Generator azt határozza meg, hogy:

> milyen alakú legyen a felület.

Például:

* hullám;
* dűne;
* heightmap;
* kép alapján létrehozott felület;
* vektor alapján létrehozott felület.

Kimenete egy Height Field.

---

## Relief Geometry Layer

A Relief Geometry Layer azt határozza meg, hogy:

> a felületből milyen fizikai relief-test készüljön.

Ide tartozik:

* fizikai X/Y méret;
* reliefmagasság;
* alaptest;
* oldalfalak;
* alsó felület;
* felső felület;
* zárt test definíciója.

---

## Mesh Generator

A Mesh Generator azt határozza meg, hogy:

> a ReliefGeometry hogyan legyen háromszögekből/poligonokból álló mesh-ként reprezentálva.

A Mesh Generator nem módosítja a relief jelentését.

---

# 4. A ReliefGeometry koncepciója

A `ReliefGeometry` nem CAD-solid és nem mesh.

Egy domainmodell, amely egy fizikai relief-test szerkezetét írja le.

Logikailag:

```text
ReliefGeometry
│
├── physical_size
│
├── base
│
└── top_surface
```

ahol:

* `physical_size` a test X/Y méretét;
* `base` az alaptestet;
* `top_surface` a relief felső felületét

határozza meg.

A tényleges mesh csak később készül ebből.

---

# 5. Koordinátarendszer

A ReliefGeometry a SliceDesigner projektben használt jobbkezes koordinátarendszert követi.

Az alapfelület síkja:

```text
Z = 0
```

A fizikai méretek:

```text
X ∈ [0, width]
Y ∈ [0, height]
```

A relief a pozitív Z irányba emelkedik.

A koordinátarendszer:

```text
          +Y
           ↑
           │
           │
           └────────→ +X
          /
        +Z
```

A pontos globális koordinátarendszer-konvenció összhangban kell maradjon a SliceDesigner meglévő koordinátarendszerével.

---

# 6. A Height Field bemenete

A Geometry Layer bemenete egy normalizált Height Field:

[
H(x,y)\in[0,1]
]

A Height Field azt határozza meg, hogy az adott XY pozícióban milyen relatív reliefmagasság tartozik a felülethez.

A Geometry Layer nem feltételezheti, hogy a Height Field WaveFunctionből származik.

Ez lehet például:

```text
Wave Generator
Heightmap Generator
Image Generator
Vector Generator
```

Ez biztosítja a későbbi generátorok közös geometriai útvonalát.

---

# 7. Fizikai XY méret

A Height Field normalizált koordinátatere:

[
x,y\in[0,1]
]

A Geometry Layer ezt fizikai koordinátákra képezi le:

[
X=x\cdot width
]

[
Y=y\cdot height
]

Így ugyanaz a Height Field különböző fizikai méretekre alkalmazható.

Például ugyanaz a hullámfelület készülhet:

```text
500 × 500 mm
```

vagy:

```text
2000 × 1000 mm
```

méretben.

---

# 8. Relief magasság

A `relief_height` a felső relief-felület maximális, alaphoz viszonyított magassága.

A Height Fieldből:

[
Z_{relief}(x,y)
===============

H(x,y)\cdot relief_height
]

következik.

Ez azt jelenti:

```text
H = 0
    ↓
Zrelief = 0

H = 0.5
    ↓
Zrelief = relief_height / 2

H = 1
    ↓
Zrelief = relief_height
```

A `relief_height` nem azonos a matematikai hullám amplitúdójával.

Az amplitúdó a Surface Generator paramétere.

A `relief_height` a geometriai skálázás paramétere.

---

# 9. Alaptest

A relief egy sík alapra épül.

Az alap alsó felülete:

```text
Z = 0
```

Az alaptest biztosítja a relief mögötti szerkezeti vastagságot.

A modellben az alapvastagság külön geometriai paraméter:

```text
base_thickness
```

Az alap felső síkja:

```text
Z = base_thickness
```

A relief felső felületének magassága ehhez képest értendő.

Így a teljes modell:

[
Z_{bottom}=0
]

és

[
Z_{top}(x,y)
============

base_thickness
+
H(x,y)\cdot relief_height
]

---

# 10. A relief minimális magassága

A Height Field:

[
H\in[0,1]
]

ezért:

[
Z_{top}\geq base_thickness
]

A relief felső felülete soha nem kerülhet az alap felső síkja alá.

Ez biztosítja, hogy a bemélyedések ne okozzanak negatív geometriai vastagságot.

---

# 11. Bemélyedések

A bemélyedés nem jelent negatív Z koordinátát.

A bemélyedés relatív értelemben értendő.

Például:

```text
        /\              /\
       /  \____    ____/  \
──────────────\____/────────────
```

A mélyebb rész kisebb Z értékű, mint a környezete, de továbbra is az alaptest fölött marad.

A geometriai minimum:

[
Z_{top,min}=base_thickness
]

---

# 12. Oldalfalak

Az első Geometry Model függőleges oldalfalakat használ.

A felső felület határánál az oldalfal:

```text
top surface
     │
     │
     │
     │
─────┴──────── base
```

Az oldalfalak a relief teljes XY határán körbefutnak.

Az első implementáció nem támogat:

* döntött oldalfalat;
* lekerekített oldalfalat;
* változó vastagságú oldalfalat.

Ezek későbbi bővítések lehetnek.

---

# 13. Alsó felület

A geometria alsó felülete sík:

```text
Z = 0
```

Ez az első modellben kötelező része a testnek.

Az alsó felület biztosítja, hogy a geometria valódi zárt térfogatot alkosson.

---

# 14. Felső felület

A felső felületet a Height Field definiálja.

A felső felület:

[
S(x,y)=
(X,Y,Z_{top})
]

ahol:

[
X=x\cdot width
]

[
Y=y\cdot height
]

[
Z_{top}=base_thickness+H(x,y)\cdot relief_height
]

A felső felület alakját tehát nem a Geometry Layer találja ki.

A Geometry Layer csak fizikai koordinátákra és geometriai kontextusra helyezi.

---

# 15. A geometria zártsága

A ReliefGeometry által definiált testnek zárt térfogatot kell alkotnia.

Logikailag az alábbi felületekből áll:

```text
┌──────────────────────────┐
│       top surface        │
├──────────────────────────┤
│                          │
│        base volume       │
│                          │
├──────────────────────────┤
│       bottom surface     │
└──────────────────────────┘
```

A határoló felületek:

1. felső relief-felület;
2. alsó sík felület;
3. négy oldalfal.

Ez biztosítja a zárt geometriai modellt.

---

# 16. Watertight követelmény

A létrehozott geometriai modell célállapota watertight.

A modell nem tartalmazhat:

* nyitott határéleket;
* hiányzó oldalfalat;
* hiányzó alsó felületet;
* nem zárt felső felületet.

A Geometry Layer feladata olyan geometriai struktúrát előállítani, amelyből szabályos, zárt mesh generálható.

A végleges watertight állapotot azonban a Mesh Validator ellenőrzi.

---

# 17. Construction és Validation szétválasztása

A rendszerben a geometria előállítása és validációja külön felelősség.

```text
Generator
    ↓
Geometry Construction
    ↓
Mesh Generation
    ↓
Mesh Validation
```

A generátorok és geometriai réteg nem tartalmaznak teljes körű validációs és javítási logikát.

A validátor feladata annak ellenőrzése, hogy a létrehozott mesh megfelel-e a rendszer által meghatározott geometriai követelményeknek.

Ez a szétválasztás azért fontos, mert későbbi, összetettebb generátorok esetén nem célszerű a generátorokat egyre nagyobb validációs felelősséggel terhelni.

---

# 18. Sampling és felbontás

A Geometry Model nem rögzít konkrét mesh-felbontást.

A Height Field folytonos vagy absztrakt felületi reprezentációként kezelhető.

A tényleges mintavételezés a Mesh Generation Layer feladata.

Ez lehetővé teszi, hogy ugyanaz a ReliefGeometry különböző mesh-felbontásokban legyen előállítható.

Például:

```text
ReliefGeometry
      ↓
low resolution mesh
```

vagy:

```text
ReliefGeometry
      ↓
high resolution mesh
```

anélkül, hogy a generátort módosítani kellene.

---

# 19. Mesh-függetlenség

A ReliefGeometry nem tárol STL-t és nem használ STL-t köztes reprezentációként.

A belső feldolgozási lánc:

```text
Height Field
     ↓
ReliefGeometry
     ↓
Mesh
```

Nem megengedett az alábbi köztes út:

```text
Height Field
     ↓
Mesh
     ↓
STL
     ↓
Mesh
```

Az STL export formátumként kezelhető, de nem része a belső geometriai feldolgozásnak.

---

# 20. Mesh Generator határa

A Mesh Generator feladata a ReliefGeometry tényleges mesh-reprezentációvá alakítása.

A Mesh Generator felelős:

* mintavételezésért;
* vertexek létrehozásáért;
* face-ek létrehozásáért;
* triangulációért;
* topológia létrehozásáért.

A Relief Geometry Layer nem felelős ezek részletes megvalósításáért.

---

# 21. Későbbi bővíthetőség

A ReliefGeometry modellt úgy kell kialakítani, hogy ne kizárólag a Wave Generator számára legyen használható.

A későbbi generátorok ugyanabba a geometriai pipeline-ba illeszthetők:

```text
Wave Generator ──────┐
Heightmap Generator ─┤
Image Generator ─────┤
Vector Generator ────┤
Future Generator ────┘
            ↓
        Height Field
            ↓
      ReliefGeometry
            ↓
       Mesh Generator
            ↓
           Mesh
```

Ezért a Geometry Layer nem tartalmazhat WaveFunction-specifikus logikát.

---

# 22. Későbbi geometriai bővítések

A modell hosszú távon alkalmas lehet például:

* peremmel rendelkező reliefekre;
* nem sík alapokra;
* összetettebb oldalfalakra;
* több relieffelületre;
* lyukakat tartalmazó geometriákra;
* több geometriai régióra;
* használati tárgyakra;
* bútorok részleges vagy teljes geometriai előállítására.

Ezek nem részei az első implementációnak.

Az első modell célja a lehető legegyszerűbb, stabil geometriai alap létrehozása.

---

# 23. Első implementáció geometriai modellje

Az első implementáció minimális modellje:

```text
ReliefGeometry
│
├── width
├── height
│
├── base_thickness
├── relief_height
│
└── top_surface
        └── HeightField
```

A geometriai értelmezés:

[
X\in[0,width]
]

[
Y\in[0,height]
]

[
Z_{bottom}=0
]

[
Z_{top}(x,y)
============

base_thickness
+
H(x,y)\cdot relief_height
]

A test határa:

```text
bottom
+ top surface
+ four vertical side walls
```

---

# 24. Nem része az első implementációnak

Az első Geometry Layer nem támogat:

* döntött oldalfalakat;
* lekerekített széleket;
* peremet;
* több különálló relief-régiót;
* lyukakat;
* nem sík alapot;
* adaptív mesh-samplinget;
* mesh-optimalizálást;
* automatikus geometriajavítást.

Ezek későbbi bővítési lehetőségek.

---

# 25. Domainmodell alapelve

A ReliefGeometry célja nem egy teljes CAD-geometriai kernel létrehozása.

A cél egy **egyszerű, stabil, mesh-független domainmodell**, amely a Surface Generator és a Mesh Generator közötti határt definiálja.

Az első modell egyszerűsége tudatos.

A modellnek ugyanakkor nem szabad olyan döntéseket beégetnie, amelyek megakadályoznák a későbbi:

* kép;
* heightmap;
* vektor;
* összetett matematikai felület;
* többféle relief;
* használati tárgy;
* bútor

jellegű generátorok bevezetését.

---

# 26. Következő tervezési lépés

A Relief Geometry Model után a következő dokumentum:

**`MESH_GENERATION_MODEL.md`**

feladata a `ReliefGeometry → Mesh` átalakítás részletes megtervezése.

Ebben kell majd lezárni többek között:

* sampling stratégiát;
* resolution kezelését;
* vertex-struktúrát;
* face-struktúrát;
* triangulációt;
* oldalfalak mesh-elését;
* alsó felület mesh-elését;
* topológiai követelményeket;
* mesh watertight követelményeit;
* mesh-validáció kapcsolatát;
* és azt, hogy a létrejövő Mesh pontosan hogyan illeszkedik a SliceDesigner meglévő `MeshSource` szerződéséhez.
