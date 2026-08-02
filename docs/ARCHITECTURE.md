# Architektúra

Státusz: Elfogadva
Tulajdonos:
Létrehozva: 2026-07-30
Utolsó módosítás: 2026-08-01
Kapcsolódó dokumentumok: [PROJECT_CONSTITUTION.md](PROJECT_CONSTITUTION.md), [PROJECT_VISION.md](PROJECT_VISION.md), [ENGINEERING_PRINCIPLES.md](ENGINEERING_PRINCIPLES.md), [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md), [adr/](adr/)

## Cél

Ez a dokumentum írja le a Slice Designer tervezett rendszerarchitektúráját.

## 1. Áttekintés

A Slice Designer architektúrája három rétegre épül: **Domain réteg** (engine-ek), **Koordinációs réteg** (Project) és **Prezentációs réteg** (GUI). Minden fő feladatnak (Mesh betöltés, szeletelés, illesztés, pozicionálás, jelölés, elrendezés, export) külön, egyetlen felelősségű engine felel meg, az Engineering Principles moduláris felépítés elvének megfelelően.

A rétegek szigorúan egyirányban függenek: GUI → Project → Engine-ek. Fordított irányú függés nincs: egyetlen engine sem ismeri vagy hívja a Project-et vagy a GUI-t. Az engine-ek egymástól is függetlenek — nem hívják egymást közvetlenül, csak a Project által köztük továbbított adatokon keresztül érintkeznek.

## 2. Fő komponensek

### Mesh Import

**Réteg:** Domain

**Felelősség:** STL formátumú modell betöltése, validálása, Mesh domain objektum előállítása.

**Domain Model kapcsolat:** Mesh

---

### Slice Engine

**Réteg:** Domain

**Felelősség:** A Mesh keresztmetszeteinek (szeleteinek) előállítása a szeletelési tengely mentén — a Gap paraméter figyelembevételével, úgy, hogy a szeletek és a köztük tervezett hézagok együttesen a Mesh szeletelési tengely menti méretét adják ki —, Slice Set létrehozása.

**Domain Model kapcsolat:** Mesh, Slice, Slice Set, Gap

---

### Dowel Engine

**Réteg:** Domain

**Felelősség:** Dowel és Dowel Hole pozíciójának és geometriájának számítása a szeletek egymáshoz viszonyított illesztéséhez, a Slice Engine által pozicionált Slice Set alapján, a modell külső palástján belül maradva.

**Domain Model kapcsolat:** Dowel, Dowel Hole, Slice

---

### Gap Engine

**Réteg:** Domain

**Felelősség:** A Gap fizikai megvalósítását biztosító Spacer specifikáció előállítása, a Slice Engine által már a Gap figyelembevételével pozicionált Slice Set alapján, a Dowel Engine által már meghatározott Dowel-pozíciók figyelembevételével és előnyben részesítésével.

**Domain Model kapcsolat:** Gap, Spacer, Slice Set, Dowel

---

### Backplate Engine

**Réteg:** Domain

**Felelősség:** A Backplate geometriájának előállítása, és a szeletek Backplate-hez viszonyított pozicionálása.

**Domain Model kapcsolat:** Backplate, Slice

---

### Numbering Engine

**Réteg:** Domain

**Felelősség:** Minden Slice egyedi azonosítóval ellátása — bevésve/kivágva a szelet geometriájába —, valamint a hozzá tartozó Backplate pozíción a szelet helyének megjelölése, biztosítva a hibamentes összeszerelést.

**Domain Model kapcsolat:** Slice, Backplate, Numbering

---

### Nesting Engine

**Réteg:** Domain

**Felelősség:** Az elkészült alkatrészek (Slice, Backplate) optimális elrendezése a rendelkezésre álló Material-okon.

**Domain Model kapcsolat:** Material, Nest, Slice

---

### DXF Export Engine

**Réteg:** Domain

**Felelősség:** A Nest alapján gyártásra kész Export (DXF) kimenet előállítása.

**Domain Model kapcsolat:** Nest, Export

---

### Project

**Réteg:** Koordinációs

**Felelősség:** Az engine-ek végrehajtási sorrendjének (pipeline) összefogása, a Project állapotának tartása, mentés és betöltés kezelése, valamint a paraméterek továbbítása az egyes engine-ek felé. A Project maga nem tartalmaz geometriai vagy üzleti logikát — kizárólag koordinál.

**Domain Model kapcsolat:** Project

---

### GUI

**Réteg:** Prezentációs

**Felelősség:** Megjelenítés és felhasználói interakció fogadása, beleértve az Assembly és az egyes Slice-ok interaktív, forgatható/zoomolható 3D vizualizációját. Nem tartalmaz üzleti vagy geometriai logikát (Engineering Principles, GUI felelőssége) — a vizualizációhoz szükséges geometriai adatokat (pl. Slice pozíció, vastagság, geometria típusa; Assembly szerkezete) a Domain Modelben rögzített attribútumok alapján a Project biztosítja, a GUI nem számol geometriát, kizárólag megjelenít. Kizárólag a Project komponensen keresztül kommunikál, engine-t közvetlenül nem hív.

**Domain Model kapcsolat:** —

## 3. Adatfolyam / munkafolyamat a rendszeren belül

A feldolgozási folyamat lineáris pipeline-t követ, amelyet a Project koordinál:

```
Mesh Import → Slice Engine → Dowel Engine → Gap Engine → Backplate Engine
     → Numbering Engine → Nesting Engine → DXF Export Engine
```

* A **Mesh Import** állítja elő a Mesh-t, amely a **Slice Engine** bemenete.
* A **Slice Engine** a Mesh-ből, a Gap paraméter figyelembevételével, már helyesen pozicionált Slice Set-et állít elő.
* A **Dowel Engine** a pozicionált Slice Set-hez számítja az illesztőelemeket, a modell külső palástján belül maradva.
* A **Gap Engine** a Dowel Engine által már meghatározott Dowel-pozíciók figyelembevételével és előnyben részesítésével állítja elő a Spacer elemeket.
* A **Backplate Engine** ezután állítja elő a Backplate geometriát és a szeletek pozícióját azon.
* A **Numbering Engine** a kész Slice Set-et és a Backplate-et egészíti ki azonosítókkal — ezért csak a Backplate Engine után futhat.
* A **Nesting Engine** az összes elkészült alkatrészt (megjelölt Slice-ok, Backplate) elrendezi a Material-okon.
* A **DXF Export Engine** a végleges Nest alapján állítja elő az Export-ot.

Minden nyíl adatátadást jelent, nem közvetlen függőséget — az engine-ek a Project-en keresztül, jól definiált be- és kimeneti adatszerkezeteken (a Domain Model fogalmain) keresztül kommunikálnak.

## 4. Komponensek közötti felelősségmegosztás

* A GUI kizárólag a Project-tel kommunikál, sosem hívja közvetlenül az engine-eket.
* A Project ismeri a pipeline végrehajtási sorrendjét és orchestrálja az engine-eket, de maga nem végez geometriai számítást vagy üzleti döntést.
* A Project a `use_spacers`, `use_dowels`, `use_backplate` kapcsolók alapján dönti el, lefuttatja-e a Gap Engine-t, a Dowel Engine-t, illetve a Backplate Engine-t; kikapcsolt kapcsoló esetén az adott engine nem fut le. A pipeline indítása előtt a Project ellenőrzi, hogy legalább egy kapcsoló be van-e kapcsolva — ha egyik sem, hiba. Ez konfiguráció-teljességi ellenőrzés, nem geometriai vagy üzleti döntés.
* Az engine-ek egymástól függetlenek: nem hívják egymást közvetlenül, kizárólag a Project által továbbított, jól definiált adatszerkezeteken keresztül érintkeznek.
* Minden engine a GUI-tól függetlenül, önállóan futtatható és tesztelhető, és determinisztikusan működik (Engineering Principles).
* Hibakezelés fail-fast elven történik: egy engine érvénytelen vagy hiányos bemenet esetén explicit hibát jelez a Project felé, amely azt továbbítja a GUI-nak megjelenítésre — csendes alapértelmezés vagy automatikus javítás egyetlen rétegben sem történik.

## 5. Kapcsolódó architekturális döntések (hivatkozás az ADR-ekre)

Ez a dokumentum az architektúra kezdeti, alapállapotát rögzíti, ezért önmagában nem igényel Architecture Decision Record-ot. A jövőben, ha ez az architektúra jelentősen módosul (például réteg hozzáadása, engine-ek összevonása vagy szétválasztása), azt a `PROJECT_CONSTITUTION.md` 8. elve szerint ADR-ben kell rögzíteni a `docs/adr/` mappában.

Az implementációs technológia kiválasztása (Python + PySide) az [ADR-0001](adr/0001-python-pyside-tech-stack.md) dokumentumban került rögzítésre.

A GUI interaktív 3D vizualizációs technológiájának kiválasztása (PyVista + pyvistaqt) az [ADR-0002](adr/0002-pyvista-3d-visualization.md) dokumentumban került rögzítésre.

A Slice Engine és a Gap Engine közötti felelősség-felosztás pontosítása (a Gap figyelembevétele már a szeletelés során) az [ADR-0003](adr/0003-gap-aware-slicing.md) dokumentumban került rögzítésre.

Az opcionális összeépítési mechanizmusok (Spacer/Dowel/Backplate ki/bekapcsolhatósága) bevezetése az [ADR-0004](adr/0004-optional-assembly-mechanisms.md) dokumentumban került rögzítésre.

A pipeline-sorrend cseréje (Dowel Engine a Gap Engine elé kerül, a Spacer a Dowel-pozíciókhoz igazodik) az [ADR-0005](adr/0005-dowel-before-gap-ordering.md) dokumentumban került rögzítésre.
