# Backplate — Specifikáció

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-01
Utolsó módosítás: 2026-08-01
Kapcsolódó dokumentumok: [PROJECT_CONSTITUTION.md](../PROJECT_CONSTITUTION.md), [ARCHITECTURE.md](../ARCHITECTURE.md), [DOMAIN_MODEL.md](../DOMAIN_MODEL.md), [SPECIFICATION_STANDARD.md](../SPECIFICATION_STANDARD.md), [ENGINEERING_PRINCIPLES.md](../ENGINEERING_PRINCIPLES.md), [ADR-0004](../adr/0004-optional-assembly-mechanisms.md), [ADR-0005](../adr/0005-dowel-before-gap-ordering.md), [GAP_SYSTEM_SPEC.md](GAP_SYSTEM_SPEC.md), [DOWEL_SYSTEM_SPEC.md](DOWEL_SYSTEM_SPEC.md)

## 1. Kontextus

A Backplate Engine a pipeline ötödik lépése (ARCHITECTURE.md 3. szakasz, a Gap Engine után). Bemenete a pipeline addig lefutott lépéseinek eredménye (Slice Set — a ténylegesen megelőző engine-től függően: Gap, Dowel, vagy közvetlenül Slice Engine, az ADR-0004 kapcsolók szerint). A Backplate Engine előállítja a Backplate geometriáját, és minden, a Backplate-hez ténylegesen kapcsolódó sziget minden érintkező szakaszához hozzáadja a rögzítő csapokat, a Backplate-en pedig a hozzájuk tartozó fészkeket alakítja ki. Egyes szigetek szándékosan kizárhatók a Backplate-kapcsolódásból (`non_backplate_islands`).

## 2. Felelősség

ARCHITECTURE.md-ből átvéve, nem bővítve: a Backplate geometriájának előállítása, és a szeletek Backplate-hez viszonyított pozicionálása — csap/fészek mechanizmussal megvalósítva, szigetenként és érintkező szakaszonként.

## 3. Bemenet

| Attribútum | Típus | Kötelező |
|---|---|---|
| Slice Set | a pipeline addig lefutott lépéseinek kimenete | igen |
| `backplate_normal_axis` | enum (a `slice_axis`-tól eltérő két tengely egyike, előjellel, pl. `{+X,-X,+Y,-Y}`) | igen |
| `backplate_thickness_mm` | szám, mm | igen |
| `backplate_plane_tolerance_mm` | szám, mm | nem (alapérték: `0.1`) |
| `backplate_margin_mm` | előjeles szám, mm | nem (alapérték: `0`) |
| `tab_length_mm` | szám, mm | igen |
| `tab_spacing_mm` | szám, mm | nem (alapérték: `700`) |
| `tab_edge_margin_mm` | szám, mm | nem (alapérték: `= tab_length_mm`) |
| `slice_tab_overrides` | lista `{szelet sorszáma, sziget azonosító (opcionális, ha a szelet egyetlen szigetből áll, elhagyható), tab_length_mm?, tab_spacing_mm?, tab_edge_margin_mm?, manual_tab_positions?}` | nem (alapérték: üres lista) |
| `non_backplate_islands` | lista `{szelet sorszáma, sziget azonosító}` | nem (alapérték: üres lista) |
| `material_reference` | szöveges hivatkozás | nem |

## 4. Kimenet

**Módosított Slice Set** — minden, a Backplate-hez ténylegesen kapcsolódó sziget (azaz a `non_backplate_islands`-ben nem szereplő) minden Backplate felé néző érintkező szakaszán kiegészítve a csap-protrúzió(k) geometriájával (szélesség = szeletvastagság, mélység = `backplate_thickness_mm`, hossz(ok) a 6. szakasz szabálya szerint).

**Backplate objektum:**

| Attribútum | Típus | Mértékegység |
|---|---|---|
| geometria | a Slice Set `backplate_normal_axis` irányú sziluettje (minden szigetet figyelembe véve, a `non_backplate_islands`-ben szereplőket is), `backplate_margin_mm`-mel eltolva, a hozzá tartozó fészek-kivágásokkal | mm |
| vastagság | `= backplate_thickness_mm` | mm |
| anyag-hozzárendelés | `material_reference` (ha megadva) | — |

## 5. Paraméterek

| Név | Alapérték | Érvényességi tartomány | Jelentés |
|---|---|---|---|
| `backplate_normal_axis` | nincs (kötelező) | a `slice_axis`-tól eltérő 2 tengely egyike, előjellel | A Backplate felé néző irány. |
| `backplate_thickness_mm` | nincs (kötelező) | `> 0` | A Backplate saját vastagsága — egyben a csapok mélysége is. |
| `backplate_plane_tolerance_mm` | `0.1` | `≥ 0` | A Backplate-hez kapcsolódó szigetek érintkező szakaszainak szélső koordinátái közötti megengedett síkeltérés. |
| `backplate_margin_mm` | `0` | előjeles | A sziluett-kontúr eltolása (pozitív: kifelé, negatív: befelé). |
| `tab_length_mm` | nincs (kötelező) | `> 0` | Csap alapértelmezett hossza egy érintkező szakasz mentén. |
| `tab_spacing_mm` | `700` | `> 0` | Célzott csap-köz. |
| `tab_edge_margin_mm` | `= tab_length_mm` | `> 0` | A csap kezdete az érintkező szakasz végétől. |
| `slice_tab_overrides` | üres lista | — | Szigetenkénti (szelet sorszám + sziget azonosító alapján) paraméter- vagy pozíció-felülbírálás, az adott sziget összes érintkező szakaszára alkalmazva. |
| `non_backplate_islands` | üres lista | — | Azok a szigetek (szelet sorszám + sziget azonosító), amelyek szándékosan nem érnek a Backplate közös síkjáig — ezekre nem vonatkozik a közös sík megkövetelése és a csap-elhelyezés. |
| `material_reference` | nincs | — | Opcionális anyag-hivatkozás. |

## 6. Viselkedés

1. Minden szelet minden szigetének azonosítása; a `non_backplate_islands`-ben szereplők kizárása a további lépésekből (2–8. lépés) — ezek nem kapnak csapot, nem vesznek részt a közös sík ellenőrzésében.
2. A megmaradó szigetek mindegyikénél: a Backplate felé néző, egymással összefüggő érintkező szakasz(ok) azonosítása a sziget kontúrján — egy szigetnek egy vagy több ilyen szakasza is lehet (pl. alávágott geometria esetén).
3. Az összes azonosított érintkező szakasz szélső koordinátája közötti eltérés ellenőrzése: ha bármelyik kettő között `backplate_plane_tolerance_mm`-nél nagyobb az eltérés → hiba (7. szakasz).
4. A Backplate sík pozíciójának rögzítése a validált közös koordinátán.
5. Minden érintkező szakaszhoz (a `slice_tab_overrides` szerint, a szakaszt tartalmazó sziget szelet sorszáma + sziget azonosítója alapján esetlegesen felülírt paraméterekkel): `usable_length` = a szakasz hossza − `2 × tab_edge_margin_mm`. Ha `≤ 0` → hiba.
6. Ha van `manual_tab_positions` az adott szigethez, és azok az adott szakaszra esnek → azok validálása és felhasználása (a margókat és az egymást átfedő csapokra vonatkozó összeolvadási szabályt itt is alkalmazva).
7. Egyébként: csapok elhelyezése az adott szakaszon `tab_spacing_mm` célközzel, `tab_length_mm` hosszal, a margók között egyenletesen elosztva; egymást átfedő csapok egyetlen, hosszabb csappá olvasztása.
8. Minden csap hozzáadása az adott sziget geometriájához (protrúzióként, szélesség = szeletvastagság, mélység = `backplate_thickness_mm`).
9. A teljes Slice Set `backplate_normal_axis` irányú sziluettjének meghatározása (beleértve az esetleges belső lyukakat/megszakításokat) — ez minden szigetet figyelembe vesz, a `non_backplate_islands`-ben szereplőket is.
10. A sziluett kontúrjának eltolása `backplate_margin_mm`-mel.
11. A csapoknak megfelelő fészek-kivágások kialakítása a Backplate geometriájában, érintkező szakaszonként, a megfelelő pozíciókban.
12. A módosított Slice Set és a Backplate objektum összeállítása és visszaadása a Project felé.

## 7. Hibakezelés

Fail-fast elven:

* Egy, a `non_backplate_islands`-ben nem szereplő sziget egyáltalán nem éri el a Backplate síkját (nincs érintkező szakasza) → **hiba**.
* A Backplate-hez kapcsolódó szigetek érintkező szakaszainak szélső koordinátái nem esnek egy közös síkba (`backplate_plane_tolerance_mm`-en túl) → **hiba**.
* Érvénytelen (`≤ 0`) `backplate_thickness_mm`, `tab_length_mm`, vagy `tab_spacing_mm` → **hiba**.
* Érvénytelen (`≤ 0`) `tab_edge_margin_mm` → **hiba**.
* Egy érintkező szakaszon `usable_length ≤ 0` → **hiba**.
* Egy manuálisan megadott csap-pozíció nem fér el a megadott helyen → **hiba**.
* Érvénytelen `backplate_normal_axis` (megegyezik a `slice_axis`-szal, vagy nem létező tengely) → **hiba**.

## 8. Kapcsolódó engine-ek és Domain Model fogalmak

* **Gap Engine / Dowel Engine / Slice Engine** — a bemeneti Slice Set forrása (attól függően, melyik futott le utoljára).
* **Numbering Engine** — a Backplate Engine kimenetét fogadja majd (a pipeline következő lépése).
* Domain Model: Backplate, Slice, Sziget, Assembly.
* **Megjegyzés:** a `non_backplate_islands`-ben szereplő szigetek a Dowel Engine és a Gap Engine szempontjából nem különböznek a többi szigettől — azok az engine-ek kizárólag geometriai átfedés alapján dolgoznak, a Backplate-kapcsolódástól függetlenül, és korábban futnak le a pipeline-ban (ADR-0005), így nem is ismerhetik ezt a listát.

## 9. Nyitott kérdések

Nincs megválaszolatlan pont.

## 10. Elfogadási kritériumok

* A specifikáció mind a 10 szakaszt hiánytalanul tartalmazza.
* A csap/fészek mechanizmus (méret, pozicionálás, összeolvadási szabály, szigetenkénti felülbírálás) egyértelműen rögzített.
* A csap-elhelyezés bizonyíthatóan érintkező szakaszonként (nem szigetenként összesítve) történik, kezelve az alávágott geometriájú szigeteket is.
* A `non_backplate_islands` explicit kizárási mechanizmusa egyértelműen rögzített, és nem befolyásolja a Dowel/Gap Engine működését.
* A Backplate alakja a sziluett-alapú szabály szerint, margóval együtt definiált.
* A közös sík megkövetelése és tűréshatára rögzített.
* A Hibakezelés fail-fast elven, egyértelműen felsorolja a blokkoló eseteket.
