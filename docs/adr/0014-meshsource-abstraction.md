# ADR-0014: MeshSource modellforrás-absztrakció bevezetése

Dátum: 2026-08-15
Státusz: Elfogadva
Döntéshozó: Horváth Gyula Attila (projektgazda)

## Kontextus

A SliceDesigner jelenlegi feldolgozási modelljében a háromdimenziós modell STL importon keresztül kerül a domain rétegbe, majd `Mesh` formában jut tovább a slicing pipeline-ba.

A további fejlődés során szükségessé vált olyan modellforrások támogatása, amelyek nem meglévő STL fájlból származnak — az első ilyen eset a tervezett parametrikus relief-generátor (Relief Generator Plugin, ROADMAP Phase 8), amely külön telepíthető, opcionális plugin formájában állít elő feldolgozható Mesh-t.

A cél nem a slicing pipeline módosítása, hanem annak lehetővé tétele, hogy a pipeline ugyanazt a `Mesh` domain objektumot több, egymástól független modellforrásból fogadhassa, úgy, hogy a SliceDesigner core plugin nélkül is teljes értékű maradjon.

## Döntés

Bevezetjük a **`MeshSource` modellforrás-absztrakciót**: egy domain-szintű szerződést, amelynek eredménye mindig egy érvényes `Mesh` objektum.

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

A `MeshSource` megvalósításai közé tartozik a meglévő STL-import (mint a jelenlegi, egyetlen megvalósítás), valamint a jövőbeni egyéb import- és generáló források. Az opcionális generáló források — elsőként a parametrikus relief-generátor — külön telepíthető Python package-ként valósulhatnak meg; a SliceDesigner core nem tartalmazhat kötelező függőséget ezekre.

A döntés részletei:

* minden MeshSource közös kimenete a meglévő `Mesh` domain objektum — a downstream pipeline a Mesh eredete alapján nem tehet különbséget;
* minden MeshSource saját, forrás-specifikus paraméterobjektummal rendelkezik; a core `MeshSource` contract ilyet nem tartalmaz;
* a `MeshSource` contract lehetővé teszi külső modellforrások plugin formájában történő hozzáadását; a plugin hiánya nem akadályozhatja a core használatát;
* a `MeshSource` contract nem tartalmaz GUI-szerződést — a geometriai logika nem kerülhet a GUI rétegbe;
* a `Mesh.source_path` opcionálissá válik: importált modell esetén a forrásfájl útvonala, generált modell esetén `None` (a `DOMAIN_MODEL.md` tartalmi módosítása jelen ADR-rel egy időben megtörténik; a `src/slicedesigner/engines/mesh_import.py` `Mesh` dataclass tényleges kódbeli módosítása a Relief Generator Plugin implementációjának feladata marad, ld. Következmények);
* a MeshSource-oknak a SliceDesigner általános determinisztikus működésre és fail-fast hibakezelésre vonatkozó elveit kell követniük;
* a `MeshSource` contract verziózott interfész — a konkrét verziókezelési és plugin-kompatibilitási mechanizmus külön, későbbi implementációs döntés tárgya.

## Mérlegelt alternatívák

* **A relief-generátor közvetlen beépítése a SliceDesigner core-ba** — elutasítva: fölösleges függőséget hozna létre a core és egy konkrét modellgenerátor között, miközben a relief-generátor jellegénél fogva opcionális modellforrás.
* **A generált Mesh STL-en keresztüli visszatöltése** (`Relief Generator → STL → STL Import → Mesh`) — elutasítva: fölösleges szerializációt és újraparszolást jelentene, és összemosná a fájlformátumot a domain modellel; a helyes adatfolyam közvetlen (`Relief Generator → Mesh`).
* **Külön slicing pipeline a generált modellekhez** — elutasítva: a generált modell ugyanúgy `Mesh`, nincs domain-szintű indok külön pipeline-ra.
* **Általános, több plugin-típust kiszolgáló plugin-framework bevezetése már most** — elutasítva: nincs rá dokumentált igény, szükségtelen absztrakciót vezetne be, túlmutat a jelenlegi problémán (Engineering Principles, egyszerűség elve).

## Következmények

* Új modellforrások hozzáadhatók a slicing pipeline módosítása nélkül; a Relief Generator Plugin önállóan fejleszthető.
* A downstream pipeline (Slice Engine-től a DXF Exportig) változatlan `Mesh` contracton dolgozik, egyetlen engine sem változik emiatt (ld. `ARCHITECTURE.md` frissítése).
* A `DOMAIN_MODEL.md` `Mesh` fogalmának definíciója és attribútumlistája módosul (`source_path` opcionálissá válik) — ezt jelen ADR-rel egy időben, külön prompttal vezetjük át.
* A `src/slicedesigner/engines/mesh_import.py` `Mesh` dataclass tényleges kódbeli módosítása (`source_path: str` → `source_path: str | None`) ezzel az ADR-rel még nem történik meg — az a Relief Generator Plugin implementációjának (ROADMAP Phase 8) feladata marad.
* A plugin discovery, telepítés és GUI-integráció technikai mechanizmusa jelen ADR hatókörén kívül esik; ezeket külön dokumentáció (plugin architektúra ADR, `PLUGIN_ARCHITECTURE.md` véglegesítése) rendezi a Phase 8 további lépéseiben.
