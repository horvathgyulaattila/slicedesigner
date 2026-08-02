# Slice Engine — Specifikáció

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-01
Utolsó módosítás: 2026-08-01
Kapcsolódó dokumentumok: [PROJECT_CONSTITUTION.md](../PROJECT_CONSTITUTION.md), [ARCHITECTURE.md](../ARCHITECTURE.md), [DOMAIN_MODEL.md](../DOMAIN_MODEL.md), [SPECIFICATION_STANDARD.md](../SPECIFICATION_STANDARD.md), [ENGINEERING_PRINCIPLES.md](../ENGINEERING_PRINCIPLES.md), [ADR-0003](../adr/0003-gap-aware-slicing.md), [MESH_IMPORT_SPEC.md](MESH_IMPORT_SPEC.md)

## 1. Kontextus

A Slice Engine a pipeline második lépése (ARCHITECTURE.md 3. szakasz), bemenete a Mesh Import kimenete. Az ADR-0003 nyomán a Slice Engine felelőssége kibővült: a Gap paramétert már a szeletelés során figyelembe veszi, úgy, hogy a szeletek és a köztük lévő hézagok együtt pontosan a Mesh eredeti méretét adják ki a szeletelési tengely mentén.

## 2. Felelősség

ARCHITECTURE.md-ből átvéve, nem bővítve: a Mesh keresztmetszeteinek (szeleteinek) előállítása a szeletelési tengely mentén — a Gap paraméter figyelembevételével, úgy, hogy a szeletek és a köztük tervezett hézagok együttesen a Mesh szeletelési tengely menti méretét adják ki —, Slice Set létrehozása.

## 3. Bemenet

| Attribútum | Típus | Kötelező |
|---|---|---|
| Mesh | Mesh Import kimenete (teljes objektum) | igen |
| `slice_axis` | enum `{X, Y, Z}` | nem (alapérték: `Z`) |
| `slice_thickness_mm` | szám, mm | igen |
| `gap_mm` | szám, mm | nem (alapérték: `0.0`) |
| `max_scale_tolerance` | arányszám | nem (alapérték: `0.02`) |

## 4. Kimenet

**Slice Set:**

| Attribútum | Típus |
|---|---|
| forrás Mesh-referencia | hivatkozás a bemeneti Mesh-re |
| Gap-referencia | `gap_mm` értéke (a Slice Engine tölti ki) |
| szeletek listája/sorrendje | Slice objektumok listája, tengely menti sorrendben |
| szeletek száma | egész szám (N) |

**Slice** (minden Slice Set-en belül):

| Attribútum | Típus | Mértékegység |
|---|---|---|
| vastagság | `slice_thickness_mm`-mel egyező szám | mm |
| geometria típusa | 1 vagy több zárt kontúr (polygon-lista) | mm |
| pozíció a szeletelési tengely mentén | szám (a szelet sávjának közepe) | mm |
| sorszám a Slice Set-en belül | egész szám, 1-től N-ig | — |

## 5. Paraméterek

| Név | Alapérték | Érvényességi tartomány | Jelentés |
|---|---|---|---|
| `slice_axis` | `Z` | `{X, Y, Z}` | A tengely, amely mentén a keresztmetszetek készülnek. |
| `slice_thickness_mm` | nincs (kötelező) | `> 0` | Az egyes szeletek vastagsága. |
| `gap_mm` | `0.0` | `≥ 0` | A szeletek között tervezett, egységes hézag mérete. Szeletpáronként eltérő Gap nem e specifikáció hatóköre. |
| `max_scale_tolerance` | `0.02` (2%) | `0 ≤ x < 1` | A Mesh méretének maximális arányos eltérése, amit a rendszer **egységes, mindhárom tengelyre azonos mértékű** skálázással kompenzál, hogy `N × slice_thickness_mm + (N-1) × gap_mm` pontosan a Mesh `slice_axis` menti méretét adja ki — a modell arányainak torzítása nélkül. E fölött hiba. |

## 6. Viselkedés

1. A Mesh bounding box-ának meghatározása a `slice_axis` mentén → `axis_size`.
2. A szeletszám (N) meghatározása: a legközelebbi egész az `(axis_size + gap_mm) / (slice_thickness_mm + gap_mm)` hányadosból.
3. Célméret kiszámítása: `target_size = N × slice_thickness_mm + (N-1) × gap_mm`.
4. Ha `target_size` és `axis_size` relatív eltérése meghaladja `max_scale_tolerance`-t → hiba (7. szakasz).
5. Egyébként: a Mesh **egységes, mindhárom tengelyre azonos mértékű** skálázása úgy, hogy `slice_axis` menti mérete pontosan `target_size` legyen — a modell aránya nem torzul, csak a teljes mérete változik kismértékben; figyelmeztetés rögzítése a validáltsági állapotban a skálázás tényéről és mértékéről.
6. Az *i.* szelet (i = 0..N−1) keresztmetszetének pozíciója: `i × (slice_thickness_mm + gap_mm) + slice_thickness_mm / 2`.
7. Minden pozícióban keresztmetszet előállítása — egy vagy több zárt kontúrból állhat.
8. Slice objektumok létrehozása: vastagság = `slice_thickness_mm`, geometria = kontúr(ok), pozíció = a 6. lépés szerinti koordináta, sorszám = 1-től N-ig.
9. Slice Set összeállítása (Gap-referencia = `gap_mm`) és visszaadása a Project felé.

## 7. Hibakezelés

Fail-fast elven:

* Érvénytelen (`≤ 0`) `slice_thickness_mm` → **hiba**.
* Érvénytelen (`< 0`) `gap_mm` → **hiba**.
* Üres Mesh vagy nulla méret a `slice_axis` mentén → **hiba**.
* `N < 1` → **hiba**.
* A szükséges skálázás meghaladja `max_scale_tolerance`-t → **hiba**.
* Egy adott metszősík üres vagy nyitott (nem zárt) keresztmetszetet eredményez → **hiba**.

## 8. Kapcsolódó engine-ek és Domain Model fogalmak

* **Mesh Import** — a bemeneti Mesh forrása.
* **Gap Engine** — a Slice Engine által már pozicionált Slice Set alapján kizárólag a Spacer geometriát állítja elő (ADR-0003).
* Domain Model: Mesh, Slice, Slice Set, Gap.

## 9. Nyitott kérdések

Nincs megválaszolatlan pont e specifikáció hatókörén belül. Kimaradt a hatókörből (jövőbeli téma): szeletpáronként eltérő Gap támogatása.

## 10. Elfogadási kritériumok

* A specifikáció mind a 10 szakaszt hiánytalanul tartalmazza.
* A Bemenet/Kimenet a DOMAIN_MODEL.md és az ADR-0003 szerinti Slice/Slice Set/Gap fogalmakat típus- és mértékegység-szinten pontosítja.
* A pozicionálási képlet igazoltan biztosítja, hogy a szeletek és hézagok együtt a Mesh eredeti méretét adják ki (ADR-0003).
* A skálázási logika bizonyíthatóan nem torzítja a modell arányait (mindhárom tengelyen azonos skálázási tényező).
* A Hibakezelés fail-fast elven, egyértelműen felsorolja a blokkoló eseteket.
