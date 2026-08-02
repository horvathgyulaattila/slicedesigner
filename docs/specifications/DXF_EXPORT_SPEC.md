# DXF Export — Specifikáció

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-01
Utolsó módosítás: 2026-08-01
Kapcsolódó dokumentumok: [PROJECT_CONSTITUTION.md](../PROJECT_CONSTITUTION.md), [ARCHITECTURE.md](../ARCHITECTURE.md), [DOMAIN_MODEL.md](../DOMAIN_MODEL.md), [SPECIFICATION_STANDARD.md](../SPECIFICATION_STANDARD.md), [ENGINEERING_PRINCIPLES.md](../ENGINEERING_PRINCIPLES.md), [NESTING_SPEC.md](NESTING_SPEC.md)

## 1. Kontextus

A DXF Export Engine a pipeline nyolcadik, utolsó lépése, a Nesting Engine után. Bemenete a Nest-ek listája (anyagonként, laponként elrendezett alkatrészekkel, beleértve a toldott alkatrészek darabonkénti al-azonosítóit is). Minden anyaglaphoz külön DXF fájlt állít elő, két réteggel (vágás, gravírozás).

## 2. Felelősség

ARCHITECTURE.md-ből átvéve, nem bővítve: a Nest alapján gyártásra kész Export (DXF) kimenet előállítása.

## 3. Bemenet

| Attribútum | Típus | Kötelező |
|---|---|---|
| Nest-ek listája | Nesting Engine kimenete | igen |
| `dxf_version` | szöveges/enum (pl. `"R12"`) | nem (alapérték: `"R12"`, a legszélesebb körben kompatibilis verzió) |
| `cut_layer_name` | szöveg | nem (alapérték: `"CUT"`) |
| `cut_layer_color` | szín (AutoCAD Color Index) | nem (alapérték: piros) |
| `engrave_layer_name` | szöveg | nem (alapérték: `"ENGRAVE"`) |
| `engrave_layer_color` | szín (AutoCAD Color Index) | nem (alapérték: kék) |
| `output_filename_pattern` | szöveges minta | nem (alapérték: `"{material_id}_sheet{sheet_number}"`) |

## 4. Kimenet

**Export objektumok listája** — anyaglaponként egy Export:

| Attribútum | Típus |
|---|---|
| fájlformátum/verzió | `dxf_version` |
| réteg-/layer-struktúra | `[cut_layer_name, engrave_layer_name]` |
| kapcsolódó Nest-referencia | hivatkozás a forrás Nest-re és lapra |
| fájlnév | `output_filename_pattern` alapján |

## 5. Paraméterek

| Név | Alapérték | Jelentés |
|---|---|---|
| `dxf_version` | `"R12"` | A generált DXF fájlok formátumverziója. |
| `cut_layer_name` | `"CUT"` | A vágási réteg neve. |
| `cut_layer_color` | piros | A vágási réteg színe (ACI). |
| `engrave_layer_name` | `"ENGRAVE"` | A gravírozási réteg neve. |
| `engrave_layer_color` | kék | A gravírozási réteg színe (ACI). |
| `output_filename_pattern` | `"{material_id}_sheet{sheet_number}"` | A fájlnév-generálási minta. |

## 6. Viselkedés

1. Minden Nest minden lapjához új DXF dokumentum létrehozása (`dxf_version` szerint, mm mértékegységgel).
2. A `cut_layer_name`/`cut_layer_color` és `engrave_layer_name`/`engrave_layer_color` rétegek létrehozása a dokumentumban.
3. Az adott lapra elrendezett minden alkatrész vágási geometriájának (külső kontúr, lyukak, csap/fészek-kivágás, Dowel Hole, toldási varratvonal) rajzolása a CUT rétegre, a Nesting Engine által meghatározott pozícióban és forgatásban.
4. Az adott lapon szereplő alkatrészek Numbering-azonosítóinak, valamint a toldott darabok al-azonosítóinak rajzolása az ENGRAVE rétegre, ugyanabban a pozícióban/forgatásban.
5. A DXF fájl mentése az `output_filename_pattern` szerint generált néven.
6. Az Export objektumok listájának összeállítása és visszaadása a Project felé.

## 7. Hibakezelés

Fail-fast elven:

* Érvénytelen/nem támogatott `dxf_version` → **hiba**.
* Üres Nest-lista (nincs mit exportálni) → **hiba**.
* Az `output_filename_pattern` alapján két lap azonos fájlnevet kapna → **hiba**.

## 8. Kapcsolódó engine-ek és Domain Model fogalmak

* **Nesting Engine** — a bemeneti Nest-ek forrása.
* Domain Model: Nest, Export.

## 9. Nyitott kérdések

Nincs megválaszolatlan pont.

## 10. Elfogadási kritériumok

* A specifikáció mind a 10 szakaszt hiánytalanul tartalmazza.
* A réteg-struktúra (CUT, ENGRAVE — név és szín is paraméterezhető) egyértelműen rögzített.
* A lapok szerinti fájlszervezés (egy lap = egy fájl) rögzített.
* Az ENGRAVE réteg tartalmazza mind a fő Numbering-azonosítókat, mind a toldott darabok al-azonosítóit.
* A Hibakezelés fail-fast elven, egyértelműen felsorolja a blokkoló eseteket.
