# PLUGIN_ARCHITECTURE.md

**Státusz:** Tervezet
**Cél:** A SliceDesigner opcionális MeshSource pluginjainak architektúrája
**Első konkrét alkalmazás:** Parametric Relief Generator

---

# 1. Cél

A SliceDesigner olyan opcionális bővítési lehetőségének meghatározása, amelyen keresztül külső komponensek új `MeshSource` megvalósításokat biztosíthatnak.

A plugin-architektúra elsődleges célja:

> Egy opcionális plugin telepítése új modellforrást adhat a SliceDesignerhez anélkül, hogy a SliceDesigner core működéséhez szükség lenne a pluginra.

A jelen dokumentum kizárólag a **MeshSource pluginokra** vonatkozik.

Nem definiál általános SliceDesigner plugin-frameworköt.

---

# 2. Alapmodell

A plugin a már elfogadott `MeshSource` contract konkrét külső megvalósítása.

A rendszer alapvető adatfolyamata:

```text
                    SliceDesigner Core
                           │
                           │ MeshSource contract
                           │
             ┌─────────────┴─────────────┐
             │                           │
       beépített source             opcionális plugin
             │                           │
        STL Import              Relief Generator
             │                           │
             └─────────────┬─────────────┘
                           ▼
                          Mesh
                           │
                           ▼
                    meglévő pipeline
```

A downstream pipeline számára nincs különbség a beépített és plugin által létrehozott Mesh között.

---

# 3. Mi számít pluginnek?

Plugin az a külön telepíthető Python package, amely:

1. a SliceDesigner által támogatott `MeshSource` contractot implementálja;
2. saját modellforrást biztosít;
3. a core által meghatározott contracton keresztül kapcsolódik a SliceDesignerhez;
4. a létrehozott Mesh-t a core számára átadható formában biztosítja.

A plugin saját belső algoritmusai és domainlogikája nem része a SliceDesigner core-nak.

---

# 4. Mi NEM plugin?

A következőket nem tekintjük pluginnek:

* STL fájl;
* konfigurációs fájl;
* projektfájl;
* Mesh;
* egyetlen algoritmus vagy Python modul, amely nem önálló telepíthető komponens;
* a SliceDesigner core részeként szállított MeshSource implementáció.

A plugin fogalma a **külön telepíthető komponensre** vonatkozik.

---

# 5. Core és plugin felelősségi határa

## SliceDesigner core felelőssége

A core felelős:

* a MeshSource contract definiálásáért;
* az elérhető MeshSource-ok kezeléséért;
* a pluginok felismeréséért;
* a kompatibilitás ellenőrzéséért;
* a használható MeshSource-ok felhasználói felületen történő megjelenítéséért;
* a MeshSource meghívásáért;
* a kapott Mesh további feldolgozásáért.

## Plugin felelőssége

A plugin felelős:

* saját MeshSource implementációjáért;
* saját bemeneti paramétereinek kezeléséért;
* saját modellgenerálási logikájáért;
* saját bemeneti adatai validálásáért;
* érvényes Mesh előállításáért;
* saját hibáinak megfelelő jelzéséért.

A plugin nem felelős a Slice Engine, Nesting, Export vagy más downstream folyamatokért.

---

# 6. Függőségi irány

A függőségi irány:

```text
SliceDesigner Core
        ▲
        │
    contract
        │
        │
     Plugin
```

A plugin a core által meghatározott szerződéshez igazodik.

A core nem függhet egy konkrét plugin implementációjától.

Különösen:

```text
Core ──X──> Relief Generator
```

nem megengedett.

Helyette:

```text
Core ──> MeshSource contract <── Relief Generator
```

---

# 7. Plugin telepíthetősége

A plugin külön Python package-ként telepíthető.

A SliceDesigner core telepítésének nem lehet előfeltétele egyetlen opcionális MeshSource plugin jelenléte sem.

Ezért:

### Plugin telepítve

```text
SliceDesigner
 ├── STL Import
 └── Relief Generator
```

### Plugin nincs telepítve

```text
SliceDesigner
 └── STL Import
```

Mindkét állapot érvényes és támogatott.

---

# 8. Plugin discovery

A SliceDesignernek képesnek kell lennie a telepített MeshSource pluginok felismerésére.

A discovery mechanizmusnak az alábbi tulajdonságokkal kell rendelkeznie:

* ne igényeljen manuális core-kódmódosítást minden új pluginhoz;
* ne igényelje a pluginok hardcode-olt felsorolását;
* a plugin hiánya ne okozzon hibát;
* inkompatibilis plugin ne kerülhessen használható MeshSource-ként a rendszerbe.

A konkrét Python packaging/discovery mechanizmus jelen dokumentum további technikai tervezési szakaszában kerül meghatározásra.

A discovery mechanizmus nem változtathatja meg a `MeshSource` contractot.

---

# 9. Plugin registration

A discovery eredménye egy vagy több használható `MeshSource`.

A core számára egy plugin lényegi eredménye:

```text
Plugin
   ↓
MeshSource registration
   ↓
elérhető MeshSource
```

A regisztráció minimálisan azonosíthatóvá és kiválaszthatóvá kell tegye a MeshSource-t.

A registration nem lehet source-specifikus üzleti logika.

---

# 10. Felhasználói felület

A plugin által biztosított MeshSource-nak meg kell jelennie a SliceDesigner modellforrásai között.

A felhasználó szempontjából az eredmény:

```text
Model Source

○ STL file
○ Relief Generator
```

A konkrét GUI-mechanizmus külön implementációs döntés.

A pluginnek azonban képesnek kell lennie a saját bemeneti paramétereinek felhasználói felületen történő megadására.

---

# 11. Source-specifikus paraméterek

A plugin saját paramétermodelllel rendelkezik.

Például a Relief Generator később rendelkezhet:

```text
width
height
resolution
amplitude
frequency
seed
...
```

Ezek **nem kerülnek a core `MeshSource` contractba**.

A core számára csak az általános MeshSource működés számít:

```text
plugin parameters
       ↓
plugin MeshSource
       ↓
Mesh
```

A konkrét parametrikus relief-modell külön dokumentációban kerül majd meghatározásra.

---

# 12. Plugin életciklusa

A plugin életciklusa minimálisan:

```text
telepítés
   ↓
felfedezés
   ↓
kompatibilitás ellenőrzése
   ↓
regisztráció
   ↓
felhasználás
   ↓
eltávolítás / deaktiválás
```

A pluginnek nem kell folyamatosan futó szolgáltatásként működnie.

A MeshSource használata történhet igény szerint.

A plugin saját állapotának kezelése nem kerülhet a core-ba, kivéve azt az állapotot, amely a MeshSource contract működéséhez szükséges.

---

# 13. Plugin kompatibilitás

A plugin és a SliceDesigner core közötti kompatibilitást explicit módon kezelni kell.

A kompatibilitás legalább két szintből áll:

### Core API / contract kompatibilitás

A plugin által támogatott `MeshSource` contract verziójának kompatibilisnek kell lennie a core által biztosított contracttal.

### Plugin package kompatibilitás

A plugin saját verziója külön kezelhető.

A két fogalom nem keverendő:

```text
plugin version
      ≠
MeshSource contract version
```

A konkrét verziózási mechanizmus külön ADR-ben vagy a jelen dokumentum implementáció előtti véglegesítésében kerül rögzítésre, ha a választott megoldás architekturális jelentőségű.

---

# 14. Inkompatibilis plugin

Ha egy telepített plugin nem kompatibilis a jelenlegi SliceDesignerrel:

* a core nem használhatja MeshSource-ként;
* a plugin hibája nem akadályozhatja a core elindulását;
* a felhasználó számára egyértelműen jelezhető az inkompatibilitás;
* a többi használható MeshSource továbbra is működőképes marad.

A plugin hibája tehát izolált hiba.

---

# 15. Plugin nélküli működés

Ez az architektúra egyik kötelező invariánsa.

A SliceDesignernek plugin nélkül is teljes értékűen kell működnie a core által biztosított MeshSource-okkal.

Nem lehet:

```text
Plugin hiányzik
      ↓
SliceDesigner nem indul
```

és nem lehet:

```text
Plugin hiányzik
      ↓
STL Import sem működik
```

A helyes működés:

```text
Plugin hiányzik
      ↓
adott MeshSource nem érhető el
      ↓
core többi funkciója változatlanul működik
```

---

# 16. Plugin izoláció

A plugin nem módosíthatja közvetlenül:

* a Slice Engine működését;
* a Gap Engine működését;
* a Dowel Engine működését;
* a Backplate Engine működését;
* a Numbering Engine működését;
* a Nesting Engine működését;
* az Export működését.

A plugin által létrehozott Mesh után a meglévő pipeline változatlanul működik.

Ez biztosítja, hogy a plugin hozzáadása ne hozzon létre második slicing-rendszert.

---

# 17. Hibakezelés

A plugin hibája a plugin határán kezelendő.

Például:

```text
érvénytelen plugin paraméter
        ↓
plugin validációs hiba
        ↓
nincs Mesh
```

nem pedig:

```text
hibás plugin
   ↓
hibás Mesh
   ↓
Slice Engine próbálja megoldani
```

A plugin nem adhat át tudottan érvénytelen Mesh-t a core pipeline számára.

---

# 18. Biztonsági és stabilitási határ

A plugin architektúra nem jelent sandboxot.

A külön telepített Python plugin ugyanabban a Python futtatási környezetben működik, ezért technikai értelemben a plugin megbízható helyi kódnak tekintendő.

A jelen architektúra nem vállal:

* sandboxolást;
* jogosultságkezelést;
* rosszindulatú plugin elleni védelmet;
* külön processzben történő futtatást.

Ezek jelenleg nem részei a projekt céljának.

---

# 19. Relief Generator helye

A Parametric Relief Generator az első konkrét MeshSource plugin.

A kapcsolat:

```text
Relief Generator Plugin
          │
          ▼
   Relief MeshSource
          │
          ▼
         Mesh
          │
          ▼
    SliceDesigner
          │
          ▼
   meglévő pipeline
```

A Relief Generator saját dokumentációjában kell majd meghatározni:

* a bemeneti modellt;
* a parametrikus felületet;
* a generálási algoritmust;
* a geometriai validációt;
* a generátor saját paramétereit.

Ezek nem részei a plugin-architektúrának.

---

# 20. Amit a plugin nem tud

A plugin-architektúra szándékosan nem biztosít általános hozzáférést a SliceDesigner teljes belső rendszeréhez.

A plugin nem kap önálló jogot:

* a domainmodell módosítására;
* a slicing szabályok módosítására;
* a core konfiguráció átírására;
* a pipeline sorrendjének módosítására;
* más MeshSource-ok módosítására.

A plugin bővítési pontja:

> `MeshSource`

és nem a teljes SliceDesigner.

---

# 21. Visszafelé kompatibilitás

A döntés a meglévő SliceDesigner működését nem változtatja meg plugin nélkül.

Megmarad:

* STL import;
* Mesh;
* Slice;
* Slice Set;
* teljes downstream pipeline;
* meglévő projektfájlok kezelése;
* meglévő GUI-folyamat.

Új képességként jelenik meg:

* külső MeshSource-ok telepítése;
* opcionális modellgenerátorok használata.

A plugin architektúra nem igényel külön slicing pipeline-t.

---

# 22. Hatókörön kívül

A jelen dokumentum nem határozza meg:

* a Relief Generator algoritmusát;
* a HeightField domain modellt;
* a relief paramétereket;
* a konkrét Python entry-point mechanizmust;
* a plugin package konkrét könyvtárstruktúráját;
* a plugin GUI konkrét widgetjeit;
* a plugin marketplace-et;
* automatikus plugin letöltést;
* plugin sandboxot;
* más típusú pluginokat;
* export pluginokat;
* post-processing pluginokat.

Ezek közül jelenleg egyik sem szükséges a cél megvalósításához.

---

# 23. Impact Analysis

## Érintett dokumentumok

### Közvetlenül

* `PLUGIN_ARCHITECTURE.md`

### Már elfogadott és hivatkozott

* `MESH_SOURCE.md`
* `ADR_MESH_SOURCE`
* `DOMAIN_MODEL.md`
* `ARCHITECTURE.md`

### Később

* Relief Generator domain/specifikáció
* plugin implementációs dokumentáció, ha szükséges

## Érintett könyvtárak

A dokumentáció szintjén:

```text
docs/
```

Az implementáció konkrét könyvtárstruktúrája még nem dönthető el ebből a dokumentumból.

## Szükséges dokumentummódosítások

A plugin architektúra elfogadása után szükség lehet:

* `ARCHITECTURE.md` plugin-határra vonatkozó kiegészítésére;
* `PROJECT_STRUCTURE.md` kiegészítésére, ha a plugin package struktúrája külön projektkönyvtárat igényel;
* később a Relief Generator saját dokumentációjára.

Ezek tényleges szükségességét a konkrét technikai discovery/packaging döntés után kell megállapítani.

## Szükséges ADR

**Igen.**

A plugin mint opcionális külső MeshSource architekturális bővítési mechanizmusként való bevezetése új architekturális döntés.

A `PLUGIN_ARCHITECTURE.md` jóváhagyása után külön ADR-ben kell rögzíteni:

* miért plugin;
* miért opcionális;
* miért kizárólag MeshSource bővítési pont;
* miért nincs általános plugin-framework;
* milyen core/plugin határ került elfogadásra.

## Visszafelé kompatibilitás

A plugin hiánya nem változtatja meg a meglévő SliceDesigner működését.

A meglévő STL-alapú workflow továbbra is érvényes.

---

# 24. Elfogadási kritériumok

A plugin-architektúra akkor tekinthető megfelelőnek, ha:

1. a plugin kizárólag `MeshSource` bővítési pontként jelenik meg;
2. a SliceDesigner plugin nélkül működőképes;
3. a core nem függ egyetlen konkrét plugintól;
4. a plugin külön telepíthető;
5. a plugin saját paramétermodellt használhat;
6. a plugin közvetlenül `Mesh`-t ad át;
7. a downstream pipeline változatlan marad;
8. a plugin nem módosíthatja a slicing pipeline-t;
9. a plugin inkompatibilitása nem akadályozza a core működését;
10. a discovery és registration nem igényel minden új pluginhoz core-kódmódosítást;
11. nincs bevezetve általános, jelenleg szükségtelen plugin-framework;
12. a dokumentum nem dönt még a Relief Generator konkrét algoritmusáról;
13. a dokumentum összhangban van a `MESH_SOURCE.md` és `ADR_MESH_SOURCE` döntéseivel.

---

# 25. Célállapot

A SliceDesigner architekturális modellje:

```text
                     SliceDesigner
                           │
                    ┌──────▼──────┐
                    │    Core     │
                    └──────┬──────┘
                           │
                    MeshSource API
                           │
             ┌─────────────┴─────────────┐
             │                           │
      Core MeshSource             Optional Plugin
             │                           │
        STL Import                Relief Generator
             │                           │
             └─────────────┬─────────────┘
                           ▼
                          Mesh
                           │
                           ▼
                    Slice / Pipeline
```

A legfontosabb architekturális szabály:

> **A plugin a modell létrehozását bővíti, nem a modell feldolgozását.**

---

# 26. Következő dokumentációs lépések

A jelen dokumentum jóváhagyása után:

1. `PLUGIN_ARCHITECTURE` ADR elkészítése;
2. a plugin discovery és packaging konkrét megoldásának dokumentálása, ha ehhez külön döntés szükséges;
3. a Relief Generator saját domainmodelljének megtervezése;
4. HeightField / generálási contract dokumentálása;
5. csak ezután a plugin implementáció tervezése.

A Relief Generator konkrét algoritmusa továbbra sem része a plugin-architektúra döntésének.

---

# 27. Státusz

**Tervezet — projektgazdai jóváhagyásra vár.**

A tényleges plugin-implementáció csak a jelen dokumentum és a hozzá tartozó ADR elfogadása után kezdhető meg.
