# ARCHITECTURE.md módosítási terv — MeshSource

**Státusz:** Tervezet  
**Alap:** `MESH_SOURCE.md` + elfogadott `ADR_MESH_SOURCE.md`

## Cél

Az `ARCHITECTURE.md` úgy módosuljon, hogy az architektúra hivatalos leírása már ne az STL-importot tekintse az egyetlen modellbelépési pontnak, hanem az elfogadott `MeshSource` absztrakciót.

A módosításnak **nem célja** a teljes Architecture dokumentum átszervezése.

---

## 1. Meglévő állapot

Az aktuális `ARCHITECTURE.md` a Mesh Importot önálló Domain komponensként írja le, amely STL-t tölt be és Mesh domain objektumot állít elő. A pipeline jelenlegi ábrája:

```text
Mesh Import → Slice Engine → Dowel Engine → Gap Engine → Backplate Engine
     → Numbering Engine → Nesting Engine   ⇢   DXF Export Engine
```

A problémát nem maga az STL-import jelenti, hanem az a feltételezés, hogy **a Mesh kizárólag importból származhat**.

---

# 2. Szükséges architekturális változás

A modellforrás belépési pontját általánosítani kell:

```text
GUI
 ↓
Project
 ↓
MeshSource
 ↓
Mesh
 ↓
Slice Engine
 ↓
további pipeline
```

A `MeshSource` több konkrét megvalósítást fogadhat:

```text
              MeshSource
              /    |    \\
             /     |     \\
      STL Source  Relief  ...
             \\     |     /
              \\    |    /
                  Mesh
                   ↓
             Slice Engine
```

Az `ARCHITECTURE.md` számára ebből az következik, hogy a **Mesh előállítása** és a **Mesh feldolgozása** külön architekturális felelősségként jelenjen meg.

---

# 3. Módosítandó részek

## 3.1. Fő komponensek — Mesh Import

A jelenlegi `Mesh Import` komponens megnevezését és felelősségleírását általánosítani kell.

### Javasolt fogalmi változás

**Régi szemlélet:**

> Mesh Import: STL formátumú modell betöltése, validálása, Mesh domain objektum előállítása.

**Új szemlélet:**

> MeshSource: modellforrásból feldolgozható Mesh domain objektum előállítása.

Az STL-import ezután egy konkrét MeshSource megvalósításként jelenjen meg.

**Nem cél:** a `Mesh Import` teljes fogalmának eltüntetése. Az STL-import továbbra is létező komponens/funkció marad, csak nem az architekturális modellforrás-absztrakció neve.

---

## 3.2. Adatfolyam / munkafolyamat

A jelenlegi pipeline-ábrát úgy kell módosítani, hogy a Mesh előállítási pontján `MeshSource` szerepeljen.

### Célállapot

```text
MeshSource → Slice Engine → Dowel Engine → Gap Engine → Backplate Engine
     → Numbering Engine → Nesting Engine   ⇢   DXF Export Engine
     └──────────── automatikus (Futtatás) ────────────┘   (explicit interakció)
```

A szöveges magyarázatban:

- a `MeshSource` állítja elő a Mesh-t;
- az STL-import ennek egy konkrét megvalósítása;
- a Slice Engine továbbra is kizárólag a Mesh-et kapja bemenetként;
- a downstream pipeline többi része nem változik.

A pipeline sorrendjét, a Dowel/Gap/Backplate/Numbering/Nesting kapcsolatokat és a DXF Export leválasztását nem kell újraértelmezni.

---

## 3.3. Project szerepe

A Project felelősségleírását ki kell egészíteni annyival, hogy a modellforrás kiválasztását és a megfelelő `MeshSource` használatát koordinálja.

A Project továbbra is:

- koordinál;
- paramétereket továbbít;
- állapotot tart;
- pipeline-t futtat.

A Project **nem** tartalmazhat source-specifikus geometriai logikát.

---

## 3.4. Rétegek és felelősségi határok

A háromrétegű modell változatlan marad:

```text
GUI → Project → Domain
```

A `MeshSource` a Domain oldalon elhelyezkedő modell-előállítási felelősség.

A rétegek közötti architekturális kapcsolatot célszerű így pontosítani:

```text
GUI
  ↓
Project
  ↓
MeshSource
  ↓
Mesh
  ↓
Domain engine-ek
```

Ez nem új negyedik réteg; a `MeshSource` a Domain réteg része.

---

## 3.5. Opcionális pluginok

Az `ARCHITECTURE.md`-ben szükséges egy rövid architekturális megjegyzés az opcionális MeshSource pluginokról.

A dokumentum szintjén ezt kell rögzíteni:

- a MeshSource implementáció lehet a core része vagy opcionális külső plugin;
- a parametrikus relief-generátor opcionális plugin;
- a plugin külön telepíthető Python package;
- a plugin hiánya nem akadályozhatja a SliceDesigner core működését;
- a core és plugin közötti szerződés a MeshSource contract.

**Nem kell itt leírni** a plugin discovery konkrét technikai mechanizmusát. Az külön dokumentációs feladat.

---

# 4. Amit NEM kell módosítani

Az ADR alapján az alábbi architekturális elemekhez nincs szükség változtatásra:

### Slice Engine

Nem változik. Továbbra is `Mesh`-ből dolgozik.

### Dowel Engine

Nem változik.

### Gap Engine

Nem változik.

### Backplate Engine

Nem változik.

### Numbering Engine

Nem változik.

### Nesting Engine

Nem változik.

### DXF Export Engine

Nem változik.

### GUI általános rétegszerepe

Nem változik.

### Project koordinációs szerepe

Nem változik; csak a Mesh előállításának módja válik általánosabbá.

---

# 5. Amit szándékosan NEM döntünk el itt

Az `ARCHITECTURE.md` módosítása során nem kell eldönteni:

- hogyan fedezi fel a core a pluginokat;
- hogyan telepíthetők a pluginok;
- hogyan néz ki a plugin GUI-ja;
- hogyan működik a HeightField;
- hogyan működik a relief-generátor;
- milyen algoritmusból készül a relief;
- milyen konkrét Python package struktúrát használ a plugin;
- hogyan történik a MeshSource contract technikai verzióellenőrzése.

Ezeket az architektúra későbbi dokumentumai kezelik.

---

# 6. Mesh.source_path következménye

Az `ARCHITECTURE.md`-ben csak akkor szükséges erre kitérni, ha a jelenlegi dokumentum a Mesh eredetét vagy a source path jelentését architekturális szinten tárgyalja.

Ha ilyen rész nincs, **nem kell új domain részletet beemelni az Architecture dokumentumba**.

A `source_path: str | None` konkrét domain-modelbeli változását a `DOMAIN_MODEL.md` módosítási terve fogja kezelni.

---

# 7. Kapcsolódó ADR-ek

A meglévő `ARCHITECTURE.md` jelenleg az ADR-eket a `docs/adr/` mappából hivatkozza. A `MeshSource` döntést ugyanebbe a dokumentációs rendszerbe kell illeszteni.

Az Architecture dokumentum megfelelő helyén hivatkozni kell az elfogadott `ADR_MESH_SOURCE` döntésre.

A meglévő ADR-0001–ADR-0009 döntések tartalmát nem kell módosítani.

---

# 8. Dokumentációs sorrend

Az Architecture módosítás csak az alábbi elfogadott alapokra támaszkodhat:

1. `MESH_SOURCE.md`
2. `ADR_MESH_SOURCE.md`
3. `ARCHITECTURE.md`
4. `DOMAIN_MODEL.md`
5. plugin architecture
6. relief domain / HeightField
7. implementáció

Az Architecture dokumentum nem vezethet be új, még jóvá nem hagyott technikai döntést.

---

# 9. Elfogadási kritériumok

Az `ARCHITECTURE.md` módosítás akkor tekinthető megfelelőnek, ha:

- az STL-import már nem jelenik meg kizárólagos modellforrásként;
- a `MeshSource → Mesh` kapcsolat hivatalosan megjelenik;
- az STL-import konkrét MeshSource-ként értelmezhető;
- az opcionális pluginok helye egyértelmű;
- a core/plugin határ összhangban van az ADR-rel;
- a downstream pipeline változatlansága egyértelmű;
- a Project továbbra is koordinációs réteg;
- nem kerülnek bele még nem eldöntött implementációs részletek;
- nincs szükségtelen átszervezés az Architecture dokumentumban.

---

# 10. Javasolt végállapot

Az architektúra lényegi modellje:

```text
                     SliceDesigner
                          │
                    ┌─────▼─────┐
                    │  Project  │
                    └─────┬─────┘
                          │
                    MeshSource
                    /    |     \\
                   /     |      \\
             STL Source Relief   ...
                   \\     |      /
                    \\    |     /
                     └───▼─────┘
                         Mesh
                          │
                    ┌─────▼─────┐
                    │   Slice   │
                    └─────┬─────┘
                          │
                    további pipeline
```

Ez az `ARCHITECTURE.md` módosításának **célállapota**, nem új implementációs terv.

---

## Kapcsolódó döntések

- `docs/MESH_SOURCE.md` — elfogadott tervezet
- `docs/adr/ADR_MESH_SOURCE.md` — elfogadott ADR
- Jelen dokumentum — az `ARCHITECTURE.md` módosításának terve

## Státusz

**Tervezet — jóváhagyásra vár.**

Az `ARCHITECTURE.md` tényleges tartalmát a jelen terv elfogadása után kell módosítani.
