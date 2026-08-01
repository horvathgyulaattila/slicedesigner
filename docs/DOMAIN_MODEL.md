# Domain Model

Státusz: Piszkozat
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-01
Utolsó módosítás: 2026-08-01
Kapcsolódó dokumentumok: [PROJECT_CONSTITUTION.md](PROJECT_CONSTITUTION.md), [ROADMAP.md](ROADMAP.md), [PROJECT_VISION.md](PROJECT_VISION.md)

## A dokumentum célja

Ez a dokumentum definiálja a Slice Designer projekt közös fogalomrendszerét (Ubiquitous Language). Minden későbbi specifikáció, architekturális döntés és implementáció ezekre a fogalmakra épül, hogy a projekt minden résztvevője ugyanazt értse ugyanazon fogalmak alatt.

> **Megjegyzés (2026-08-01):** A Numbering fogalom kivételesen, a Phase 1 hivatalos megkezdése előtt került rögzítésre, mert a ROADMAP Phase 2 (Functional Specifications) listája már hivatkozott rá, miközben a Domain Model nem tartalmazta — ez dokumentáción belüli ellentmondást okozott. A kiegészítés a projektgazda jóváhagyásával, kizárólag erre a fogalomra korlátozva történt; a Phase 1 további tartalma (koordinátarendszer, mértékegységek stb.) változatlanul a Phase 1 hivatalos megkezdésére vár.

## Alapelvek

* A dokumentum technológiafüggetlen.
* A dokumentum nem implementáció.
* A fogalmak hosszú távon stabilak.
* A projekt minden része ezeket a definíciókat használja.

## Fogalmak

Minden fogalom azonos szerkezetben szerepel: Definíció, Szerepe, Kapcsolódó fogalmak.

### Project

**Definíció:** A felhasználó teljes munkafolyamata és annak menthető állapota.

**Szerepe:** Egyben tartja a munkafolyamat során létrejövő összes adatot és beállítást.

**Kapcsolódó fogalmak:** Mesh, Assembly, Export

---

### Mesh

**Definíció:** A felhasználó által importált háromdimenziós modell.

**Szerepe:** A szeletelési folyamat kiindulási alapja.

**Kapcsolódó fogalmak:** Project, Slice Set

---

### Slice

**Definíció:** A modellből létrehozott egyetlen szelet.

**Szerepe:** A gyártásra kerülő alkatrészek alapegysége.

**Kapcsolódó fogalmak:** Slice Set, Material, Dowel Hole, Backplate, Numbering

---

### Slice Set

**Definíció:** Egy modellhez tartozó szeletek összessége.

**Szerepe:** A Mesh-ből származó szeletek egységes csoportja.

**Kapcsolódó fogalmak:** Mesh, Slice, Gap

---

### Gap

**Definíció:** A szeletek közötti tervezett távolság.

**Szerepe:** Meghatározza a szeletek egymáshoz viszonyított elhelyezését.

**Kapcsolódó fogalmak:** Slice Set, Spacer

---

### Spacer

**Definíció:** A Gap fizikai biztosítására szolgáló elem.

**Szerepe:** Fenntartja a szeletek között tervezett távolságot.

**Kapcsolódó fogalmak:** Gap, Slice

---

### Backplate

**Definíció:** A szeletek pozicionálását segítő hordozóelem.

**Szerepe:** Rögzített referenciát biztosít a szeletek elhelyezéséhez.

**Kapcsolódó fogalmak:** Slice, Assembly, Numbering

---

### Numbering

**Definíció:** A szeletek egyedi azonosítóval történő megjelölése, amely mind a szelet geometriájába bevésve/kivágva, mind a hozzá tartozó Backplate pozíción megjelenik.

**Szerepe:** Biztosítja a szeletek és a Backplate pozíciók egyértelmű megfeleltetését, lehetővé téve a hibamentes összeszerelést.

**Kapcsolódó fogalmak:** Slice, Backplate

---

### Dowel

**Definíció:** A szeletek pontos illesztését biztosító alkatrész.

**Szerepe:** Biztosítja a szeletek egymáshoz viszonyított pontos, ismételhető illeszkedését.

**Kapcsolódó fogalmak:** Dowel Hole, Slice

---

### Dowel Hole

**Definíció:** A Dowel befogadására szolgáló furat.

**Szerepe:** Lehetővé teszi a Dowel általi illesztést.

**Kapcsolódó fogalmak:** Dowel, Slice

---

### Material

**Definíció:** Az a lemez vagy alapanyag, amelyből az alkatrészek készülnek.

**Szerepe:** A Nest és a gyártás alapjául szolgáló fizikai erőforrás.

**Kapcsolódó fogalmak:** Nest, Slice

---

### Nest

**Definíció:** Az alkatrészek optimális elrendezése egy vagy több alapanyagon.

**Szerepe:** Meghatározza az alkatrészek helyét a gyártáshoz felhasznált Material-okon.

**Kapcsolódó fogalmak:** Material, Slice, Export

---

### Assembly

**Definíció:** A kész termék összes alkatrészének együttese.

**Szerepe:** A Project végeredményeként létrejövő, összeépítendő alkatrészhalmaz.

**Kapcsolódó fogalmak:** Slice, Backplate, Project

---

### Export

**Definíció:** A gyártásra előkészített eredmény (például DXF).

**Szerepe:** A Nest alapján előállított, gyártásra alkalmas kimenet.

**Kapcsolódó fogalmak:** Nest, Project

## Fogalmi kapcsolatok

* Egy Project egy Mesh-t tartalmaz.
* Egy Mesh-ből Slice Set készül.
* A Slice Set Slice elemekből áll.
* A Slice-eket egy Backplate pozicionálhatja.
* A Dowel és Dowel Hole együtt biztosítja az illesztést.
* A Nest az alkatrészek Material-okra történő elrendezése.
* Az Export a teljes előkészített eredmény.
* A Numbering minden Slice-hoz egyedi azonosítót rendel, és ezt a hozzá tartozó Backplate pozíción is megjeleníti.

## A dokumentum határai

Ez a dokumentum nem definiálja:

* az algoritmusokat;
* a geometriai számításokat;
* a GUI működését;
* a fájlformátumokat;
* az implementációt.
