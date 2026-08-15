# ADR: Opcionális MeshSource plugin architektúra

**Státusz:** Tervezet
**Dátum:** 2026-08-09
**Döntés típusa:** Architektúra
**Kapcsolódó döntések:** `ADR_MESH_SOURCE`

---

## 1. Kontextus

A SliceDesigner modellfeldolgozási architektúrájában a `MeshSource` absztrakció választja el a modell létrehozását a modell további feldolgozásától.

A SliceDesigner elsődleges működése jelenleg fájlból importált Mesh-re épül, de a projekt céljai között szerepelnek olyan modellgeneráló képességek is, amelyek nem egy meglévő modellfájlból indulnak.

Az első ilyen képesség a **Parametric Relief Generator**.

Ennek megvalósításához nem szükséges és nem kívánatos a SliceDesigner core módosítása minden új modellforrás bevezetésekor.

Ugyanakkor jelenleg nincs szükség általános plugin-frameworkre sem. A projekt jelenlegi célja kizárólag az, hogy új `MeshSource` megvalósítások opcionálisan, külön telepíthető komponensként kapcsolódhassanak a SliceDesignerhez.

---

# 2. Döntés

A SliceDesigner támogatni fogja az **opcionális, külön telepíthető MeshSource pluginokat**.

A plugin architektúra kizárólag a `MeshSource` bővítési pontra vonatkozik.

A plugin:

```text
Plugin
   ↓
MeshSource
   ↓
Mesh
   ↓
meglévő SliceDesigner pipeline
```

A plugin feladata a modell létrehozása.

A plugin nem vesz részt a Mesh további feldolgozásában.

---

# 3. Alapelvek

## 3.1. A plugin opcionális

A SliceDesignernek plugin nélkül is teljes értékűen működnie kell.

Egy plugin hiánya nem akadályozhatja:

* a SliceDesigner indulását;
* a core működését;
* az STL importot;
* a meglévő slicing folyamatot;
* a downstream pipeline működését.

---

## 3.2. A plugin külön telepíthető

A plugin a SliceDesigner core-tól elkülönített Python package-ként telepíthető.

A core telepítése nem igényli az opcionális plugin jelenlétét.

---

## 3.3. A plugin a MeshSource contracton keresztül kapcsolódik

A plugin nem kap közvetlen hozzáférést a SliceDesigner teljes belső architektúrájához.

A kapcsolódási pont:

```text
SliceDesigner Core
       │
       ▼
MeshSource contract
       ▲
       │
     Plugin
```

A core a contractot biztosítja.

A plugin annak implementációját biztosítja.

---

## 3.4. A plugin Mesh-t állít elő

A plugin által létrehozott eredmény ugyanaz a `Mesh` domainobjektum, amelyet a core által biztosított MeshSource-ok is használnak.

A downstream rendszer nem tesz különbséget:

```text
STL → Mesh
```

és:

```text
Plugin → Mesh
```

között.

---

## 3.5. A plugin nem módosítja a slicing pipeline-t

A plugin kizárólag a Mesh előállításának módját bővíti.

Nem módosíthatja:

* Slice Engine működését;
* Gap Engine működését;
* Dowel Engine működését;
* Backplate Engine működését;
* Numbering működését;
* Nesting működését;
* Export működését.

Ez biztosítja, hogy a plugin bevezetése ne hozzon létre külön slicing- vagy feldolgozási rendszert.

---

# 4. Miért plugin?

A plugin architektúra három alapvető célt szolgál.

### 4.1. Core stabilitás

A modellgenerátorok fejlesztése nem igényli a SliceDesigner core folyamatos módosítását.

### 4.2. Opcionális képességek

A felhasználó csak azokat a képességeket telepíti, amelyekre szüksége van.

### 4.3. Független fejlesztés

A Parametric Relief Generator saját fejlődési ciklussal rendelkezhet, miközben a SliceDesigner core változatlanul működhet.

---

# 5. Miért nem általános plugin-framework?

Jelenleg nincs dokumentált projektigény más plugin-típusokra.

Ezért nem kerül bevezetésre olyan általános architektúra, amely például:

* Export pluginokat;
* Post-processing pluginokat;
* teljes pipeline pluginokat;
* GUI pluginokat;
* egyéb extension pointokat

is kezelne.

Az ilyen általánosítás jelenleg szükségtelen komplexitást jelentene.

Ha a projekt később más plugin-típusra is igényt támaszt, az külön architekturális döntést igényel.

---

# 6. Core és plugin felelősségi határa

## Core

A core felelős:

* a MeshSource contractért;
* a pluginok felismeréséért;
* a kompatibilitás ellenőrzéséért;
* a MeshSource-ok regisztrációjáért;
* a MeshSource-ok felhasználói felületen való elérhetővé tételéért;
* a MeshSource meghívásáért;
* a kapott Mesh további feldolgozásáért.

## Plugin

A plugin felelős:

* saját MeshSource implementációjáért;
* saját bemeneti paramétereiért;
* saját validációjáért;
* saját modellgenerálási logikájáért;
* érvényes Mesh előállításáért;
* saját hibáinak megfelelő jelzéséért.

---

# 7. Plugin izoláció

A plugin hibája nem veszélyeztetheti a core működését.

Egy inkompatibilis vagy hibás plugin:

* nem válhat használható MeshSource-szá;
* nem akadályozhatja a SliceDesigner indulását;
* nem teheti használhatatlanná a többi MeshSource-ot.

A plugin hibája a plugin határán kezelendő.

---

# 8. Plugin kompatibilitás

A plugin és a core között kompatibilitási követelmény áll fenn.

A pluginnek kompatibilisnek kell lennie a SliceDesigner által biztosított `MeshSource` contracttal.

A következő fogalmak külön kezelendők:

```text
Plugin version
        ≠
MeshSource contract version
```

A konkrét verziókezelési mechanizmus jelen ADR-ben nincs rögzítve.

Annak technikai meghatározása csak akkor kerül külön döntésként dokumentálásra, ha az implementációhoz szükséges.

---

# 9. Plugin discovery és registration

A SliceDesignernek képesnek kell lennie a telepített MeshSource pluginok automatikus felismerésére.

Új plugin hozzáadásához nem lehet szükséges a core forráskódjának módosítása.

A discovery és registration mechanizmus:

```text
telepített plugin
       ↓
discovery
       ↓
kompatibilitás ellenőrzése
       ↓
registration
       ↓
elérhető MeshSource
```

A konkrét Python packaging/discovery mechanizmus jelen ADR-ben nem kerül rögzítésre.

Ez technikai megvalósítási döntés.

---

# 10. Felhasználói működés

A plugin telepítése után annak MeshSource-a megjelenik a SliceDesigner által elérhető modellforrások között.

Például:

```text
Model Source

○ STL file
○ Relief Generator
```

A plugin saját paramétereit maga kezeli.

A core számára a folyamat:

```text
felhasználói bemenet
       ↓
plugin MeshSource
       ↓
Mesh
       ↓
SliceDesigner pipeline
```

---

# 11. Első konkrét plugin

Az architektúra első alkalmazása:

**Parametric Relief Generator**

Ez egy opcionális MeshSource plugin lesz.

A plugin saját dokumentációja fogja meghatározni:

* a bemeneti adatokat;
* a paramétereket;
* a geometriai modellt;
* a generálási algoritmust;
* a validációt.

Ezek nem részei ennek az ADR-nek.

---

# 12. Alternatívák

## A. Relief Generator közvetlenül a core-ban

**Elutasítva.**

Indok:

* a core feleslegesen függne a generátortól;
* opcionális képességből kötelező core-komponens válna;
* a generátor fejlesztése közvetlenül érintené a core-t.

---

## B. Általános plugin-framework

**Elutasítva jelenleg.**

Indok:

* nincs rá jelenleg dokumentált igény;
* szükségtelen absztrakciót és komplexitást vezetne be;
* túlmutat a jelenlegi MeshSource problémán.

---

## C. Különálló Relief Generator alkalmazás

**Nem választott megoldás.**

Bár technikailag működőképes lehetne, a projekt célja az, hogy a generált Mesh közvetlenül a SliceDesigner modellforrásai között legyen használható.

A plugin megoldás ezt úgy biztosítja, hogy közben a core opcionális marad.

---

## D. MeshSource plugin

**Elfogadva.**

Ez biztosítja a szükséges bővíthetőséget a lehető legkisebb architekturális kiterjesztéssel.

---

# 13. Következmények

## Pozitív következmények

* A SliceDesigner core változatlanul használható plugin nélkül.
* A modellgenerátorok külön fejleszthetők.
* A downstream slicing pipeline változatlan marad.
* Új MeshSource hozzáadása nem igényel core-kódmódosítást.
* A plugin saját paraméter- és generálási logikát kezelhet.
* A rendszer egyszerű marad.

## Negatív következmények

* Plugin discovery mechanizmust kell biztosítani.
* Kompatibilitást kell kezelni.
* A plugin és core közötti contractot stabilan fenn kell tartani.
* A pluginok telepítése külön kezelendő.

Ezek a többletkomplexitások szükségesek az opcionális bővítéshez.

---

# 14. Hatókörön kívüli döntések

Jelen ADR nem dönt:

* a konkrét Python entry-point mechanizmusról;
* a plugin package pontos könyvtárstruktúrájáról;
* a plugin GUI konkrét megvalósításáról;
* a Relief Generator algoritmusáról;
* a HeightField domainmodellről;
* a relief paramétermodellről;
* a plugin marketplace-ről;
* automatikus plugin-letöltésről;
* sandboxolásról;
* más plugin-típusok támogatásáról.

---

# 15. Kapcsolódó dokumentumok

* `MESH_SOURCE.md`
* `ADR_MESH_SOURCE.md`
* `DOMAIN_MODEL.md`
* `ARCHITECTURE.md`
* `PLUGIN_ARCHITECTURE.md`

---

# 16. Döntés összefoglalása

A SliceDesigner **opcionális, külön telepíthető MeshSource pluginokat** támogat.

A plugin:

```text
külön package
      ↓
MeshSource contract
      ↓
Mesh
      ↓
meglévő SliceDesigner pipeline
```

A plugin hiánya nem érinti a core működését.

A plugin kizárólag a modell előállítását bővíti.

A projekt jelenlegi állapotában nem vezetünk be általános plugin-frameworköt.

Az első konkrét plugin a **Parametric Relief Generator**.

---

# 17. Státusz

**Tervezet — projektgazdai jóváhagyásra vár.**
