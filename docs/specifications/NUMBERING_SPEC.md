# Numbering — Specifikáció

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-01
Utolsó módosítás: 2026-08-04
Kapcsolódó dokumentumok: [PROJECT_CONSTITUTION.md](../PROJECT_CONSTITUTION.md), [ARCHITECTURE.md](../ARCHITECTURE.md), [DOMAIN_MODEL.md](../DOMAIN_MODEL.md), [SPECIFICATION_STANDARD.md](../SPECIFICATION_STANDARD.md), [ENGINEERING_PRINCIPLES.md](../ENGINEERING_PRINCIPLES.md), [ADR-0004](../adr/0004-optional-assembly-mechanisms.md), [BACKPLATE_SPEC.md](BACKPLATE_SPEC.md)

## 1. Kontextus

A Numbering Engine a pipeline hatodik lépése (ARCHITECTURE.md 3. szakasz, a Backplate Engine után). Bemenete a Backplate Engine kimenete (módosított Slice Set + Backplate objektum) — vagy ha `use_backplate=false`, közvetlenül a megelőző engine (Dowel/Gap/Slice Engine) kimenete, Backplate objektum nélkül. A Numbering Engine minden szelet minden szigetéhez egyedi azonosítót rendel, ezt bevési/kivágja a sziget geometriájába, és — ha van Backplate — a hozzá tartozó, elrejtett pozíción is megjelöli.

## 2. Felelősség

ARCHITECTURE.md-ből átvéve, nem bővítve: minden Slice egyedi azonosítóval ellátása — bevésve/kivágva a szelet geometriájába —, valamint a hozzá tartozó Backplate pozíción a szelet helyének megjelölése, biztosítva a hibamentes összeszerelést.

## 3. Bemenet

| Attribútum | Típus | Kötelező |
|---|---|---|
| Slice Set | a pipeline addig lefutott lépéseinek kimenete (a Slice-ok saját, Slice Engine által adott sorszámával) | igen |
| Backplate objektum | Backplate Engine kimenete | nem (ha `use_backplate=false`, nincs Backplate-jelölés) |
| `numbering_normal_axis` | enum (a `slice_axis`-tól eltérő két tengely egyike, előjellel) | igen |
| `numbering_direction_axis_sign` | előjel (a `slice_axis`-tól és `numbering_normal_axis`-tól eltérő harmadik tengely iránya) | igen |
| `numbering_height_mm` | szám, mm | igen |
| `numbering_min_height_mm` | szám, mm | nem (alapérték: `numbering_height_mm / 2`) |
| `numbering_margin_mm` | szám, mm | nem (alapérték: `numbering_height_mm / 4`) |
| `slice_numbering_overrides` | lista `{szelet sorszáma, sziget azonosító?, numbering_height_mm?, numbering_min_height_mm?, numbering_margin_mm?, manual_position?}` | nem (alapérték: üres lista) |

## 4. Kimenet

**Módosított Slice Set** — minden sziget geometriájába bevésve/kivágva a saját azonosítója (vektoros kontúr, külön jelölve — nem szilárd anyag, nem lyuk, hanem felületi jelölés/gravírozás; a tényleges DXF réteg-besorolás a DXF Export Engine feladata).

**Módosított Backplate objektum** (ha volt Backplate) — minden, Backplate-hez kapcsolódó szigethez tartozó azonosító bevésve a hozzá tartozó, legalsó érintkező szakasz Backplate felőli sávjába.

Minden azonosító:

| Attribútum | Típus |
|---|---|
| szöveg | `"N"` (egyetlen sziget esetén) vagy `"N/Betű"` (több sziget esetén; `N` = a szelet Slice Engine szerinti sorszáma, `Betű` = A-tól kezdődő, `numbering_direction_axis_sign` szerinti sorrend) |
| geometria | vektoros kontúr |
| tájolás | álló vagy 90°-kal elforgatott (amelyik nagyobb, még érvényes méretet enged) |
| tényleges magasság | a `numbering_height_mm` és a rendelkezésre álló hely alapján számolt, ténylegesen alkalmazott érték |
| pozíció | a sziget "hátulsó-alsó" sarkához legközelebbi, ténylegesen elférő pozícióban (Slice-on) — l. 6. szakasz 2–3. pont —, illetve a legalsó érintkező szakasz sávjában (Backplate-en) |

## 5. Paraméterek

| Név | Alapérték | Érvényességi tartomány | Jelentés |
|---|---|---|---|
| `numbering_normal_axis` | nincs (kötelező) | a `slice_axis`-tól eltérő 2 tengely egyike, előjellel | A "hátulsó" irány — függetlenül attól, fut-e a Backplate Engine. |
| `numbering_direction_axis_sign` | nincs (kötelező) | a `slice_axis`-tól és `numbering_normal_axis`-tól eltérő tengely előjele | A szigetek A/B/C sorrendje, és az "alsó" irány. |
| `numbering_height_mm` | nincs (kötelező) | `> 0` | A szám célzott (kényelmesen olvasható) magassága. |
| `numbering_min_height_mm` | `numbering_height_mm / 2` | `0 <` és `≤ numbering_height_mm` | A minimálisan elfogadható magasság, ha a cél nem fér el. |
| `numbering_margin_mm` | `numbering_height_mm / 4` | `≥ 0` | A szám távolsága a két legközelebbi éltől. |
| `slice_numbering_overrides` | üres lista | — | Szigetenkénti méret- vagy pozíció-felülbírálás. |

## 6. Viselkedés

1. Minden szelet minden szigetéhez az azonosító szöveg meghatározása.
2. Minden szigethez (felülírt paraméterekkel, ha van): a sziget "hátulsó" és "alsó" sarkának meghatározása, `numbering_margin_mm` távolságra a két éltől — ez a pozíció a keresés preferált célpontja, nem kizárólagos, kötelező helye (l. 3–4. pont).
3. Minden vizsgált magasság-tájolás kombinációhoz (l. 4. pont): annak megállapítása, hogy a 2. pont szerinti célpontban elfér-e az azonosító; ha nem, a sziget teljes területén (a befoglaló téglalapján belül, felső korlát vagy keresési sugár nélkül) keresés a célponthoz legközelebbi olyan pozícióra, ahol az azonosító teljes egészében a sziget anyagán belül marad. A kettő közül a nagyobb elérhető magasságot engedő tájolás kiválasztása; azonos magasság esetén a célponthoz közelebbi pozíció élvez elsőbbséget.
4. Ha `numbering_height_mm`-hez (bármelyik tájolásban) található érvényes pozíció (a 3. pont szerint) → azzal a mérettel; ha nem, de `numbering_min_height_mm`-hez igen → a ténylegesen elférő mérettel, figyelmeztetéssel; ha `numbering_min_height_mm`-hez sem található érvényes pozíció egyik tájolásban sem → a jelölés kimarad az adott szigetről, figyelmeztetéssel (ugyanígy, mint a Backplate-en lévő azonosítónál, lásd 6. lépés).
5. Az azonosító vektoros geometriájának elhelyezése a sziget geometriájában.
6. Ha van Backplate objektum: minden, a Backplate-hez kapcsolódó szigethez a legalsó érintkező szakaszának Backplate felőli sávjában (szélesség = szeletvastagság) ugyanazon azonosító elhelyezése, ugyanazzal a méretezési logikával — de itt, ha még a minimális méret sem fér el, az csak figyelmeztetés, nem hiba.
7. A módosított Slice Set és (ha volt) a módosított Backplate objektum összeállítása és visszaadása a Project felé.

## 7. Hibakezelés

Fail-fast elven:

* Érvénytelen (`≤ 0`) `numbering_height_mm` → **hiba**.
* Érvénytelen `numbering_min_height_mm` (nem esik a `(0, numbering_height_mm]` tartományba) → **hiba**.
* Érvénytelen (`< 0`) `numbering_margin_mm` → **hiba**.
* Érvénytelen `numbering_normal_axis` vagy `numbering_direction_axis_sign` (megegyezik a `slice_axis`-szal vagy egymással, vagy nem létező tengely) → **hiba**.
* *(Nem hiba, csak figyelmeztetés:)* egy sziget saját, és/vagy a Backplate-en lévő azonosítója egyik tájolásban sem éri el `numbering_min_height_mm`-et — a jelölés az érintett helyről kimarad.

## 8. Kapcsolódó engine-ek és Domain Model fogalmak

* **Backplate Engine** — a bemeneti (módosított) Slice Set és a Backplate objektum forrása.
* **Nesting Engine** — a Numbering Engine kimenetét fogadja majd; ismernie kell az azonosítók pozícióját (jövőbeli NESTING_SPEC hatóköre).
* **DXF Export Engine** — a végleges DXF réteg-besorolás (vágás vs. gravírozás) az ő feladata; ez a specifikáció csak jelzi a megkülönböztetés szükségességét.
* Domain Model: Slice, Backplate, Numbering.

## 9. Nyitott kérdések

Nincs megválaszolatlan pont.

## 10. Elfogadási kritériumok

* A specifikáció mind a 10 szakaszt hiánytalanul tartalmazza.
* Az azonosító-formátum (N, illetve N/Betű) és a betűrend szabálya egyértelműen rögzített.
* A tájolás-választási és méretezési logika mindkét elhelyezésre (szelet, Backplate) egységesen, figyelmeztetés-alapú fallback-kal rögzített.
* A szelet-oldali elhelyezés a preferált sarok-pozícióhoz legközelebbi, ténylegesen elférő pozíciót keresi a sziget teljes területén, nem kizárólag az elméleti sarokpontot — ez a keresési elv egyértelműen rögzített.
* A `numbering_normal_axis` és `numbering_direction_axis_sign` a Backplate Engine-től függetlenek.
* A Hibakezelés fail-fast elven, egyértelműen felsorolja a blokkoló eseteket.
