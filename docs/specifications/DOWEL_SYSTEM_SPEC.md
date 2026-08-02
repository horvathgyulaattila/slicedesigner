# Dowel System — Specifikáció

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-01
Utolsó módosítás: 2026-08-01
Kapcsolódó dokumentumok: [PROJECT_CONSTITUTION.md](../PROJECT_CONSTITUTION.md), [ARCHITECTURE.md](../ARCHITECTURE.md), [DOMAIN_MODEL.md](../DOMAIN_MODEL.md), [SPECIFICATION_STANDARD.md](../SPECIFICATION_STANDARD.md), [ENGINEERING_PRINCIPLES.md](../ENGINEERING_PRINCIPLES.md), [ADR-0004](../adr/0004-optional-assembly-mechanisms.md), [ADR-0005](../adr/0005-dowel-before-gap-ordering.md), [SLICE_ENGINE_SPEC.md](SLICE_ENGINE_SPEC.md), [GAP_SYSTEM_SPEC.md](GAP_SYSTEM_SPEC.md)

## 1. Kontextus

A Dowel Engine a pipeline harmadik lépése (ARCHITECTURE.md 3. szakasz, ADR-0005 szerint a Slice Engine után, a Gap Engine előtt). Bemenete a Slice Engine kimenete: a pozicionált Slice Set. A Dowel Engine önállóan, a Gap Engine ismerete nélkül határozza meg a Dowel- és Dowel Hole-pozíciókat, a modell külső palástján belül maradva. Kimenete (a Dowel Hole-okkal ténylegesen módosított Slice Set, valamint a Dowel-pozíció lista) a Gap Engine bemenete (GAP_SYSTEM_SPEC.md, ADR-0005).

## 2. Felelősség

ARCHITECTURE.md-ből átvéve, nem bővítve: Dowel és Dowel Hole pozíciójának és geometriájának számítása a szeletek egymáshoz viszonyított illesztéséhez, a Slice Engine által pozicionált Slice Set alapján, a modell külső palástján belül maradva.

## 3. Bemenet

| Attribútum | Típus | Kötelező |
|---|---|---|
| Slice Set | Slice Engine kimenete (teljes objektum) | igen |
| `dowel_diameter_mm` | szám, mm | igen |
| `spacer_diameter_mm` | szám, mm | nem (alapérték: `0`; kizárólag a `min_edge_clearance_mm` alapértékének számításához) |
| `min_edge_clearance_mm` | szám, mm | nem (alapérték: `max(dowel_diameter_mm, spacer_diameter_mm) / 2`) |
| `dowel_count_per_region` | egész szám | nem (alapérték: `3`) |
| `min_dowels_per_region` | egész szám | nem (alapérték: `1`) |
| `blind_hole_cap_mm` | szám, mm | nem (alapérték: a Slice Set szeletvastagságának 30%-a) |
| `manual_dowel_positions` | lista `{x, y, kezdő szelet sorszáma, záró szelet sorszáma}` | nem (alapérték: üres lista) |

## 4. Kimenet

**Módosított Slice Set** — a Slice Engine kimenetével azonos szerkezetű, de minden érintett Slice geometriájából kimetszve a rá eső Dowel Hole(ok). A Slice geometria reprezentációja (SLICE_ENGINE_SPEC.md, "1 vagy több zárt kontúr") ezennel pontosításra kerül: a kontúr körüljárási iránya (vagy azzal egyenértékű, megkülönböztető jelölés) határozza meg, hogy az adott kontúr szilárd anyagot (pl. önálló sziget) vagy kivágott lyukat (pl. Dowel Hole) jelöl — a pontos technikai konvenció Phase 4 implementációs döntés, itt csak a megkülönböztetés kötelező meglétét rögzítjük.

**Dowel-pozíciók listája**, minden Dowel:

| Attribútum | Típus | Mértékegység |
|---|---|---|
| pozíció (x, y) | koordináta-pár | mm |
| átmérő | = `dowel_diameter_mm` | mm |
| hossz | a kezdő és záró szelet külső síkjai közti távolság (a szeletek már gap-inkluzív pozíciója alapján) | mm |
| érintett szeletek | kezdő és záró szelet sorszáma | — |
| tartozó régió azonosító | hivatkozás | — |

Minden érintett Slice-hoz tartozó Dowel Hole: átmérő (= `dowel_diameter_mm`), típus (átmenő / vak), mélység (átmenő esetén = szeletvastagság; vak esetén = szeletvastagság − `blind_hole_cap_mm`).

## 5. Paraméterek

| Név | Alapérték | Érvényességi tartomány | Jelentés |
|---|---|---|---|
| `dowel_diameter_mm` | nincs (kötelező) | `> 0` | A Dowel (és a hozzá tartozó furatok) átmérője. |
| `spacer_diameter_mm` | `0` | `≥ 0` | Csak a `min_edge_clearance_mm` alapértékének számításához; a tényleges Spacer-elhelyezés a Gap Engine feladata. Ha `use_spacers` igaz, ennek az értéknek meg kell egyeznie a Gap Engine saját `spacer_diameter_mm` paraméterével — az egyeztetés a Project felelőssége. |
| `min_edge_clearance_mm` | `max(dowel_diameter_mm, spacer_diameter_mm) / 2` | `≥ 0` | A Dowel-pozíciónak (a rá kerülő Spacer méretét is figyelembe véve) ennyi biztonsági távolságot kell tartania a szelet külső szélétől. |
| `dowel_count_per_region` | `3` | `≥ 1` | Az elhelyezendő Dowel-ek célszáma összefüggő 3D anyagrégiónként. |
| `min_dowels_per_region` | `1` | `1 ≤ x ≤ dowel_count_per_region` | A minimálisan elfogadható Dowel-szám egy régióban, ha a cél nem fér el. |
| `blind_hole_cap_mm` | szeletvastagság 30%-a | `0 <` és `<` szeletvastagság | A vak furat lezáró oldalán megmaradó anyagvastagság. |
| `manual_dowel_positions` | üres lista | — | Kézzel megadott, elsőbbséget élvező Dowel-pozíciók. |

## 6. Viselkedés

1. A szeletek geometriájának (lyuk-vs-sziget megkülönböztetéssel) egymáshoz kapcsolódó, egymást átfedő kontúrjai mentén a teljes Slice Set-en átívelő, összefüggő 3D anyagrégiók azonosítása.
2. Minden `manual_dowel_positions` elem validálása: a megadott teljes szeletsávban a `dowel_diameter_mm + 2×min_edge_clearance_mm` átmérőjű kör teljes egészében az adott szeletek anyagán belül marad-e. Érvénytelen pozíció, vagy egymást átfedő kézi pozíciók esetén hiba (7. szakasz).
3. Minden régióban: az érvényes kézi pozíciók hozzárendelése a régióhoz.
4. Ha a régióban lévő kézi pozíciók száma nem éri el `dowel_count_per_region`-t, automatikus kiegészítés: olyan (x,y) pozíciók keresése, amelyeknél a fenti kör a lehető leghosszabb, egymást követő szeletsávon át (legalább 2 szeleten) a régión belül marad, a kézi pozíciókkal és egymással sem átfedve.
5. Ha egy régióban a kézi és automatikus pozíciók együttes száma nem éri el `dowel_count_per_region`-t, de legalább `min_dowels_per_region`-t igen → a ténylegesen elért darabszám elfogadása; figyelmeztetés rögzítése.
6. Ha még `min_dowels_per_region` sem érhető el egy régióban → hiba (7. szakasz).
7. Minden elhelyezett Dowel-hoz: a szakasz két végén lévő szeleten vak furat (mélység = szeletvastagság − `blind_hole_cap_mm`), minden közbenső szeleten átmenő furat.
8. A Dowel Hole-ok tényleges kimetszése az érintett szeletek geometriájából, lyukként megjelölve.
9. A módosított Slice Set és a Dowel-pozíció lista összeállítása és visszaadása a Project felé.

## 7. Hibakezelés

Fail-fast elven:

* Érvénytelen (`≤ 0`) `dowel_diameter_mm` → **hiba**.
* Érvénytelen (`< 0`) `spacer_diameter_mm` vagy `min_edge_clearance_mm` → **hiba**.
* Érvénytelen (`< 1`) `dowel_count_per_region` vagy `min_dowels_per_region`, vagy `min_dowels_per_region > dowel_count_per_region` → **hiba**.
* Érvénytelen `blind_hole_cap_mm` (nem esik a `(0, szeletvastagság)` tartományba) → **hiba**.
* Egy manuálisan megadott pozíció nem fér el a megadott szeletsávban → **hiba**.
* Két manuális pozíció egymást átfedi → **hiba**.
* Egy összefüggő régió nem képes befogadni legalább `min_dowels_per_region` db Dowel-t → **hiba**.

## 8. Kapcsolódó engine-ek és Domain Model fogalmak

* **Slice Engine** — a bemeneti Slice Set forrása.
* **Gap Engine** — a kimenetét (módosított Slice Set és Dowel-pozíciók) fogadja, a Spacer-eket ehhez igazítja (ADR-0005).
* Domain Model: Dowel, Dowel Hole, Slice, Spacer (csak a `min_edge_clearance_mm` alapérték-számításához).

## 9. Nyitott kérdések

Nincs megválaszolatlan pont.

## 10. Elfogadási kritériumok

* A specifikáció mind a 10 szakaszt hiánytalanul tartalmazza.
* A lyuk-vs-sziget kontúr-megkülönböztetés explicit módon rögzített.
* A régiónkénti cél/minimum Dowel-szám logika (kézi és automatikus pozíciók együtt) egyértelműen rögzített.
* A vak furat logika mindkét végre és minden közbenső szeletre egyértelműen leírt.
* A Hibakezelés fail-fast elven, egyértelműen felsorolja a blokkoló eseteket.
