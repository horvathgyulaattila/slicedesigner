# WAVE_FUNCTION_MODEL.md

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-11
Utolsó módosítás: 2026-08-15
Kapcsolódó dokumentumok: [PROJECT_CONSTITUTION.md](../../PROJECT_CONSTITUTION.md), [RELIEF_GENERATOR_DOMAIN.md](RELIEF_GENERATOR_DOMAIN.md), [PARAMETRIC_RELIEF_GENERATOR.md](PARAMETRIC_RELIEF_GENERATOR.md)

## 1. Cél

A Wave Function a Parametric Relief Generator matematikai felületmodelljének része.

Feladata, hogy egy kétdimenziós koordinátatér minden pontjához egy normalizált relatív magasságértéket rendeljen.

A Wave Function nem foglalkozik:

* STL-generálással;
* mesh-topológiával;
* fizikai mesh-validációval;
* fájlformátumokkal;
* GUI-megjelenítéssel.

A kimenete egy **Height Field**, amelyet a Relief Generator később fizikai geometriává alakít.

---

## 2. Alapmodell

A Wave Function több hullámkomponens összegéből áll.

Az alapfüggvény:

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

ahol:

| Jel         | Jelentés                         |
| ----------- | -------------------------------- |
| (x,y)       | normalizált felületi koordináták |
| (n)         | hullámkomponensek száma          |
| (A_i)       | az i. komponens amplitúdója      |
| (\lambda_i) | az i. komponens hullámhossza     |
| (\theta_i)  | az i. komponens iránya           |
| (\phi_i)    | az i. komponens fázisa           |

A függvény értéke kezdetben relatív magasságként értelmezendő.

---

## 3. Koordinátarendszer

A Wave Function normalizált lokális koordinátatérben működik:

[
x,y \in [0,1]
]

A fizikai méretet nem maga a Wave Function kezeli.

Például ugyanaz a Wave Function alkalmazható:

* 100 × 100 mm-es;
* 500 × 300 mm-es;
* 2000 × 1000 mm-es

felületre.

A fizikai méret a későbbi geometriai réteg feladata.

---

## 4. Directional Wave Source

Az első generátor alapvető hullámforrás-típusa a **Directional Wave Source**.

Ez síkhullám-frontokat modellez.

A hullám terjedési irányát a (\theta) paraméter határozza meg.

A síkbeli pozíciót a hullám irányára vetítjük:

[
d(x,y)=x\cos\theta+y\sin\theta
]

A hullámérték:

[
f(x,y)=
A\sin
\left(
\frac{2\pi}{\lambda}d(x,y)+\phi
\right)
]

A többkomponensű modell ennek több példányát kombinálja.

---

## 5. Domináns irány

A generátor felhasználói szinten egy **domináns irányt** definiál.

Ez nem feltétlenül jelenti azt, hogy minden komponens pontosan ugyanabba az irányba mutat.

A domináns irány:

[
\theta
]

a komponensek irányainak központi értéke.

---

## 6. Direction Spread

A `direction_spread` azt határozza meg, hogy az egyes hullámkomponensek iránya mennyire térhet el a domináns iránytól.

Egy komponens iránya:

[
\theta_i=\theta+\Delta\theta_i
]

ahol:

[
\Delta\theta_i \in [-S,+S]
]

és (S) a `direction_spread`.

A komponensek eltérése **determinista módon** kerül meghatározásra.

A rendszer nem használhat olyan véletlenszerűséget, amely miatt ugyanazon paraméterek mellett minden generálás eltérő eredményt adna.

### Példa

Domináns irány:

[
\theta=30^\circ
]

Direction spread:

[
S=10^\circ
]

A komponensek iránya a 20–40° közötti tartományból származhat.

A `direction_spread = 0°` szabályos, párhuzamos hullámrendszert eredményez.

Nagyobb érték szabadabb, természetesebb irányeloszlást tesz lehetővé.

---

## 7. Hullámkomponensek

A Wave Function több komponensből épülhet fel.

Az első generátorban a komponensek számát és konkrét paramétereit nem szükséges a felhasználónak egyenként szerkesztenie.

A generátor egy magasabb szintű paraméterkészletből determinisztikusan állítja elő őket.

Egy komponens alapvető paraméterei:

* amplitúdó;
* hullámhossz;
* irány;
* fázis.

---

## 8. Több léptékű komponensek

A természetesebb felület érdekében a komponensek nem feltétlenül azonos léptékűek.

A rendszer több léptékű hullámstruktúrát használhat.

Például:

```text
Domináns komponens
    nagy amplitúdó
    nagy hullámhossz

Másodlagos komponens
    kisebb amplitúdó
    rövidebb hullámhossz

Finom komponens
    kis amplitúdó
    rövid hullámhossz
```

A cél nem a matematikai zaj növelése, hanem a domináns forma finom, kontrollált összetettségének létrehozása.

---

## 9. Irregularity

A `direction_spread` kizárólag a komponensek irányának változatosságát szabályozza.

Ettől elkülönül az `irregularity` paraméter.

Az `irregularity` a komponensek egyéb paramétereinek kontrollált eltérését teszi lehetővé, különösen:

* amplitúdó;
* hullámhossz;
* fázis.

Az eltérés továbbra is determinisztikus.

Az `irregularity` célja, hogy az azonos paraméterekből létrejövő hullámrendszer ne legyen teljesen szabályos, miközben megőrzi a domináns geometriai karakterét.

---

## 10. Komponensek kombinálása

Az egyes hullámkomponensek eredménye egyszerűen összeadódik:

[
F(x,y)=\sum_i f_i(x,y)
]

Az első modellben nincs szükség további kombinációs operátorokra.

Ez egyszerű, kiszámítható és később bővíthető alapot biztosít.

---

## 11. Fázis

Minden hullámkomponens saját fázissal rendelkezhet:

[
\phi_i
]

A fázis szabályozott eltérése segíti a komponensek egymáshoz viszonyított helyzetének változtatását.

Az első generátorban a fázisok determinisztikus szabály szerint kerülnek előállításra.

---

## 12. Normalizálás

A komponensek összeadásából származó nyers függvényérték:

[
F(x,y)
]

önmagában nem tekinthető közvetlen fizikai magasságnak.

A generátor ezt normalizált Height Fielddé alakítja:

[
H(x,y)\in[0,1]
]

Az első változatban a normalizálás a generált felület tényleges minimum- és maximumértékei alapján történik.

Ennek eredményeként:

[
H_{\min}=0
]

és

[
H_{\max}=1
]

A fizikai maximális reliefmagasságot a következő geometriai réteg alkalmazza.

---

## 13. A Wave Function és a fizikai magasság szétválasztása

A Wave Function nem határozza meg közvetlenül, hogy például 1.0 érték hány milliméter.

A kapcsolat:

```text
Wave Function
      ↓
H(x,y) ∈ [0,1]
      ↓
Relief height
      ↓
fizikai Z-koordináta
```

A fizikai magasságot a Relief Generator geometriai modellje határozza meg.

Ez lehetővé teszi, hogy ugyanaz a matematikai felület különböző fizikai mélységgel vagy magassággal legyen előállítható.

---

## 14. Első generátor hatóköre

Az első implementáció kizárólag a Directional Wave Source-ra épül.

Támogatott:

* több hullámkomponens;
* amplitúdó;
* hullámhossz;
* domináns irány;
* direction spread;
* fázis;
* irregularity;
* determinisztikus komponens-előállítás;
* normalizált Height Field előállítása.

Nem része az első implementációnak:

* radiális hullámforrás;
* több explicit felhasználói hullámforrás;
* noise-alapú felületgenerálás;
* heightmap-alapú generálás;
* képalapú generálás;
* vektor-alapú generálás.

Ezek későbbi bővítési lehetőségek.

---

## 15. Jövőbeli Wave Source típusok

A modellnek lehetővé kell tennie további hullámforrások bevezetését.

Például:

```text
Directional
Radial
Point
Line
```

A későbbi forrástípusok eltérő matematikai távolság- vagy fázisfüggvényt használhatnak.

### Radial példa

Egy radiális forrás esetén a forrás pozíciója:

[
(x_0,y_0)
]

és az adott ponttól való távolság:

[
r(x,y)=
\sqrt{(x-x_0)^2+(y-y_0)^2}
]

A hullám:

[
f(x,y)=
A\sin
\left(
\frac{2\pi}{\lambda}r+\phi
\right)
]

Ez koncentrikus hullámfrontokat eredményez.

A Radial Wave Source nem része az első implementációnak, de a Wave Function modelljének későbbi bővíthetőségét ez az eset is figyelembe veszi.

---

## 16. Több hullámforrás

A hosszú távú modellnek lehetővé kell tennie több Wave Source kombinálását.

Például:

```text
Directional Source A
        +
Radial Source B
        +
Radial Source C
        ↓
Wave Function
        ↓
Height Field
```

Az első generátor azonban ettől még egyetlen logikai Directional Wave Generator egyszerűbb változata lehet.

A több explicit forrás kezelése későbbi bővítés.

---

## 17. Determinizmus

Azonos bemeneti paraméterek esetén a Wave Functionnek azonos eredményt kell adnia.

Ez fontos:

* reprodukálhatóság;
* tesztelhetőség;
* hibakeresés;
* paraméterezhető generálás;
* későbbi projektmentés és újragenerálás

szempontjából.

A természetes hatás nem valódi, kontrollálatlan véletlenszerűségen alapul.

---

## 18. Domain-határok

A Wave Function nem felelős a végleges mesh határainak vagy topológiájának kialakításáért.

A koordinátatérből kilógó vagy geometriailag érvénytelen eredmények kezelését a fölötte elhelyezkedő generátor- és geometriai rétegek végzik.

A Wave Function feladata kizárólag a definiált `(x,y)` tartományon értelmezett magasságfüggvény előállítása.

---

## 19. Architektúrális szerep

A modell logikai felépítése:

```text
Generator Parameters
        ↓
Wave Source / Wave Components
        ↓
Wave Function
        ↓
Normalized Height Field
        ↓
Relief Geometry
        ↓
Mesh
```

A Wave Function és a Mesh között nincs közvetlen kapcsolat.

A Wave Function nem ismeri a SliceDesigner mesh-rendszerét.

---

## 20. Bővíthetőségi alapelv

Az első implementáció célja nem egy teljes procedurális felületgeneráló motor megvalósítása.

Az első implementáció célja egy egyszerű, jól definiált matematikai alap létrehozása, amely később további generátortípusokkal és Wave Source típusokkal bővíthető.

A későbbi bővítéseknek lehetőség szerint nem szabad az első generátor alapmodelljét megkerülniük vagy annak működését újradefiniálniuk.

A rendszer hosszú távú célja egy általánosabb felületgeneráló motor, amelyben a Wave Function csak az első megvalósított matematikai felületmodell.

---

## 21. Első implementáció minimális modellje

Az első implementáció minimális logikai modellje:

```text
Directional Wave Generator
        │
        ├── dominant direction
        ├── direction spread
        ├── amplitude
        ├── wavelength
        ├── irregularity
        └── component count / complexity
                │
                ↓
        deterministic components
                │
                ↓
        summed Wave Function
                │
                ↓
        normalized Height Field
```

Ez a modell elegendő az első célként meghatározott természetesebb hullám- és dűneszerű reliefek előállításához, miközben nem zárja ki a későbbi radiális, képi, heightmap- vagy vektoralapú generátorok bevezetését.
