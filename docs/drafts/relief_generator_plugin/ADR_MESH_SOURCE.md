# ADR: MeshSource modellforrás-absztrakció bevezetése

- **Státusz:** Tervezet
- **Dátum:** 2026-08-08
- **Döntés tárgya:** Modellforrások egységes kezelése
- **Kapcsolódó dokumentum:** `docs/MESH_SOURCE.md`

## 1. Kontextus

A SliceDesigner jelenlegi feldolgozási modelljében a háromdimenziós modell STL importon keresztül kerül a domain rétegbe, majd `Mesh` formában jut tovább a slicing pipeline-ba.

A további fejlődés során szükségessé vált olyan modellforrások támogatása, amelyek nem meglévő STL fájlból származnak. Az első ilyen eset a tervezett parametrikus relief-generátor, amely külön telepíthető, opcionális plugin formájában állít elő feldolgozható Mesh-t.

A cél nem a slicing pipeline módosítása, hanem annak lehetővé tétele, hogy a pipeline ugyanazt a `Mesh` domain objektumot több, egymástól független modellforrásból fogadhassa.

A megoldásnak biztosítania kell, hogy:

- a SliceDesigner plugin nélkül is teljes értékű maradjon;
- a core ne függjön opcionális pluginoktól;
- a különböző modellforrások ne okozzanak külön downstream feldolgozási ágakat;
- a forrás-specifikus geometriai logika a saját komponensén belül maradjon;
- a későbbi modellgenerátorok ugyanarra az architekturális szerződésre épülhessenek.

## 2. Döntés

Bevezetjük a **`MeshSource` modellforrás-absztrakciót**.

A `MeshSource` olyan domain-szintű szerződés, amelynek eredménye egy érvényes `Mesh` objektum.

Az alapvető adatfolyam:

```text
MeshSource
    ↓
Mesh
    ↓
Slice Engine
    ↓
további pipeline
```

A `MeshSource` megvalósításai közé tartozik a meglévő STL-import, valamint a jövőbeni egyéb import- és generáló források.

Az opcionális generáló források — elsőként a parametrikus relief-generátor — külön telepíthető Python package-ként valósulhatnak meg.

A SliceDesigner core nem tartalmazhat kötelező függőséget ezekre az opcionális package-ekre.

## 3. A döntés részletei

### 3.1. A MeshSource kimenete

Minden MeshSource közös kimenete a meglévő `Mesh` domain objektum.

A downstream pipeline a Mesh eredete alapján nem tehet különbséget.

Ennek eredményeként a slicing, assembly, nesting és export folyamatok változatlanul a `Mesh` domain modellen keresztül működnek.

### 3.2. Source-specifikus paraméterek

Minden MeshSource saját paraméterobjektummal rendelkezik.

A core `MeshSource` contract nem tartalmazhat egy adott forrás számára specifikus paramétereket.

Ez lehetővé teszi, hogy az egyes modellforrások saját domain logikájukat és konfigurációjukat önállóan kezeljék.

### 3.3. Opcionális pluginok

A MeshSource contract lehetővé teszi külső modellforrások plugin formájában történő hozzáadását.

A plugin:

- külön telepíthető;
- saját MeshSource implementációt biztosít;
- saját paramétermodellt használ;
- saját geometriai logikájáért felel;
- a SliceDesigner core downstream feldolgozását nem módosítja.

A plugin hiánya nem akadályozhatja a core használatát.

### 3.4. GUI-határ

A MeshSource contract nem tartalmaz GUI-szerződést.

A plugin felhasználói felületének konkrét megoldása későbbi architekturális döntés tárgya.

A geometriai logika nem kerülhet a GUI rétegbe.

### 3.5. Mesh eredete

A `Mesh.source_path` opcionális.

Importált modell esetén tartalmazhatja a forrásfájlt; generált modell esetén `None` lehet.

A Mesh feldolgozás nem támaszkodhat arra a feltételezésre, hogy minden Mesh mögött fizikai forrásfájl áll.

### 3.6. Determinizmus és hibakezelés

A MeshSource-oknak követniük kell a SliceDesigner determinisztikus működésre és fail-fast hibakezelésre vonatkozó általános elveit.

Azonos dokumentált bemenetek és seed mellett reprodukálható eredmény szükséges.

Érvénytelen bemenet esetén a MeshSource nem adhat át tudottan hibás Mesh-t a downstream pipeline-nak.

### 3.7. Contract verziózása

A MeshSource contract verziózott architekturális interfész.

A konkrét verziókezelési és plugin-kompatibilitási mechanizmus külön döntés tárgya; jelen ADR csak azt rögzíti, hogy a kompatibilitásnak explicit módon kezelhetőnek kell lennie.

## 4. Miért ezt a megoldást választjuk?

A döntés legfontosabb oka a **felelősségek szétválasztása**.

A Mesh létrehozása és a Mesh feldolgozása két külön felelősség:

```text
modell létrehozása
        ↓
      Mesh
        ↓
modell feldolgozása
```

A slicing engine-nek nem kell tudnia, hogy a Mesh STL-ből, parametrikus algoritmusból vagy később más pluginból származik.

Ez megakadályozza, hogy minden új modellforrás új slicing-pipeline ágat igényeljen.

A megoldás továbbá lehetővé teszi, hogy a parametrikus relief-generátor önállóan fejlődjön anélkül, hogy a SliceDesigner core-ba kerülne a teljes generálási logika.

## 5. Elutasított alternatívák

### 5.1. A relief-generátor közvetlen beépítése a SliceDesigner core-ba

**Elutasítva.**

Ez a core és egy konkrét modellgenerátor közötti fölösleges függőséget eredményezne.

A parametrikus relief-generátor opcionális modellforrás.

### 5.2. A generált Mesh STL-en keresztüli visszatöltése

```text
Relief Generator
    ↓
STL
    ↓
STL Import
    ↓
Mesh
```

**Elutasítva.**

Ez fölösleges serializációt és újraparszolást jelentene, valamint összemossa a fájlformátumot a domain modellel.

A helyes adatfolyam közvetlen:

```text
Relief Generator
    ↓
Mesh
```

### 5.3. Külön slicing pipeline a generált modellekhez

**Elutasítva.**

A generált modell ugyanúgy `Mesh`, ezért nincs domain-szintű indok külön slicing pipeline fenntartására.

### 5.4. A parametrikus relief-generátor önálló alkalmazásként történő elsődleges integrációja

**Elutasítva mint elsődleges architekturális megoldás.**

A generátor jelenlegi célja opcionális SliceDesigner modellforrásként való működés.

Az algoritmikus core későbbi önálló felhasználhatóságát az architektúra nem akadályozza, de ez nem része a jelen döntésnek.

### 5.5. Pluginfüggőség beépítése a SliceDesigner core-ba

**Elutasítva.**

A SliceDesignernek plugin nélkül is működőképesnek kell maradnia.

## 6. Következmények

### Pozitív következmények

- Új modellforrások hozzáadhatók a slicing pipeline módosítása nélkül.
- Az opcionális pluginok elkülöníthetők a core-tól.
- A Relief Generator önállóan fejleszthető.
- A downstream pipeline változatlan Mesh contracton dolgozhat.
- A későbbi import- és generátorforrások ugyanarra az architekturális mintára épülhetnek.
- Csökken az új modellforrások által okozott core-komplexitás.

### Negatív következmények

- A SliceDesignernek új `MeshSource` absztrakciót és annak kezelését kell bevezetnie.
- A plugin-kompatibilitás és discovery kérdéseit meg kell oldani.
- A `Mesh` domain modell `source_path` szemantikája módosítást igényel.
- A külső pluginok kompatibilitásának kezelése hosszú távon karbantartási feladatot jelent.

## 7. Hatókörön kívül hagyott döntések

Jelen ADR nem dönt:

- a plugin discovery konkrét technikai mechanizmusáról;
- a plugin telepítésének részletes folyamatáról;
- a GUI plugin-contractjáról;
- a HeightField domain modellről;
- a relief-generálás algoritmusáról;
- a konkrét relief-paraméterekről;
- a plugin package build- és release-folyamatáról;
- a contract verziózás konkrét technikai megvalósításáról.

Ezeket a jelen ADR és a `MESH_SOURCE.md` alapján, külön dokumentációs lépésekben kell kidolgozni.

## 8. Kapcsolódó dokumentáció

- `docs/MESH_SOURCE.md` — a MeshSource contract részletes specifikációja.
- `ARCHITECTURE.md` — a SliceDesigner architektúrájának frissítendő dokumentuma.
- `DOMAIN_MODEL.md` — a Mesh domain modell szükséges módosításainak helye.
- `ENGINEERING_PRINCIPLES.md` — determinisztikus és fail-fast működési alapelvek.

## 9. Következő lépések

Az ADR elfogadása után:

1. az `ARCHITECTURE.md` módosítása;
2. a `DOMAIN_MODEL.md` módosítása, különösen a `source_path` opcionálissá tétele miatt;
3. a plugin-architektúra és discovery külön dokumentálása;
4. a parametrikus relief plugin domain modelljének megtervezése;
5. a HeightField contract dokumentálása;
6. csak ezután implementáció.

## 10. Státusz

**Tervezet.**

Az ADR addig nem tekintendő végleges architekturális döntésnek, amíg a projekt tulajdonosa külön nem hagyja jóvá.
