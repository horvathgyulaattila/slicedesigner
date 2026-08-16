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

---

## 22. Determinisztikus komponens-előállítási szabály (első implementáció)

A 10–11. szakasz, valamint a `PARAMETRIC_RELIEF_GENERATOR.md` 11. szakasza nyitva hagyja a `complexity`/`irregularity` → konkrét komponensszám/amplitúdó/hullámhossz/fázis leképezés pontos szabályát. Az első implementációhoz tartozó, jóváhagyott szabály a következő.

### Komponensszám

[
n = MIN\_COMPONENTS + \mathrm{round}\big(complexity \cdot (MAX\_COMPONENTS - MIN\_COMPONENTS)\big)
]

ahol `MIN_COMPONENTS = 1`, `MAX_COMPONENTS = 5`.

### Determinisztikus perturbációs segédfüggvény

Egy `random`-mentes, tisztán az `i` komponensindextől (és egy `salt` értéktől) függő, `[-1,1]` tartományba eső, jól szóródó sorozat:

[
\rho(i, salt) = 2 \cdot \mathrm{frac}\big((i+1+salt)\cdot\varphi\big) - 1
]

ahol (\varphi \approx 1.618033988749895) (aranymetszés-arány).

### Komponensenkénti paraméterek (`i = 0..n-1`)

[
A_i = amplitude \cdot PERSISTENCE^i \cdot \big(1 + irregularity \cdot A\_JITTER \cdot \rho(i,0)\big)
]

[
\lambda_i = \frac{wavelength}{LACUNARITY^i} \cdot \big(1 + irregularity \cdot \lambda\_JITTER \cdot \rho(i,1)\big)
]

[
\theta_i =
\begin{cases}
direction & n=1 \\
(direction - S) + i\cdot\dfrac{2S}{n-1} & n>1
\end{cases}
]

ahol `S = direction_spread` (fokban; a képlet a `WaveGenerator` implementációjában radiánra váltva alkalmazandó).

[
\phi_i = \big(i \cdot \Gamma + irregularity \cdot \phi\_JITTER \cdot \rho(i,2)\cdot 2\pi\big) \bmod 2\pi
]

ahol (\Gamma \approx 2.399963229728653) radián (aranyszög) — determinisztikus, jól szóródó fázis-elosztást biztosít a komponensek között.

Konstansok: `PERSISTENCE = 0.5`, `LACUNARITY = 2.0`, `A_JITTER = 0.5`, `λ_JITTER = 0.3`, `φ_JITTER = 1.0`.

A `PERSISTENCE`/`LACUNARITY` biztosítja a 8. szakaszban leírt "több léptékű komponensek" viselkedést (a domináns, `i=0` komponens a legnagyobb amplitúdójú és leghosszabb hullámhosszú). A `θ_i` képlet garantálja, hogy `direction` a komponensirányok középértéke maradjon (5. szakasz), tetszőleges `n`-re. A `JITTER` konstansok `irregularity=1.0` mellett sem tehetik `A_i`-t vagy `λ_i`-t nem-pozitívvá (a szorzótényezők alsó korlátja rendre `1 - A_JITTER = 0.5` és `1 - λ_JITTER = 0.7`, mindkettő pozitív).

---

## 23. Normalizálási mintavételezés (első implementáció)

A 12. szakasz szerinti, a felület tényleges minimum-/maximumértékein alapuló normalizálás megvalósításához az első implementáció egy belső, felhasználó számára nem elérhető, fix `65×65` rácson mintavételezi a nyers `F(x,y)` függvényt a `[0,1]×[0,1]` tartományon, és az így becsült `F_min`/`F_max` alapján normalizál. Ez a rács független a Mesh Generator későbbi, felhasználó által vezérelt mintavételi felbontásától (`IMPLEMENTATION_PLAN.md` 12. szakasza).

A rácsalapú közelítésből eredő lebegőpontos szélsőérték-eltérés ellen a normalizált érték a `[0.0, 1.0]` tartományra van szorítva (`clamp`) — ez a felhasználói bemenettől független, tisztán numerikus védelem, nem hibás bemenet elfedése.

Ha a becsült `F_max` és `F_min` megegyezik (elméletileg csak degenerált bemenet esetén fordulhatna elő, mivel `amplitude > 0` validált a `WaveParameters`-ben), a generálás explicit hibával áll le.
