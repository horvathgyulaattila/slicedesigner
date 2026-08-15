# PARAMETRIC_RELIEF_GENERATOR.md

**Státusz:** Tervezet
**Cél:** Az első matematikai alapú parametrikus Relief Generator működési és belső modelljének meghatározása
**Első generátor:** Wave Relief Generator

---

# 1. Cél

A dokumentum az első parametrikus relief-generátor konkrét működését határozza meg.

A generátor feladata:

```text
paraméterek
    ↓
matematikai felület
    ↓
magasságmező
    ↓
zárt relief-test
    ↓
Mesh
```

Az első generátor egyszerű, természetes hatású hullámzó és dűneszerű felületek előállítására szolgál.

A belső modellnek ugyanakkor lehetővé kell tennie későbbi, összetettebb generátorok hozzáadását anélkül, hogy a relief-test előállításának és Mesh-generálásának logikáját minden generátorban újra kellene írni.

---

# 2. Alapvető tervezési elv

Az első generátor képessége legyen egyszerű, a mögötte lévő modell viszont legyen bővíthető.

A rendszerben külön kell választani:

```text
GENERÁLÁS
    ↓
"milyen alakú legyen a felület?"

GEOMETRIA
    ↓
"hogyan lesz ebből relief-test?"

MESH
    ↓
"hogyan lesz a testből feldolgozható Mesh?"
```

Az első generátor nem lehet úgy kialakítva, hogy a matematikai hullámfüggvény és a teljes Mesh-generálás egyetlen elválaszthatatlan algoritmust alkosson.

---

# 3. Első generátor működési modellje

Az első generátor minimális adatfolyamata:

```text
User Parameters
       ↓
Wave Function
       ↓
Height Field
       ↓
Relief Builder
       ↓
Mesh
       ↓
Validator
```

A `MeshSource` architekturális contract ezen folyamat külső határa.

A downstream SliceDesigner számára kizárólag az érvényes `Mesh` számít. A MeshSource contract szerint a forrás-specifikus paramétermodell nem része a core contractnak.

---

# 4. Height Field mint belső köztes reprezentáció

Az első generátor belső modelljében a matematikai függvény eredménye egy magasságmezőként értelmezendő.

Formálisan:

```text
H(x,y) → z
```

ahol:

* `x` a felület X koordinátája;
* `y` a felület Y koordinátája;
* `H(x,y)` a felület magassága.

A Height Field nem azonos a Mesh-sel.

```text
Height Field
    ↓
geometriai felület
    ↓
solid
    ↓
Mesh
```

Ez lehetővé teszi, hogy később egy matematikai függvény helyett más forrás is előállíthasson Height Fieldet.

Például:

```text
Wave Generator ──────┐
Dune Generator ──────┤
Noise Generator ─────┤
Heightmap Generator ─┤
Image Generator ─────┤
                     ▼
                 Height Field
                     ↓
                Relief Builder
                     ↓
                    Mesh
```

Ez azonban nem jelent még általános HeightField Engine bevezetését.

Az első implementáció csak a szükséges minimális reprezentációt valósítja meg.

---

# 5. Normalizált magasságmodell

A belső magasságmező elsődleges reprezentációja normalizált legyen:

```text
H(x,y) ∈ [0,1]
```

A fizikai reliefmagasság külön paraméterből származik.

Például:

```text
H(x,y) = 0.0
    ↓
alapmagasság

H(x,y) = 1.0
    ↓
maximális reliefmagasság
```

A fizikai Z koordináta:

```text
z(x,y) = H(x,y) × relief_height
```

Ez az elválasztás fontos.

A matematikai generátor így nem a konkrét milliméteres méretet „tudja”, hanem egy normalizált felületet állít elő.

A fizikai méretet a geometriai réteg alkalmazza.

---

# 6. A normalizálás célja

A normalizált modell lehetővé teszi, hogy ugyanaz a generálási logika különböző fizikai méretekben működjön.

Például ugyanaz a felület:

```text
100 × 100 mm
```

vagy:

```text
1000 × 500 mm
```

méretben is előállítható.

A generátor matematikai modellje ettől nem változik.

---

# 7. Bemélyedések kezelése

A normalizált magasságmezőben:

```text
0 ≤ H(x,y) ≤ 1
```

A `0` az alapfelület.

Az `1` a maximális reliefmagasság.

A felület tehát tartalmazhat lokális minimumokat:

```text
        /\              /\
       /  \____    ____/  \
______/        \__/        \____
```

de a minimum nem mehet `0` alá.

Ez biztosítja, hogy a felső felület ne kerüljön az alapfelület alá.

---

# 8. Hullámfüggvény

Az első generátor egy matematikai hullámfüggvényből állítja elő a Height Fieldet.

Az alapmodell:

```text
H(x,y) = wave(x,y)
```

Az első verzió célja nem egyetlen „helyes” hullámforma definiálása.

A cél egy olyan parametrikus modell, amelyből:

* szabályos hullám;
* enyhén szabálytalan hullám;
* többirányú hullám;
* dűneszerű felület

is létrehozható.

---

# 9. A matematikai modell rétegezése

A hullámfüggvényt célszerű komponensekből felépíteni.

Kezdetben:

```text
base function
```

Később:

```text
base function
     +
secondary component
     +
variation
     +
noise
```

Például koncepcionálisan:

```text
H_raw(x,y) =
    Wave_1(x,y)
    +
    Wave_2(x,y)
    +
    Noise(x,y)
```

Az első generátor nem köteles mindegyik komponenst támogatni.

A modell azonban ne akadályozza ezek későbbi hozzáadását.

---

# 10. Természetes hatás

Az első generátor célja nem a tökéletesen szabályos szinuszhullám.

A természetesebb megjelenés érdekében a generátor későbbi változatai támogathatnak:

* több hullámkomponenst;
* eltérő irányokat;
* eltérő hullámhosszakat;
* amplitúdóváltozást;
* fáziseltolást;
* lokális szabálytalanságot;
* zajkomponenst.

Az első verzióban ezek közül csak a szükséges minimum kerül implementálásra.

---

# 11. Paramétermodell

Az első generátor paraméterei két logikai csoportba tartoznak.

## Geometriai paraméterek

```text
width
height
base_thickness
relief_height
```

Ezek a fizikai méretet és a test alapvető geometriai méreteit határozzák meg.

## Generálási paraméterek

Az első generátor várható paraméterei:

```text
wave_count
wave_length
amplitude
direction
phase
irregularity
```

A végleges paraméternevek és tartományok a konkrét implementációs specifikációban kerülnek rögzítésre.

---

# 12. Emberi paraméterek

A felhasználói paraméterezés ne közvetlenül a matematikai függvény minden belső változóját tegye elérhetővé.

A felhasználó számára elsősorban értelmezhető fogalmak legyenek:

```text
Hullámok száma
Hullámhossz
Hullámmagasság
Irány
Szabálytalanság
```

A generátor ezeket belső matematikai paraméterekké alakítja.

Ez lehetővé teszi, hogy később a matematikai modell komplexebbé váljon anélkül, hogy a felhasználói paraméterezést feltétlenül ugyanilyen mértékben kellene bonyolítani.

---

# 13. Fizikai méret

A generátor fizikai méretben dolgozik.

A fő méretparaméterek:

```text
width
height
```

A generált relief ezeknek megfelelő fizikai kiterjedésű lesz.

A generátor nem feltételez fix munkadarabméretet.

A modell ezért alkalmas lehet:

* kis dekorációs elemek;
* falpanelek;
* nagyobb táblák;
* korlátok;
* későbbi nagyobb felületek

előállítására is.

---

# 14. Alapvastagság és reliefmagasság

A test két külön geometriai dimenzióból áll:

```text
base_thickness
+
relief_height
```

Például:

```text
                 max Z
                   ↑
                   │
          ~~~~~~~~~~~~~~~~
       ~~~              ~~~
     ~~                    ~~
    │                       │
    │       base            │
    └───────────────────────┘
             ↑
        base surface
```

A `base_thickness` a teljes test alsó, sík részének vastagsága.

A `relief_height` a felső felület maximális kiemelkedése az alapfelülethez képest.

---

# 15. Fizikai koordináták

A Height Field normalizált koordinátákon vagy a generátor által meghatározott lokális tartományon értelmezhető.

A geometriai réteg a felhasználó által megadott fizikai méretre skálázza:

```text
normalized X
      ↓
physical X

normalized Y
      ↓
physical Y
```

A Z koordináta:

```text
base_thickness + H(x,y) × relief_height
```

Ez azt jelenti, hogy a teljes test legalacsonyabb pontja nem feltétlenül `Z = 0`.

A modellben:

```text
bottom = 0
top_min = base_thickness
top_max = base_thickness + relief_height
```

Ez tisztán elválasztja:

* a test vastagságát;
* a relief relatív magasságát.

---

# 16. Mintavételezés

A folytonos Height Fieldből diszkrét pontokból álló felület készül.

```text
continuous function
        ↓
sampling grid
        ↓
height values
        ↓
surface mesh
```

Az első generátor rácsalapú mintavételezést használhat.

A mintavételi rács:

```text
Nx × Ny
```

pontból áll.

A pontos triangulációs algoritmus ebben a dokumentumban még nincs rögzítve.

---

# 17. Fizikai felbontás

A mintavétel elsődleges paramétere fizikai felbontás legyen.

Koncepcionálisan:

```text
sample_spacing_x
sample_spacing_y
```

vagy egy közös:

```text
sample_spacing
```

érték.

Ez előnyösebb, mint kizárólag fix vertexszám használata, mert a generált geometria fizikai méretéhez igazodik.

---

# 18. Felbontás és számítási költség

A felbontás közvetlenül befolyásolja a Mesh méretét.

Ha:

```text
width  = 1000 mm
height = 500 mm
spacing = 1 mm
```

akkor nagyságrendileg:

```text
1001 × 501
```

mintapont keletkezhet.

A pontos pontszám a későbbi mintavételi definíció része.

A rendszernek ezért figyelembe kell vennie a felhasználó által kért fizikai felbontásból következő számítási és memóriaigényt.

---

# 19. Adaptív felbontás

Az adaptív mintavételezés **nem része az első generátor minimális implementációjának**.

Hosszú távon azonban indokolt lehet.

Például ott érdemes több mintapontot használni, ahol:

* nagy a felület görbülete;
* gyorsan változik a magasság;
* finom részletek jelennek meg.

A későbbi adaptív mintavételezés nem változtathatja meg a Height Field fogalmát.

Ez backlog-tétel.

---

# 20. Height Field → Relief

A Height Field önmagában még nem szilárd test.

A Relief Builder feladata:

```text
Height Field
      ↓
Top Surface
      +
Bottom Surface
      +
Side Walls
      ↓
Closed Solid
```

Ez a réteg nem tudhatja, hogy a Height Field:

* hullámgenerátorból;
* dűnegenerátorból;
* zajgenerátorból;
* heightmapből;
* képből

származik.

---

# 21. Top Surface

A Top Surface a Height Fieldből származó felső felület.

A mintavételezett pontokból háromszögek készülnek.

Koncepcionálisan:

```text
p00 ───── p10
 │      / │
 │    /   │
 │  /     │
p01 ───── p11
```

A cellák triangulálása adja a felső Mesh-felületet.

A konkrét triangulációs megvalósítás implementációs döntés.

---

# 22. Bottom Surface

A Bottom Surface sík.

```text
Z = 0
```

A test teljes alsó felülete ehhez a síkhoz tartozik.

A Bottom Surface nem függ a generátor matematikai függvényétől.

---

# 23. Side Walls

A Top Surface határán lévő pontokat a Bottom Surface megfelelő határpontjaival kell összekötni.

```text
top boundary
    │
    │ side wall
    │
bottom boundary
```

A négy külső oldal:

```text
left
right
front
back
```

zárt testet hoz létre.

---

# 24. Relief Builder általánosíthatósága

A Relief Builder legyen független a generátortól.

Ez az első generátor egyik legfontosabb jövőbeli bővíthetőségi követelménye.

A cél:

```text
Wave Generator
      ↓
Height Field
      ↓
       ┐
Dune Generator
      ↓         │
Height Field ───┤
                ↓
          Relief Builder
                ↓
               Mesh
```

Így új generátor hozzáadásakor nem kell újra implementálni:

* az alapfelületet;
* az oldalfalakat;
* a zárt test logikáját;
* a Mesh összeállítását.

---

# 25. Height Field → Mesh határ

A rendszerben fontos határvonal:

```text
Generator
    ↓
Height Field
```

és:

```text
Relief Builder
    ↓
Mesh
```

A generátor nem felelős a MeshSource contract teljesítéséért.

A generátor egy geometriai reprezentációt állít elő.

A Relief Builder állítja elő a zárt Mesh-t.

A MeshSource ezt a folyamatot a plugin külső szerződésén keresztül teszi elérhetővé.

---

# 26. Validáció

A generálás után a Mesh validálása kötelező.

```text
Mesh
 ↓
Validator
```

A validator legalább az alábbiakat ellenőrzi:

* zártság;
* watertight állapot;
* degenerált geometriai elemek;
* topológiai konzisztencia;
* alapvető geometriai érvényesség.

A generátor nem támaszkodhat a validatorra hibás geometria javítására.

A `MeshSource` contract szerint érvénytelen bemenet vagy eredmény esetén fail-fast működés szükséges.

---

# 27. Generátor és Validator kapcsolata

A helyes modell:

```text
Generator
    ↓
saját specifikációjának megfelelő eredmény
    ↓
Validator
    ↓
ellenőrzés
```

Nem:

```text
Generator
    ↓
"valami Mesh"
    ↓
Validator
    ↓
"javítsd ki"
```

A validator nem geometriai javítóalgoritmus.

---

# 28. Determinizmus

Azonos paraméterek esetén a generátornak azonos Height Fieldet és azonos geometriai eredményt kell előállítania.

```text
parameters A
     ↓
Height Field A

parameters A
     ↓
Height Field A
```

Az első generátor nem igényel randomizációt.

Ha később szabálytalanság vagy zaj kerül a modellbe, annak reprodukálható seed segítségével kell működnie.

Ez összhangban van a `MeshSource` determinisztikus működésére vonatkozó contracttal.

---

# 29. Paraméterváltozás

A generátor stateless újragenerálási modellben működjön.

```text
Parameters A
     ↓
Mesh A

Parameters B
     ↓
Mesh B
```

A paraméterváltozás nem igényli a korábbi Mesh módosítását.

Az optimalizált inkrementális újraszámítás későbbi fejlesztési lehetőség.

Nem része az első implementációnak.

---

# 30. Bővíthetőségi modell

A rendszer hosszú távú bővíthetőségének alapelve:

> **Új generátor lehetőleg csak a Height Field előállításának módját változtassa meg.**

Ideális esetben:

```text
Wave Generator
Dune Generator
Noise Generator
Heightmap Generator
Image Generator
Vector Generator
       │
       ▼
  Height Field
       │
       ▼
Relief Builder
       │
       ▼
      Mesh
```

A közös réteg felelőssége csak az legyen, amit valóban minden ilyen generátor használ.

---

# 31. Későbbi összetett generátorok

Az első Wave Generator később összetettebbé válhat.

Például:

```text
Wave A
   +
Wave B
   +
Noise
   +
Directional deformation
   ↓
Height Field
```

A rendszernek ezt úgy kell lehetővé tennie, hogy a Relief Builder és a MeshSource contract változatlan maradhasson.

---

# 32. Dűnegenerátor

A dűneszerű felület később külön generátor lehet.

Nem szükséges az első Wave Generatorba beépíteni.

```text
Wave Generator
       ↓
Height Field

Dune Generator
       ↓
Height Field
```

Mindkettő ugyanazt a Relief Builder réteget használhatja.

---

# 33. Heightmap generátor

A későbbi Heightmap Generator:

```text
heightmap
    ↓
Height Field
    ↓
Relief Builder
    ↓
Mesh
```

A bemeneti kép felbontása ebben az esetben természetes korlátot jelent.

Ezért az első generátor fizikai mintavételi modelljét nem szabad a későbbi Heightmap Generatorra ráerőltetni.

---

# 34. Image generátor

A későbbi Image Generator eltérő feldolgozási lépéseket igényelhet:

```text
image
  ↓
image analysis
  ↓
height interpretation
  ↓
Height Field
  ↓
Relief Builder
```

Az első generátor nem tartalmazhatja előre ennek a logikáját.

---

# 35. Vector generátor

A vektoros bemenet nem feltétlenül közvetlen Height Field.

Lehetséges jövőbeli modell:

```text
vector geometry
      ↓
surface interpretation
      ↓
Height Field
      ↓
Relief Builder
```

Ez külön domain- és algoritmikai kérdés.

Nem része az első generátornak.

---

# 36. Általános Surface Engine

A projekt hosszú távú célja lehet egy általánosabb felületgeneráló motor.

Az első generátor azonban nem hozza létre ezt teljes formájában.

A jelen dokumentum csak azokat az absztrakciókat vezeti be, amelyeket az első generátor és a már meghatározott jövőbeli irányok indokolnak:

```text
Generator
    ↓
Height Field
    ↓
Relief Builder
    ↓
Mesh
```

További absztrakció csak konkrét új igény megjelenésekor vezethető be.

---

# 37. Hibás paraméterek

Érvénytelen paraméterkombináció esetén a generátor nem készíthet tetszőleges eredményt.

Példák:

* nulla vagy negatív fizikai méret;
* negatív reliefmagasság;
* nulla vagy negatív mintavételi távolság;
* értelmezhetetlen hullámparaméter;
* túl nagy felbontás, amely a megengedett erőforrás-korlátot meghaladja.

A generátor explicit hibát jelez.

Nem alkalmaz csendes korrekciót.

Ez megfelel a `MeshSource` fail-fast contractjának.

---

# 38. Geometriai invariánsok

A Relief Generator teljes eredményére érvényes:

```text
width > 0
height > 0
base_thickness > 0
relief_height >= 0
```

A Height Fieldre:

```text
0 ≤ H(x,y) ≤ 1
```

A végső testre:

```text
bottom Z = 0
top Z ≥ base_thickness
top Z ≤ base_thickness + relief_height
```

A Meshre:

```text
closed
watertight
valid
```

---

# 39. Első implementáció minimális modellje

Az első implementáció minimális belső modellje:

```text
WaveParameters
       ↓
WaveFunction
       ↓
HeightField
       ↓
ReliefBuilder
       ↓
Mesh
       ↓
Validator
```

Nem szükséges első verzióban:

* több generátor;
* node-alapú felületépítés;
* adaptív mesh;
* komplex zajrendszer;
* általános Surface Graph;
* általános geometriai CSG;
* több különálló relief-test;
* lyukak generálása;
* bútor- vagy tárgygenerálási logika.

---

# 40. Amit az első implementációval szándékosan nem oldunk meg

A következő képességek backlogként kezelendők:

* összetett többkomponensű hullámrendszer;
* fejlett zajmodellek;
* adaptív mintavételezés;
* lokális felbontásvezérlés;
* heightmap bemenet;
* képalapú generálás;
* vektoros generálás;
* többféle relief-típus;
* lyukakat tartalmazó általános topológia;
* több különálló test;
* használati tárgyak generálása;
* bútor-generálás;
* általános Surface Engine;
* paraméterekből felépített generálási gráf.

Ezek nem elveszett képességek, hanem tudatosan későbbre hagyott bővítési irányok.

---

# 41. Nem része a dokumentumnak

A dokumentum nem határozza meg:

* konkrét Python osztályneveket;
* konkrét Python package struktúrát;
* konkrét Mesh library használatát;
* konkrét triangulációs algoritmust;
* konkrét validator libraryt;
* plugin discovery mechanizmust;
* plugin telepítési folyamatot;
* GUI implementációt;
* STL exportot.

Ezek az implementációs terv későbbi részei.

---

# 42. Kapcsolódás a MeshSource contracthoz

A Relief Generator plugin a következő határon keresztül illeszkedik a SliceDesignerhez:

```text
Relief-specific parameters
          ↓
     Relief Generator
          ↓
         Mesh
```

A core számára a relief-specifikus paramétermodell nem kötelező.

A `MeshSource` contract kifejezetten source-specifikus paramétermodelleket enged meg.

A generált Mesh közvetlenül kerül a SliceDesigner pipeline-ba.

Nincs:

```text
Relief Generator
    ↓
STL
    ↓
STL Import
    ↓
Mesh
```

A korábban elfogadott architekturális döntés szerint ez szükségtelen serializáció lenne.

---

# 43. Felelősségi összefoglaló

| Komponens      | Felelősség                                   |
| -------------- | -------------------------------------------- |
| Wave Generator | Matematikai felület előállítása              |
| Height Field   | A felület magassági reprezentációja          |
| Relief Builder | Height Fieldből zárt test létrehozása        |
| Mesh Builder   | Geometria Mesh-re alakítása                  |
| Validator      | Mesh érvényességének ellenőrzése             |
| MeshSource     | A plugin és a SliceDesigner közötti contract |
| Project        | Folyamat koordinációja                       |
| GUI            | Paraméterek megadása és megjelenítése        |

A konkrét osztályok vagy modulok nevei még nem részei ennek a dokumentumnak.

---

# 44. Impact Analysis

## Érintett dokumentumok

Közvetlenül:

* `PARAMETRIC_RELIEF_GENERATOR.md`

Kapcsolódó:

* `RELIEF_GENERATOR_DOMAIN.md`
* `MESH_SOURCE.md`
* `ADR_MESH_SOURCE.md`
* `PLUGIN_ARCHITECTURE.md`
* `DOMAIN_MODEL.md`

A `MESH_SOURCE.md` contract módosítása nem szükséges.

## Érintett könyvtárak

Dokumentációs szinten:

```text
docs/
```

Implementációs könyvtár ebben a dokumentumban még nem kerül meghatározásra.

## Új dokumentációs döntés

A Height Field itt belső köztes reprezentációként jelenik meg.

Ez nem egy teljes általános HeightField contract bevezetése.

Ha a későbbi generátorok közös, különálló HeightField contractot igényelnek, azt külön dokumentációs döntésként kell kezelni.

## Szükséges ADR

Jelen dokumentum önmagában nem igényel új ADR-t, amennyiben a Height Field csak a generátor belső modelljének része marad.

Új ADR szükséges, ha később a Height Field:

* önálló domainobjektummá válik;
* pluginok közötti szerződéssé válik;
* több generátor közös architekturális contractjává válik;
* vagy a Relief Builder önálló core architekturális komponenssé válik.

## Visszafelé kompatibilitás

A meglévő STL-alapú MeshSource működését nem módosítja.

A downstream pipeline változatlan Mesh bemenetet kap.

A Relief Generator opcionális marad.

---

# 45. Elfogadási kritériumok

A dokumentum akkor tekinthető elfogadottnak, ha:

1. meghatározza az első Wave Generator célját;
2. elválasztja a generálási modellt a geometriaépítéstől;
3. meghatározza a Height Field szerepét;
4. meghatározza a normalizált magasságmodellt;
5. meghatározza a fizikai méret kezelését;
6. meghatározza a reliefmagasság kezelését;
7. meghatározza a mintavétel alapelvét;
8. meghatározza a Relief Builder szerepét;
9. meghatározza a top surface, bottom surface és side walls kapcsolatát;
10. rögzíti a watertight Mesh követelményt;
11. különválasztja a generátort és a validátort;
12. rögzíti a fail-fast működést;
13. rögzíti a determinisztikus működést;
14. lehetővé teszi a későbbi összetettebb generátorokat;
15. nem kényszeríti a későbbi generátorokat az első hullámfüggvény modelljére;
16. nem vezet be előre teljes Surface Engine-t;
17. nem módosítja a MeshSource contractot;
18. megőrzi a SliceDesigner downstream pipeline változatlanságát;
19. világosan kijelöli a későbbi bővítések helyét;
20. az első implementáció továbbra is egyszerű marad.

---

# 46. Célállapot

Az első generátor:

```text
                  Wave Parameters
                         │
                         ▼
                  Wave Generator
                         │
                         ▼
                    Height Field
                         │
                         ▼
                  Relief Builder
                  /      |      \
                 /       |       \
              Top      Bottom    Sides
                 \       |       /
                  \      |      /
                   └─────┬─────┘
                         ▼
                        Mesh
                         │
                         ▼
                     Validator
                         │
                   ┌─────┴─────┐
                   │           │
                 valid       invalid
                   │           │
                   ▼           ▼
              MeshSource      Error
                   │
                   ▼
               SliceDesigner
```

A hosszabb távú cél:

```text
Wave Generator ──────┐
Dune Generator ──────┤
Noise Generator ────┤
Heightmap Generator ┤
Image Generator ────┤
Vector Generator ───┤
                     ▼
                Height Field
                     │
                     ▼
               Relief Builder
                     │
                     ▼
                    Mesh
```

A második diagram a bővíthetőségi irányt mutatja, nem az első implementáció követelményét.

---

# 47. Státusz

**Tervezet — projektgazdai jóváhagyásra vár.**
