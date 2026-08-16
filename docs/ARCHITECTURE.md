# Architektúra

Státusz: Elfogadva
Tulajdonos:
Létrehozva: 2026-07-30
Utolsó módosítás: 2026-08-15
Kapcsolódó dokumentumok: [PROJECT_CONSTITUTION.md](PROJECT_CONSTITUTION.md), [PROJECT_VISION.md](PROJECT_VISION.md), [ENGINEERING_PRINCIPLES.md](ENGINEERING_PRINCIPLES.md), [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md), [adr/](adr/)

## Cél

Ez a dokumentum írja le a Slice Designer tervezett rendszerarchitektúráját.

## 1. Áttekintés

A Slice Designer architektúrája három rétegre épül: **Domain réteg** (engine-ek), **Koordinációs réteg** (Project) és **Prezentációs réteg** (GUI). Minden fő feladatnak (Mesh betöltés, szeletelés, illesztés, távolságtartás, pozicionálás, jelölés, elrendezés, export) külön, egyetlen felelősségű engine felel meg, az Engineering Principles moduláris felépítés elvének megfelelően.

A rétegek szigorúan egyirányban függenek: GUI → Project → Engine-ek. Fordított irányú függés nincs: egyetlen engine sem ismeri vagy hívja a Project-et vagy a GUI-t. Az engine-ek egymástól is függetlenek — nem hívják egymást közvetlenül, csak a Project által köztük továbbított adatokon keresztül érintkeznek.

## 2. Fő komponensek

### MeshSource

**Réteg:** Domain

**Felelősség:** Modellforrásból feldolgozható Mesh domain objektum előállítása. A jelenlegi STL-import egy konkrét MeshSource-megvalósítás; a MeshSource contract emellett opcionális, külön telepíthető pluginok (pl. parametrikus modellgenerátorok) csatlakozását is lehetővé teszi. A SliceDesigner core nem függ opcionális MeshSource pluginoktól — hiányuk esetén is teljes értékű marad. A pontos contract-részleteket a MESH_SOURCE.md és az ADR-0014 rögzíti.

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

**Felelősség:** A Nest alapján gyártásra kész Export (DXF) kimenet előállítása. A Futtatás automatikus pipeline-jának ez már nem lépése — önálló, explicit felhasználói interakcióra fut le (ADR-0009).

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

A feldolgozási folyamat lineáris pipeline-t követ, amelyet a Project koordinál. A MeshSource-tól a Nesting Engine-ig terjedő szakasz a "Futtatás" részeként automatikusan lefut; a DXF Export Engine ezzel szemben önálló, explicit felhasználói interakcióra (a kimenet-panel "DXF Export" gombjára) fut le, kizárólag a legutóbbi sikeres Futtatás Nest-jein (ADR-0009):

```
MeshSource → Slice Engine → Dowel Engine → Gap Engine → Backplate Engine
     → Numbering Engine → Nesting Engine   ⇢   DXF Export Engine
     └──────────── automatikus (Futtatás) ────────────┘   (explicit interakció)
```

* A **MeshSource** állítja elő a Mesh-t (konkrét megvalósításként pl. az STL-import), amely a **Slice Engine** bemenete.
* A **Slice Engine** a Mesh-ből, a Gap paraméter figyelembevételével, már helyesen pozicionált Slice Set-et állít elő.
* A **Dowel Engine** a pozicionált Slice Set-hez számítja az illesztőelemeket, a modell külső palástján belül maradva.
* A **Gap Engine** a Dowel Engine által már meghatározott Dowel-pozíciók figyelembevételével és előnyben részesítésével állítja elő a Spacer elemeket; a Spacer-lista a Backplate Engine-t és a Numbering Engine-t megkerülve, közvetlenül a Nesting Engine bemenete.
* A **Backplate Engine** ezután állítja elő a Backplate geometriát és a szeletek pozícióját azon.
* A **Numbering Engine** a kész Slice Set-et és a Backplate-et egészíti ki azonosítókkal — ezért csak a Backplate Engine után futhat.
* A **Nesting Engine** az összes elkészült alkatrészt (megjelölt Slice-ok, Backplate, valamint a Gap Engine-től közvetlenül kapott Spacer-lista) elrendezi a Material-okon — ezzel a Futtatás automatikus szakasza lezárul.
* A **DXF Export Engine** a végleges Nest alapján állítja elő az Export-ot, a felhasználó külön kérésére (ADR-0009).

Minden nyíl adatátadást jelent, nem közvetlen függőséget — az engine-ek a Project-en keresztül, jól definiált be- és kimeneti adatszerkezeteken (a Domain Model fogalmain) keresztül kommunikálnak.

## 4. Komponensek közötti felelősségmegosztás

* A GUI kizárólag a Project-tel kommunikál, sosem hívja közvetlenül az engine-eket.
* A Project ismeri a pipeline végrehajtási sorrendjét és orchestrálja az engine-eket, de maga nem végez geometriai számítást vagy üzleti döntést.
* A Project a `use_spacers`, `use_dowels`, `use_backplate` kapcsolók alapján dönti el, lefuttatja-e a Gap Engine-t, a Dowel Engine-t, illetve a Backplate Engine-t; kikapcsolt kapcsoló esetén az adott engine nem fut le. A pipeline indítása előtt a Project ellenőrzi, hogy legalább egy kapcsoló be van-e kapcsolva — ha egyik sem, hiba. Ez konfiguráció-teljességi ellenőrzés, nem geometriai vagy üzleti döntés.
* Az engine-ek egymástól függetlenek: nem hívják egymást közvetlenül, kizárólag a Project által továbbított, jól definiált adatszerkezeteken keresztül érintkeznek.
* Minden engine a GUI-tól függetlenül, önállóan futtatható és tesztelhető, és determinisztikusan működik (Engineering Principles).
* Hibakezelés fail-fast elven történik: egy engine érvénytelen vagy hiányos bemenet esetén explicit hibát jelez a Project felé, amely azt továbbítja a GUI-nak megjelenítésre — csendes alapértelmezés vagy automatikus javítás egyetlen rétegben sem történik.
* Az opcionális MeshSource pluginok (pl. a Relief Generator Plugin) kizárólag a `MeshSource` bővítési ponton keresztül kapcsolódnak a SliceDesignerhez — nem kapnak jogot a Domain Model, a slicing szabályok, a core konfiguráció vagy a pipeline sorrendjének módosítására, sem más MeshSource megvalósítás befolyásolására. Egy plugin hibája vagy inkompatibilitása nem akadályozhatja a SliceDesigner indulását vagy a többi MeshSource működését (ADR-0015).

## 5. Kapcsolódó architekturális döntések (hivatkozás az ADR-ekre)

Ez a dokumentum az architektúra kezdeti, alapállapotát rögzíti, ezért önmagában nem igényel Architecture Decision Record-ot. A jövőben, ha ez az architektúra jelentősen módosul (például réteg hozzáadása, engine-ek összevonása vagy szétválasztása), azt a `PROJECT_CONSTITUTION.md` 8. elve szerint ADR-ben kell rögzíteni a `docs/adr/` mappában.

Az implementációs technológia kiválasztása (Python + PySide) az [ADR-0001](adr/0001-python-pyside-tech-stack.md) dokumentumban került rögzítésre.

A GUI interaktív 3D vizualizációs technológiájának kiválasztása (PyVista + pyvistaqt) az [ADR-0002](adr/0002-pyvista-3d-visualization.md) dokumentumban került rögzítésre.

A Slice Engine és a Gap Engine közötti felelősség-felosztás pontosítása (a Gap figyelembevétele már a szeletelés során) az [ADR-0003](adr/0003-gap-aware-slicing.md) dokumentumban került rögzítésre.

Az opcionális összeépítési mechanizmusok (Spacer/Dowel/Backplate ki/bekapcsolhatósága) bevezetése az [ADR-0004](adr/0004-optional-assembly-mechanisms.md) dokumentumban került rögzítésre.

A pipeline-sorrend cseréje (Dowel Engine a Gap Engine elé kerül, a Spacer a Dowel-pozíciókhoz igazodik) az [ADR-0005](adr/0005-dowel-before-gap-ordering.md) dokumentumban került rögzítésre.

A build backend és a Domain réteg alapkönyvtárainak (mesh-kezelés, DXF-írás) kiválasztása (uv + hatchling, trimesh, ezdxf, PySide6) az [ADR-0006](adr/0006-build-tooling-and-core-libraries.md) dokumentumban került rögzítésre.

A kontúr körüljárási irányának mint szolid/lyuk megkülönböztetésnek a konvenciója (CCW = szilárd anyag, CW = lyuk) az [ADR-0007](adr/0007-contour-winding-convention.md) dokumentumban került rögzítésre.

A Nesting Engine csomagolási algoritmusának megválasztása (befoglaló-téglalap alapú polc-csomagolás a specifikáció "valódi alak" megfogalmazása helyett) az [ADR-0008](adr/0008-nesting-bounding-box-packing.md) dokumentumban került rögzítésre — ezt a döntést az [ADR-0013](adr/0013-nesting-true-shape-packing.md) felváltotta.

A Nesting Engine csomagolási algoritmusának valódi alak (true-shape) szerinti elrendezésre váltása (Bottom-Left Fill heurisztika, valódi kontúr-ütközéssel) az [ADR-0013](adr/0013-nesting-true-shape-packing.md) dokumentumban került rögzítésre.

A DXF Export leválasztása a Futtatásról (önálló, explicit felhasználói interakció a kimenet-panel "DXF Export" gombjával) az [ADR-0009](adr/0009-decoupled-dxf-export.md) dokumentumban került rögzítésre.

A Slice Engine vetítésének gyökérokig visszavezetett tükrözési hibája, és az ezzel összefüggő, korábban duplikált tengely-/glyph-táblák egységes, megosztott forrásra hozása az [ADR-0010](adr/0010-slice-projection-mirror-and-shared-axis-tables.md) dokumentumban került rögzítésre.

A 3D-előnézet geometria-építésének háttérszálra vitele a Futtatás utáni első megjelenítésnél az [ADR-0011](adr/0011-preview-geometry-background-thread.md) dokumentumban került rögzítésre.

A kiemelés-/nézet-váltás interaktív újraépítésének háttérszálra vitele, generáció-számlálóval védve az elavult eredmények felülírása ellen, az [ADR-0012](adr/0012-interactive-preview-render-background-thread.md) dokumentumban került rögzítésre.

A modellforrások egységes MeshSource-absztrakciójának bevezetése, amely lehetővé teszi opcionális, külön telepíthető modellgenerátor-pluginok (elsőként a Relief Generator Plugin) csatlakozását, az [ADR-0014](adr/0014-meshsource-abstraction.md) dokumentumban került rögzítésre.

Az opcionális, külön telepíthető MeshSource pluginok architektúrája (a plugin kizárólagos MeshSource bővítési pontja, a core/plugin felelősségi határ és a plugin izolációja) az [ADR-0015](adr/0015-optional-meshsource-plugin-architecture.md) dokumentumban került rögzítésre.

A MeshSource pluginok discovery-mechanizmusa és a hozzá tartozó, core-oldali generikus GUI paraméter-séma (`MeshSourceDescriptor`) az [ADR-0017](adr/0017-plugin-discovery-and-parameter-schema.md) dokumentumban került rögzítésre.
