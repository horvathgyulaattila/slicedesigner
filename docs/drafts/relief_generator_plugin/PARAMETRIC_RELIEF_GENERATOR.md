# Parametric Relief Generator

## 1. Cél

A Parametric Relief Generator feladata, hogy paraméterezhető matematikai függvényekből olyan Height Fieldet állítson elő, amely később fizikai relief geometriává alakítható.

Az első generátor célja természetes hatású, hullám- és dűneszerű felületek létrehozása.

A generátor hosszú távú célja egy általánosabb parametric surface generation rendszer alapjainak megteremtése.

Az első implementáció ennek csak egy korlátozott részhalmazát valósítja meg.

---

## 2. Helye a rendszerben

A generátor a következő feldolgozási lánc része:

```text
Generator Parameters
        ↓
Wave Function
        ↓
Normalized Height Field
        ↓
Relief Geometry
        ↓
Mesh
        ↓
MeshSource
```

A Parametric Relief Generator nem foglalkozik közvetlenül a SliceDesigner MeshSource contractjával.

A generátor feladata a matematikai felület előállítása.

---

## 3. Első generátor

Az első generátor **Directional Wave Generator**.

Ez több, egymással kombinált irányított síkhullám-komponensből állít elő felületet.

Alapmodellje:

[
F(x,y)=
\sum_{i=1}^{n}
A_i
\sin
\left(
\frac{2\pi}{\lambda_i}
(x\cos\theta_i+y\sin\theta_i)
+\phi_i
\right)
]

A részletes matematikai modell meghatározását a `WAVE_FUNCTION_MODEL.md` tartalmazza.

---

# 4. Generátorparaméterek

Az első generátor magas szintű paramétereket használ.

A felhasználónak nem kell az egyes hullámkomponensek matematikai paramétereit külön szerkesztenie.

A generátor ezekből determinisztikusan állítja elő a belső komponenseket.

## 4.1. Fizikai méret

### `width`

A létrehozandó relief X irányú fizikai mérete.

Mértékegysége a projekt által meghatározott hosszúságegység.

### `height`

A relief Y irányú fizikai mérete.

A két paraméter együtt határozza meg a relief alapfelületének fizikai méretét.

A Wave Function ettől függetlenül normalizált lokális koordinátatérben működik.

---

# 5. Relief magasság

### `relief_height`

A generált relief maximális fizikai magassága.

A Wave Function eredménye először normalizált Height Fielddé alakul:

[
H(x,y)\in[0,1]
]

A geometriai réteg ezt a tartományt alakítja át fizikai Z-magassággá.

A `relief_height` ezért nem a matematikai hullám amplitúdója.

---

# 6. Hullámhossz

### `wavelength`

A generált hullámrendszer domináns hullámhosszát határozza meg.

A hullámhossz a geometria fizikai méretéhez képest értelmezendő.

Nagyobb hullámhossz:

* nagyobb léptékű;
* lassabban változó;
* lágyabb hullámstruktúrát

eredményez.

Kisebb hullámhossz:

* sűrűbb;
* részletesebb;
* gyorsabban változó

felületet eredményez.

A belső hullámkomponensek hullámhosszai a domináns `wavelength` értékből determinisztikus szabály alapján származnak.

---

# 7. Amplitúdó

### `amplitude`

Az alap hullámrendszer matematikai amplitúdóját határozza meg.

Az amplitúdó a hullámkomponensek egymáshoz viszonyított súlyának alapját adja.

A többkomponensű rendszerben az egyes komponensek amplitúdói eltérhetnek.

Fontos, hogy az amplitúdó nem azonos a végleges fizikai reliefmagassággal.

A végső fizikai magasságot a `relief_height` határozza meg.

Az amplitúdó elsősorban a matematikai komponensek egymáshoz viszonyított hatását befolyásolja.

---

# 8. Domináns irány

### `direction`

A hullámrendszer domináns iránya fokban megadva.

Tartománya:

```text
0° – 360°
```

A `direction` határozza meg a hullámrendszer fő orientációját.

A tényleges komponensirányok ettől a `direction_spread` és az `irregularity` alapján eltérhetnek.

---

# 9. Direction Spread

### `direction_spread`

A komponensek irányának domináns irány körüli eltérését szabályozza.

A domináns irány:

[
\theta
]

Egy komponens iránya:

[
\theta_i=\theta+\Delta\theta_i
]

ahol:

[
\Delta\theta_i\in[-S,+S]
]

és (S) a `direction_spread`.

A komponensirányok meghatározása determinisztikus.

### Értelmezés

```text
0°
```

→ szabályos, párhuzamos hullámrendszer.

Nagyobb érték:

→ változatosabb hullámirányok.

A paraméter célja nem a véletlenszerű zaj létrehozása, hanem a domináns irány megtartása mellett természetesebb felület kialakítása.

---

# 10. Irregularity

### `irregularity`

A hullámkomponensek szabályozott eltérését határozza meg.

Az eltérés érintheti:

* amplitúdót;
* hullámhosszt;
* fázist;
* komponensirányt.

A `direction_spread` és az `irregularity` külön fogalom.

A `direction_spread` elsősorban az irány változatosságát szabályozza.

Az `irregularity` a hullámrendszer egyéb tulajdonságainak változatosságát szabályozza.

Az irregularitás determinisztikus.

Azonos paraméterekből azonos eredménynek kell származnia.

---

# 11. Complexity

### `complexity`

A generált hullámrendszer összetettségét szabályozza.

A paraméter nem közvetlenül a komponensek számát jelenti.

A generátor belső szabályai határozzák meg, hogy az adott komplexitási értékhez:

* hány komponens;
* milyen hullámhosszok;
* milyen amplitúdóarányok;
* milyen fázisok

tartoznak.

Alacsony komplexitás:

→ egyszerűbb, domináns hullámstruktúra.

Magasabb komplexitás:

→ több léptékű, összetettebb felület.

A komplexitás célja a természetes részletesség szabályozása anélkül, hogy a felhasználónak a belső komponenseket kellene kezelnie.

---

# 12. Belső komponensparaméterek

A generátor belső modellje továbbra is komponensenként tartalmazza:

```text
Aᵢ
λᵢ
θᵢ
φᵢ
```

Ezeket az első generátor esetében nem szükséges közvetlenül felhasználói paraméterként megjeleníteni.

A magas szintű generátorparaméterekből determinisztikus szabályokkal kerülnek előállításra.

Ez biztosítja, hogy az első generátor egyszerűen kezelhető maradjon, miközben a belső matematikai modell többkomponensű.

---

# 13. Normalizálás

A hullámkomponensek összeadásából származó nyers eredmény:

[
F(x,y)
]

nem közvetlen fizikai magasság.

A generátor ezt normalizálja:

[
H(x,y)\in[0,1]
]

Az első modellben a normalizálás a ténylegesen előállított minimum- és maximumértékek alapján történik.

Így:

[
H_{min}=0
]

és

[
H_{max}=1
]

A fizikai skálázás a relief geometriai rétegében történik.

---

# 14. Fizikai méret és matematikai koordináták

A Wave Function normalizált koordinátákon működik:

[
x,y\in[0,1]
]

A `width` és `height` ezekhez rendeli hozzá a fizikai méretet.

Ez lehetővé teszi, hogy ugyanaz a matematikai hullámmodell eltérő fizikai méretű reliefeken legyen alkalmazható.

A geometriai réteg feladata a normalizált felület fizikai koordinátákra történő leképezése.

---

# 15. Determinizmus

A generátor determinisztikus működésű.

Azonos:

* `width`;
* `height`;
* `wavelength`;
* `amplitude`;
* `direction`;
* `direction_spread`;
* `irregularity`;
* `complexity`;
* `relief_height`

paraméterek mellett azonos Height Fieldnek kell létrejönnie.

Ez szükséges:

* reprodukálhatósághoz;
* tesztelhetőséghez;
* hibakereséshez;
* paraméterezett újrageneráláshoz;
* projektállapot mentéséhez.

---

# 16. Sampling / Resolution

Az első generátor matematikai modellje nem határozza meg a végleges mesh felbontását.

A Height Field előállításához szükséges mintavételezési sűrűség a geometriai/mesh réteg felelősségi körébe tartozik.

Ezért az első generátor publikus paraméterei között a `resolution` vagy `sampling density` jelenleg nem kerül véglegesítésre.

A kérdés a Relief Geometry Layer és a Mesh Generation tervezésekor kerül eldöntésre.

---

# 17. Első generátor támogatott paraméterei

Az első generátor domainmodelljének paraméterei:

```text
width
height

wavelength
amplitude
direction
direction_spread
irregularity
complexity

relief_height
```

A paraméterek szerepe:

```text
width
height
    ↓
fizikai alapméret

wavelength
amplitude
direction
direction_spread
irregularity
complexity
    ↓
matematikai hullámkarakter

relief_height
    ↓
fizikai Z-méret
```

---

# 18. Nem része az első generátornak

Az első implementáció nem támogatja:

* radiális hullámforrásokat;
* több explicit, felhasználó által elhelyezett hullámforrást;
* kép alapú generálást;
* heightmap alapú generálást;
* vektor alapú generálást;
* zajalapú önálló generátort;
* egyedi komponensszintű felhasználói szerkesztést.

Ezek a későbbi bővítések során kerülhetnek a rendszerbe.

---

# 19. Bővíthetőség

A generátor paramétermodelljének úgy kell illeszkednie a Wave Function modellhez, hogy később új Wave Source típusok és új generátorok bevezethetők legyenek.

Az első generátor egyszerűsége nem jelentheti azt, hogy a belső modell egyetlen speciális hullámképlethez kötődik.

A hosszú távú cél egy általánosabb parametrikus felületgeneráló rendszer.

Az első generátor ennek első, korlátozott megvalósítása.

---

# 20. Következő tervezési lépés

A jelen dokumentum után a következő domain-tervezési feladat a **Relief Geometry Layer** meghatározása.

Ennek feladata lesz meghatározni, hogyan alakul át a generátor által előállított:

[
H(x,y)\in[0,1]
]

Height Field fizikai, zárt relief geometriává.

A geometriai rétegnek különösen az alábbi kérdéseket kell kezelnie:

* fizikai X/Y méretezés;
* fizikai Z-méretezés;
* alap/fenék;
* oldalfalak;
* felső relieffelület;
* bemélyedések;
* minimum Z;
* maximum Z;
* zárt térfogat;
* watertight geometria;
* geometriai érvényesség.
