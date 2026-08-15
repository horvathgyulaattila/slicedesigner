# DOMAIN_MODEL.md módosítási terv — MeshSource

**Státusz:** Tervezet
**Alapdokumentumok:** `MESH_SOURCE.md`, `ADR_MESH_SOURCE`
**Cél:** A MeshSource döntés domainmodellre gyakorolt következményeinek átvezetése

---

## 1. Cél

A `DOMAIN_MODEL.md` módosítása annak érdekében, hogy a `Mesh` fogalma összhangba kerüljön a jóváhagyott `MeshSource` architekturális modellel.

A módosítás alapvető célja annak rögzítése, hogy:

> A `Mesh` a SliceDesigner által feldolgozandó háromdimenziós geometria domain objektuma, függetlenül attól, hogy importból vagy generálásból származik.

A `MeshSource` azt határozza meg, **hogyan jön létre** a Mesh; a `Mesh` pedig magát a feldolgozandó geometriát reprezentálja.

---

# 2. Érintett dokumentumok

### Közvetlenül érintett

* `docs/DOMAIN_MODEL.md`

### Kapcsolódó, már jóváhagyott dokumentumok

* `docs/MESH_SOURCE.md`
* `docs/adr/ADR_MESH_SOURCE.md`
* `docs/ARCHITECTURE.md`

### Később érinthető, de jelen módosításban nem módosítandó

* `docs/specifications/MESH_IMPORT_SPEC.md`
* `docs/PROJECT_STRUCTURE.md`
* plugin architecture dokumentáció
* parametrikus relief dokumentáció

A jelen terv nem írja elő ezek módosítását.

---

# 3. Érintett könyvtárak

A domainmodell módosítása dokumentációs szinten történik.

Új könyvtár létrehozása nem szükséges.

A későbbi implementáció során a `MeshSource` konkrét implementációinak helye külön architekturális döntés tárgya.

---

# 4. A jelenlegi probléma

A jelenlegi `DOMAIN_MODEL.md` a `Mesh` fogalmát így definiálja:

> A felhasználó által importált háromdimenziós modell.

Ez az új architektúrával már túl szűk.

A jóváhagyott modell szerint többféle forrás hozhat létre Mesh-t:

```text
STL import
    ↓
STL MeshSource
    ↓
Mesh
```

illetve:

```text
parametrikus generálás
    ↓
Relief MeshSource
    ↓
Mesh
```

A két eset domain szempontból ugyanazt az objektumot eredményezi.

Ezért az import eredete nem lehet a `Mesh` definíciójának része.

---

# 5. A Mesh új domain-definíciója

A `Mesh` definícióját általánosítani kell.

### Javasolt új definíció

> **Mesh:** A SliceDesigner által feldolgozandó háromdimenziós geometria domain reprezentációja.

### Szerepe

A Mesh a slicing folyamat bemeneti geometriai alapja, amelyből a Slice Set létrejön.

A Mesh származhat:

* fájlból történő importból;
* parametrikus vagy algoritmikus generálásból;
* későbbi, dokumentált MeshSource megvalósításból.

A konkrét eredet azonban nem változtatja meg a Mesh domain jelentését.

---

# 6. Mesh attribútumok módosítása

A jelenlegi attribútumlista:

* geometriai reprezentáció jellege;
* forrásfájl-hivatkozás;
* méret/bounding box;
* validáltsági állapot.

A lista alapvetően megtartható, de a **forrásfájl-hivatkozás jelentését pontosítani kell**.

### Javasolt állapot

* geometriai reprezentáció jellege;
* opcionális forrásfájl-hivatkozás;
* méret/bounding box;
* validáltsági állapot.

A forrásfájl-hivatkozás nem kötelező attribútum.

---

# 7. `source_path` szemantikája

A domainmodellnek egyértelműen rögzítenie kell:

```text
source_path: str | None
```

### Importált Mesh esetén

```text
source_path = <forrásfájl elérési útja>
```

### Generált Mesh esetén

```text
source_path = None
```

A `None` érték érvényes domainállapot.

Nem hibát, hiányos Mesh-t vagy érvénytelen állapotot jelent.

Jelentése:

> A Mesh-nek nincs fájlalapú forrása.

---

# 8. Fontos fogalmi határ

A domainmodellben egyértelműen külön kell választani:

```text
MeshSource
    ↓
Mesh
```

A `MeshSource` felelőssége:

* a modell előállítása;
* a forrás-specifikus bemenet kezelése;
* a forrás-specifikus validáció;
* érvényes Mesh előállítása.

A `Mesh` felelőssége:

* a feldolgozandó geometria reprezentációja.

A Mesh nem felelős azért, hogy milyen algoritmus vagy fájlformátum hozta létre.

---

# 9. Amit nem szabad a Mesh domainfogalomba beemelni

A Mesh attribútumai közé nem kerülnek source-specifikus adatok csak azért, hogy megőrizzük a keletkezés módját.

Jelen módosítás alapján nem kerül a Mesh-be például:

* `source_type`;
* `plugin_name`;
* `generator_name`;
* `generator_version`;
* relief-generátor paraméterek;
* HeightField;
* MeshSource konfiguráció.

Ezek nem részei a Mesh általános domainfogalmának.

Ha a jövőben szükségessé válik részletes eredet- vagy provenance-információ megőrzése, az külön domainmodellbeli döntést igényel.

---

# 10. A Mesh invariánsai

A Mesh eredetétől függetlenül ugyanazok az alapvető domainkövetelmények érvényesek.

A Mesh:

* érvényes háromdimenziós geometriai reprezentáció;
* a projekt által meghatározott koordinátarendszert használja;
* milliméter alapú geometriai értékeket használ;
* alkalmas a Slice Engine számára bemenetként szolgálni;
* validált állapotban kerülhet a downstream pipeline-ba.

A Mesh eredete nem része ezeknek az invariánsoknak.

---

# 11. Slice Set kapcsolatának módosítása

A jelenlegi kapcsolat:

```text
Mesh
 ↓
Slice Set
```

változatlan marad.

A változás csak az előtte lévő modellforrás rétegben történik:

```text
MeshSource
    ↓
Mesh
    ↓
Slice Set
```

A Slice Set továbbra is egy Mesh-ből származik.

A Slice Set számára nincs jelentősége annak, hogy a Mesh importált vagy generált.

Ezért a Slice Set domainmodelljét nem szükséges módosítani.

---

# 12. Project kapcsolatának módosítása

A Project jelenlegi Mesh-referenciája továbbra is érvényes.

A Project nem közvetlenül egy STL fájlhoz vagy konkrét generátorhoz kötődik, hanem a létrehozott Mesh-hez.

Ezért:

```text
Project
   ↓
Mesh
```

továbbra is helyes domainkapcsolat.

A `MeshSource` kiválasztásának és kezelésének pontos helye nem része ennek a módosításnak; azt az Architecture és későbbi plugin-dokumentáció kezeli.

---

# 13. Fogalmi kapcsolatok módosítása

A jelenlegi:

> Egy Project egy Mesh-t tartalmaz.

kapcsolat változatlanul érvényes.

A:

> Egy Mesh-ből Slice Set készül.

kapcsolat szintén változatlan.

A módosítás azzal egészül ki, hogy a Mesh keletkezési módja nem része ezeknek a kapcsolatoknak.

Fogalmi szinten:

```text
MeshSource
     │
     ▼
    Mesh
     │
     ▼
 Slice Set
```

---

# 14. STL Import helye a Domain Modelben

Az STL Import továbbra is létező rendszerfunkció.

Azonban a `Mesh` definíciójában nem szerepelhet úgy, mint a Mesh létrejöttének kizárólagos módja.

A domainmodell szintjén:

```text
STL Import
```

egy konkrét modellforrás.

Nem külön domainobjektumként kell hozzáadni a Mesh mellé, hanem a `MeshSource` architekturális modellhez tartozó konkrét forrásként kezelendő.

A `MESH_IMPORT_SPEC.md` későbbi felülvizsgálata külön feladat lehet, de jelen terv nem írja elő annak azonnali módosítását.

---

# 15. Visszafelé kompatibilitás

## Megmarad

* a `Mesh` mint a slicing bemeneti domain objektuma;
* a `Mesh → Slice Set` kapcsolat;
* a Project Mesh-referenciája;
* az STL importálás;
* a meglévő downstream pipeline Mesh-alapú működése.

## Változik

* a Mesh definíciója nem kizárólag importált modellre vonatkozik;
* a forrásfájl-hivatkozás opcionálissá válik;
* a generált Mesh érvényes domainállapot lesz.

## Nem változik

* Slice;
* Slice Set;
* Gap;
* Dowel;
* Spacer;
* Backplate;
* Numbering;
* Material;
* Nest;
* Assembly;
* Export.

---

# 16. Implementációs részletek határa

A `DOMAIN_MODEL.md` továbbra is technológiafüggetlen marad.

Ezért a módosítás nem rögzíti:

* Python type annotation konkrét szintaxisát;
* konkrét osztálystruktúrát;
* plugin package struktúrát;
* import API-t;
* plugin discovery mechanizmust;
* factory mechanizmust;
* dependency injectiont;
* GUI-integrációt.

A `source_path: str | None` a domain fogalom szintjén értendő; a konkrét Python implementáció az implementációs fázis feladata.

---

# 17. Impact Analysis

## Érintett dokumentumok

**Közvetlenül:**

* `DOMAIN_MODEL.md`

**Már meglévő alapdöntés:**

* `MESH_SOURCE.md`
* `ADR_MESH_SOURCE.md`

**Kapcsolódó dokumentum:**

* `ARCHITECTURE.md`

## Érintett könyvtárak

Dokumentációs könyvtár:

* `docs/`

Új könyvtár nem szükséges.

## Szükséges dokumentummódosítás

A `DOMAIN_MODEL.md` alábbi részei módosítandók:

1. `Mesh` definíció;
2. `Mesh` szerepe;
3. `Mesh` attribútumai;
4. `Mesh` és Project/Slice Set kapcsolatokhoz tartozó fogalmi megjegyzések, amennyiben azok az import eredetére utalnak;
5. szükség esetén a dokumentum elején lévő kapcsolódó dokumentumok listája, ha az új ADR-re való hivatkozás projektben használt konvenció szerint szükséges.

## Szükséges új ADR

**Nem szükséges új ADR.**

A változtatás kizárólag az elfogadott `ADR_MESH_SOURCE.md` domainmodellre gyakorolt következményeinek átvezetése.

Új ADR csak akkor válik szükségessé, ha a Domain Model módosítása során olyan új architekturális döntés merül fel, amely túlmutat a már elfogadott MeshSource modellen.

## Visszafelé kompatibilitás

A downstream domainmodell kompatibilis marad.

A lényegi változás:

```text
Mesh.source_path
kötelező
   ↓
opcionális
```

Az importált modellek működési jelentése nem változik.

Új képességként megjelenik a fájl nélküli, generált Mesh lehetősége.

---

# 18. Hatókörön kívül

A jelen terv nem dönt:

* plugin architecture-ről;
* plugin discovery-ről;
* plugin telepítéséről;
* GUI plugin-integrációról;
* HeightField modellről;
* Relief Generator domainmodelljéről;
* relief-generálási algoritmusról;
* provenance modellről;
* MeshSource verziókezelésének technikai megvalósításáról.

Ezek csak a Mesh domainmodell stabilizálása után kerülnek sorra.

---

# 19. Elfogadási kritériumok

A `DOMAIN_MODEL.md` módosítás akkor tekinthető megfelelőnek, ha:

1. a Mesh definíciója már nem korlátozódik importált modellekre;
2. a Mesh általános háromdimenziós geometriai domainobjektumként jelenik meg;
3. az importált és generált Mesh ugyanabba a domainfogalomba tartozik;
4. a forrásfájl-hivatkozás opcionális;
5. a `source_path = None` érvényes állapot;
6. a source-specifikus paraméterek nem kerülnek a Mesh-be;
7. a Slice Set továbbra is Mesh-ből származik;
8. a Project továbbra is Mesh-referenciát kezel;
9. a downstream domainfogalmak nem változnak;
10. a dokumentum technológiafüggetlen marad;
11. az új változtatás nem vezet be új, nem jóváhagyott architekturális döntést;
12. a módosítás összhangban marad a `MESH_SOURCE.md` és az `ADR_MESH_SOURCE` tartalmával.

---

# 20. Célállapot

A domainmodell lényegi szerkezete:

```text
             MeshSource
            /          \
     STL Import       Generator
            \          /
             \        /
                Mesh
                 │
                 ▼
             Slice Set
                 │
                 ▼
               Slice
                 │
                 ▼
          további domain
```

A kulcsfontosságú fogalmi elválasztás:

```text
MeshSource = a geometria létrehozásának forrása
Mesh       = maga a feldolgozandó geometria
```

Ez a különválasztás biztosítja, hogy a jövőbeni modellgenerátorok ne kényszerítsenek új domainmodellt a meglévő slicing pipeline-ra.

---

## 21. Státusz

**Tervezet — projektgazdai jóváhagyásra vár.**

A `DOMAIN_MODEL.md` tényleges módosítása csak a jelen terv jóváhagyása után történhet, a projekt aktuális workflow-ja szerint.
