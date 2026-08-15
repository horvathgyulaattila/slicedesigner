# Domain Model

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-01
Utolsó módosítás: 2026-08-15
Kapcsolódó dokumentumok: [PROJECT_CONSTITUTION.md](PROJECT_CONSTITUTION.md), [ROADMAP.md](ROADMAP.md), [PROJECT_VISION.md](PROJECT_VISION.md)

## A dokumentum célja

Ez a dokumentum definiálja a Slice Designer projekt közös fogalomrendszerét (Ubiquitous Language). Minden későbbi specifikáció, architekturális döntés és implementáció ezekre a fogalmakra épül, hogy a projekt minden résztvevője ugyanazt értse ugyanazon fogalmak alatt.

> **Megjegyzés (2026-08-01):** A Numbering fogalom kivételesen, a Phase 1 hivatalos megkezdése előtt került rögzítésre, mert a ROADMAP Phase 2 (Functional Specifications) listája már hivatkozott rá, miközben a Domain Model nem tartalmazta — ez dokumentáción belüli ellentmondást okozott. A kiegészítés a projektgazda jóváhagyásával, kizárólag erre a fogalomra korlátozva történt; a Phase 1 további tartalma (koordinátarendszer, mértékegységek stb.) változatlanul a Phase 1 hivatalos megkezdésére vár.
>
> **Megjegyzés (2026-08-01, folytatás 2):** A Phase 1 hátralévő tartalma — koordinátarendszer, mértékegységek, valamint mind a 14 fogalom attribútum-szintű (felsorolás szintű) kiegészítése — a projektgazdával közösen kidolgozásra és jóváhagyásra került. Ezzel a Phase 1 ROADMAP.md-ben rögzített feladatlistája tartalmilag lezárult; a formális ROADMAP-státusz frissítése a Claude Code általi végrehajtás és a projektgazdai review után történik (AI_WORKFLOW.md 4. szakasz).

## Alapelvek

* A dokumentum technológiafüggetlen.
* A dokumentum nem implementáció.
* A fogalmak hosszú távon stabilak.
* A projekt minden része ezeket a definíciókat használja.

## Koordinátarendszer

A Slice Designer jobbsodrású (right-handed), derékszögű 3D koordinátarendszert használ.

A szeletelési tengely (amely mentén a Slice Engine a Mesh keresztmetszeteit előállítja) paraméterezhető — az alapértelmezett tengely a Z, felülírható (Engineering Principles, paraméterezhetőség: nincs rejtett, hardkódolt tengelyválasztás).

Az origó helyét a rendszer nem kényszeríti a betöltött Mesh-re: a Mesh Import a modell saját, forrásfájlbeli koordinátáit őrzi meg, automatikus, csendes újra-origózás nélkül (fail-fast elv — ha origó-igazítás szükséges, azt explicit, dokumentált paraméter vezérli, nem hallgatólagos alapértelmezés).

## Mértékegységek

A Slice Designer minden hosszúság jellegű értéket **milliméterben (mm)** kezel, egységesen a teljes rendszerben — Mesh geometria, Gap, Material méretei, Slice vastagsága egyaránt.

Nincs beépített egységváltás vagy -választás: a rendszer nem tesz feltételezést az STL fájl mértékegységéről, azt milliméterként értelmezi (Engineering Principles, fail-fast: ha ez a feltételezés a betöltött Mesh méretei alapján irreálisnak tűnik, azt a Mesh Import réteg feladata jelezni, nem a Domain Model kérdése).

Szög jellegű értékek **fokban (°)** értendők, hacsak egy adott specifikáció explicit módon mást nem rögzít.

## Fogalmak

Minden fogalom azonos szerkezetben szerepel: Definíció, Szerepe, Attribútumok (felsorolás szinten), Kapcsolódó fogalmak.

### Project

**Definíció:** A felhasználó teljes munkafolyamata és annak menthető állapota.

**Szerepe:** Egyben tartja a munkafolyamat során létrejövő összes adatot és beállítást.

**Attribútumok (felsorolás szinten):** Mesh-referencia, mentési útvonal, létrehozás/módosítás időpontja, aktuális paraméter-állapot, összeépítési kapcsolók (Spacer/Dowel/Backplate engedélyezettsége).

**Kapcsolódó fogalmak:** Mesh, Assembly, Export

---

### Mesh

**Definíció:** A SliceDesigner által feldolgozandó háromdimenziós geometria domain reprezentációja, függetlenül attól, hogy importból vagy generálásból származik.

**Szerepe:** A szeletelési folyamat kiindulási alapja.

**Attribútumok (felsorolás szinten):** geometriai reprezentáció jellege (pl. háromszögháló), opcionális forrásfájl-hivatkozás (fájlból importált Mesh esetén a forrásfájl elérési útja; generált Mesh esetén nincs forrásfájl), méret/bounding box, validáltsági állapot.

**Kapcsolódó fogalmak:** Project, Slice Set

---

### Slice

**Definíció:** A modellből létrehozott egyetlen szelet.

**Szerepe:** A gyártásra kerülő alkatrészek alapegysége.

**Attribútumok (felsorolás szinten):** vastagság, geometria típusa, pozíció a szeletelési tengely mentén, sorszám a Slice Set-en belül.

**Kapcsolódó fogalmak:** Slice Set, Sziget, Material, Dowel Hole, Backplate, Numbering

---

### Sziget

**Definíció:** Egy Slice-on belüli, a Slice többi részétől geometriailag különálló, önmagában összefüggő anyagrész.

**Szerepe:** A ténylegesen különálló, gyártás után önálló fizikai darabként kezelendő egység — minden csap-, Dowel-, Spacer- és számozás-elhelyezési szabály erre, nem a teljes Slice-ra vonatkozik.

**Attribútumok (felsorolás szinten):** azonosító (a szelet sorszáma + saját betűjele), geometria (zárt kontúr(ok), a szülő Slice geometriájának egy összefüggő része).

**Kapcsolódó fogalmak:** Slice, Dowel Hole, Backplate, Numbering

---

### Slice Set

**Definíció:** Egy modellhez tartozó szeletek összessége.

**Szerepe:** A Mesh-ből származó szeletek egységes csoportja.

**Attribútumok (felsorolás szinten):** forrás Mesh-referencia, Gap-referencia (amivel készült), szeletek listája/sorrendje, szeletek száma (darabszám).

**Kapcsolódó fogalmak:** Mesh, Slice, Gap

---

### Gap

**Definíció:** A szeletek közötti tervezett távolság.

**Szerepe:** Meghatározza a szeletek egymáshoz viszonyított elhelyezését.

**Attribútumok (felsorolás szinten):** érték (a távolság mértéke), egységesség (fix vagy szeletpáronként eltérő-e), kapcsolódó Slice Set referencia.

**Kapcsolódó fogalmak:** Slice Set, Spacer

---

### Spacer

**Definíció:** A Gap fizikai biztosítására szolgáló elem.

**Szerepe:** Fenntartja a szeletek között tervezett távolságot.

**Attribútumok (felsorolás szinten):** geometriai forma, vastagság, darabszám Gap-enként, a rajta átmenő Dowel átmérőjével megegyező furat (kizárólag a Dowel-re fűzött Spacer-eknél).

**Kapcsolódó fogalmak:** Gap, Slice, Dowel

---

### Backplate

**Definíció:** A szeletek pozicionálását segítő hordozóelem.

**Szerepe:** Rögzített referenciát biztosít a szeletek elhelyezéséhez.

**Attribútumok (felsorolás szinten):** méret/geometria, vastagság, anyag-hozzárendelés.

**Kapcsolódó fogalmak:** Slice, Assembly, Numbering

---

### Numbering

**Definíció:** A szeletek egyedi azonosítóval történő megjelölése, amely mind a szelet geometriájába bevésve/kivágva, mind a hozzá tartozó Backplate pozíción megjelenik.

**Szerepe:** Biztosítja a szeletek és a Backplate pozíciók egyértelmű megfeleltetését, lehetővé téve a hibamentes összeszerelést.

**Attribútumok (felsorolás szinten):** azonosító formátuma, elhelyezés a szeleten, elhelyezés a Backplate-en.

**Kapcsolódó fogalmak:** Slice, Backplate

---

### Dowel

**Definíció:** A szeletek pontos illesztését biztosító alkatrész.

**Szerepe:** Biztosítja a szeletek egymáshoz viszonyított pontos, ismételhető illeszkedését.

**Attribútumok (felsorolás szinten):** átmérő, hossz, anyag/típus.

**Kapcsolódó fogalmak:** Dowel Hole, Slice

---

### Dowel Hole

**Definíció:** A Dowel befogadására szolgáló furat.

**Szerepe:** Lehetővé teszi a Dowel általi illesztést.

**Attribútumok (felsorolás szinten):** átmérő, mélység, pozíció a Slice-on.

**Kapcsolódó fogalmak:** Dowel, Slice

---

### Material

**Definíció:** Az a lemez vagy alapanyag, amelyből az alkatrészek készülnek.

**Szerepe:** A Nest és a gyártás alapjául szolgáló fizikai erőforrás.

**Attribútumok (felsorolás szinten):** kategorizálás/típus, vastagság, lemezméret, kerf (vágási rés).

**Kapcsolódó fogalmak:** Nest, Slice

---

### Nest

**Definíció:** Az alkatrészek optimális elrendezése egy vagy több alapanyagon.

**Szerepe:** Meghatározza az alkatrészek helyét a gyártáshoz felhasznált Material-okon.

**Attribútumok (felsorolás szinten):** kapcsolódó Material-referencia, elrendezett elemek listája, elrendezési paraméterek.

**Kapcsolódó fogalmak:** Material, Slice, Export

---

### Assembly

**Definíció:** A kész termék összes alkatrészének együttese.

**Szerepe:** A Project végeredményeként létrejövő, összeépítendő alkatrészhalmaz.

**Attribútumok (felsorolás szinten):** összetevők listája (Slice, Backplate, Spacer, Dowel), szerkezet típusa (lapos lista vs. hierarchikus).

**Kapcsolódó fogalmak:** Slice, Backplate, Project

---

### Export

**Definíció:** A gyártásra előkészített eredmény (például DXF).

**Szerepe:** A Nest alapján előállított, gyártásra alkalmas kimenet.

**Attribútumok (felsorolás szinten):** fájlformátum/verzió (pl. DXF verzió), réteg-/layer-struktúra, kapcsolódó Nest-referencia.

**Kapcsolódó fogalmak:** Nest, Project

## Fogalmi kapcsolatok

* Egy Project egy Mesh-t tartalmaz.
* Egy Mesh-ből Slice Set készül.
* A Slice Set Slice elemekből áll.
* Egy Slice egy vagy több Szigetből áll; több Sziget esetén azok egymástól fizikailag különálló darabok.
* Egy Slice Set szeleteinek összvastagsága és a közöttük lévő Gap-ek együttesen adják ki a forrás Mesh szeletelési tengely menti méretét — az összeállított modell mérete megegyezik az eredeti Mesh méretével.
* A Slice-eket egy Backplate pozicionálhatja.
* A Dowel és Dowel Hole együtt biztosítja az illesztést.
* A Spacer pozíciója a Dowel pozíciójához igazodik, ahol lehetséges — a Dowel az elsődleges illesztési mechanizmus, a Spacer erre épül.
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
