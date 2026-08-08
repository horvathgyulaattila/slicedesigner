# Backplate — Specifikáció

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-01
Utolsó módosítás: 2026-08-07
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
| geometria | a domináns közös sík (6. szakasz 3–5. pont) körüli, `backplate_plane_tolerance_mm` vastagságú sávban a Mesh tényleges geometriájából (térbeli metszettel) kimetszett és a (harmadik tengely, szelet-tengely) síkra vetített kontúr, `backplate_margin_mm`-mel eltolva, a hozzá tartozó fészek-kivágásokkal | mm |
| vastagság | `= backplate_thickness_mm` | mm |
| közös sík világkoordinátája | a domináns közös sík (6. szakasz 3–5. pont) tényleges world-koordinátája `backplate_normal_axis` mentén — a Backplate belső (az összeállítás felé néző) síkjának pozíciója | mm |
| anyag-hozzárendelés | `material_reference` (ha megadva) | — |

## 5. Paraméterek

| Név | Alapérték | Érvényességi tartomány | Jelentés |
|---|---|---|---|
| `backplate_normal_axis` | nincs (kötelező) | a `slice_axis`-tól eltérő 2 tengely egyike, előjellel | A Backplate felé néző irány. |
| `backplate_thickness_mm` | nincs (kötelező) | `> 0` | A Backplate saját vastagsága — egyben a csapok mélysége is. |
| `backplate_plane_tolerance_mm` | `0.1` | `≥ 0` | A közös Backplate-sík automatikus felismerésekor (6. szakasz 3. pont) használt klaszterezési küszöb: egymást követő érintkező-szakasz szélsőértékek között megengedett legnagyobb eltérés ugyanabban a csoportban. |
| `backplate_margin_mm` | `0` | előjeles | A sziluett-kontúr eltolása (pozitív: kifelé, negatív: befelé). |
| `tab_length_mm` | nincs (kötelező) | `> 0` | Csap alapértelmezett hossza egy érintkező szakasz mentén. |
| `tab_spacing_mm` | `700` | `> 0` | Célzott csap-köz. |
| `tab_edge_margin_mm` | `= tab_length_mm` | `> 0` | A csap kezdete az érintkező szakasz végétől. |
| `slice_tab_overrides` | üres lista | — | Szigetenkénti (szelet sorszám + sziget azonosító alapján) paraméter- vagy pozíció-felülbírálás, az adott sziget összes érintkező szakaszára alkalmazva. |
| `non_backplate_islands` | üres lista | — | Azok a szigetek (szelet sorszám + sziget azonosító), amelyek kézzel, explicit kizárandók a Backplate-kapcsolódásból — kiegészítésképp azokhoz képest, amelyeket a rendszer a 6. szakasz 3–4. pontja szerint már automatikusan felismer és kizár. |
| `material_reference` | nincs | — | Opcionális anyag-hivatkozás. |

## 6. Viselkedés

1. Minden szelet minden szigetének azonosítása; a `non_backplate_islands`-ben szereplők kizárása a további lépésekből (2–9. lépés) — ezek nem kapnak csapot, nem vesznek részt a közös sík felismerésében.
2. A megmaradó szigetek mindegyikénél: a Backplate felé néző, egymással összefüggő érintkező szakasz(ok) azonosítása a sziget kontúrján — egy szigetnek egy vagy több ilyen szakasza is lehet (pl. alávágott geometria esetén).
3. Az összes azonosított érintkező szakasz szélsőértékének növekvő sorrendbe rendezése, majd lánc-alapú csoportosítása: egymást követő (rendezett) értékek egy csoportba kerülnek, ha köztük legfeljebb `backplate_plane_tolerance_mm` az eltérés. A legnagyobb (legtöbb szakaszt tartalmazó) csoport a domináns közös sík. Ha a domináns csoport nem tartalmazza a szakaszok szigorú többségét (> 50%) → hiba (7. szakasz).
4. A domináns csoporton kívül eső szakaszú szigetek automatikusan úgy kezelendők, mintha a `non_backplate_islands`-ben szerepelnének (nem kapnak csapot, nem vesznek részt a további lépésekben) — figyelmeztetés rögzítése, a szelet sorszámára és a sziget azonosítójára hivatkozva. Ez nem hiba.
5. A Backplate sík pozíciójának rögzítése a domináns csoport szélsőértékén (`common_plane_mm`).
6. Minden, a domináns csoportba eső érintkező szakaszhoz (a `slice_tab_overrides` szerint, a szakaszt tartalmazó sziget szelet sorszáma + sziget azonosítója alapján esetlegesen felülírt paraméterekkel): `usable_length` = a szakasz hossza − `2 × tab_edge_margin_mm`. Ha `≤ 0`, az adott szakaszon nem kerül csap elhelyezésre — figyelmeztetés rögzítése, a szelet sorszámára, a sziget azonosítójára és a hiányzó hely mértékére hivatkozva. Ez nem hiba; a sziget más érintkező szakaszain (ha van neki) a csap-elhelyezés változatlanul folytatódik — akár egy sziget összes szakaszára vonatkozóan is előfordulhat, ekkor a sziget sehol nem kap csapot, de a geometriája változatlan marad.
7. Ha van `manual_tab_positions` az adott szigethez, és azok az adott szakaszra esnek → azok validálása és felhasználása (a margókat és az egymást átfedő csapokra vonatkozó összeolvadási szabályt itt is alkalmazva).
8. Egyébként: csapok elhelyezése az adott szakaszon `tab_spacing_mm` célközzel, `tab_length_mm` hosszal, a margók között egyenletesen elosztva; egymást átfedő csapok egyetlen, hosszabb csappá olvasztása.
9. Minden csap hozzáadása az adott sziget geometriájához (protrúzióként, szélesség = szeletvastagság, mélység = `backplate_thickness_mm`).
10. A Backplate alakjának felépítése a Mesh tényleges geometriájából: a Slice Engine-nel megegyező módon skálázott Mesh és a közös sík körüli, `[common_plane_mm − backplate_plane_tolerance_mm, common_plane_mm + backplate_plane_tolerance_mm]` vastagságú, a normál tengelyre merőleges "szeletlemez" térbeli (Boole-) metszetének meghatározása, majd ennek a metszetnek a (harmadik tengely, szelet-tengely) síkra vetítése. A tűrés-sáv (nem egy nulla-vastagságú síkmetszet) használata szükséges, mert a modell tényleges felülete a közös sík magasságában nem feltétlenül tökéletesen sík — egy egzakt metszet ezt a gyakorlatilag hasznos érintkezési területet elvágólag figyelmen kívül hagyná. A `non_backplate_islands`-ben szereplő szigetek geometriája — ha ténylegesen a tűrés-sávban van — továbbra is hozzájárul az alakhoz; a klaszterezés által automatikusan kizárt (ténylegesen távol eső) szigetek geometriája fizikai okból nem esik a sávba.
11. A sziluett kontúrjának eltolása `backplate_margin_mm`-mel.
12. A csapoknak megfelelő fészek-kivágások kialakítása a Backplate geometriájában, érintkező szakaszonként, a megfelelő pozíciókban.
13. A módosított Slice Set és a Backplate objektum összeállítása és visszaadása a Project felé.

## 7. Hibakezelés

Fail-fast elven:

* Egy, a `non_backplate_islands`-ben nem szereplő sziget egyáltalán nem éri el a Backplate síkját (nincs érintkező szakasza) → **hiba**.
* A domináns közös-sík csoport (6. szakasz 3. pont) nem tartalmazza az érintkező szakaszok szigorú többségét (> 50%) → **hiba**.
* Érvénytelen (`≤ 0`) `backplate_thickness_mm`, `tab_length_mm`, vagy `tab_spacing_mm` → **hiba**.
* Érvénytelen (`≤ 0`) `tab_edge_margin_mm` → **hiba**.
* Egy manuálisan megadott csap-pozíció nem fér el a megadott helyen → **hiba**.
* Érvénytelen `backplate_normal_axis` (megegyezik a `slice_axis`-szal, vagy nem létező tengely) → **hiba**.
* A domináns csoporton kívül eső, egyedi szigetek (6. szakasz 4. pont), valamint azok az érintkező szakaszok, ahol `usable_length ≤ 0` (6. szakasz 6. pont) — akár egy sziget összes szakaszára vonatkozóan is — kifejezetten **nem** hibák, kizárólag figyelmeztetést váltanak ki; a sziget geometriája ilyenkor is változatlanul megmarad, csak az adott szakaszon/szigeten nem kap csapot.

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
* A Backplate alakja a domináns közös síkbeli érintkező szakaszokból épített, tényleges keresztmetszet-alapú szabály szerint, margóval együtt definiált.
* A közös sík **automatikus, klaszterezés-alapú felismerése** (a domináns csoport, és a kívül eső szigetek automatikus, figyelmeztetés-alapú kizárása) egyértelműen rögzített, a `non_backplate_islands` kézi listától függetlenül is működve.
* A domináns csoport szigorú többségi (> 50%) biztonsági feltétele, és az ez alatti eset hiba-kezelése egyértelműen rögzített.
* A `usable_length ≤ 0` eset figyelmeztetés-alapú, szakaszonkénti kezelése (nem hiba) egyértelműen rögzített.
* A Hibakezelés fail-fast elven, egyértelműen felsorolja a blokkoló eseteket.
