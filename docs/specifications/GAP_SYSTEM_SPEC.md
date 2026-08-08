# Gap System — Specifikáció

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-01
Utolsó módosítás: 2026-08-06
Kapcsolódó dokumentumok: [PROJECT_CONSTITUTION.md](../PROJECT_CONSTITUTION.md), [ARCHITECTURE.md](../ARCHITECTURE.md), [DOMAIN_MODEL.md](../DOMAIN_MODEL.md), [SPECIFICATION_STANDARD.md](../SPECIFICATION_STANDARD.md), [ENGINEERING_PRINCIPLES.md](../ENGINEERING_PRINCIPLES.md), [ADR-0003](../adr/0003-gap-aware-slicing.md), [ADR-0004](../adr/0004-optional-assembly-mechanisms.md), [ADR-0005](../adr/0005-dowel-before-gap-ordering.md), [SLICE_ENGINE_SPEC.md](SLICE_ENGINE_SPEC.md)

## 1. Kontextus

A Gap Engine a pipeline negyedik lépése (ARCHITECTURE.md 3. szakasz, ADR-0005 szerint a Dowel Engine után). Bemenete a Dowel Engine kimenete: a már pozicionált, és — ha volt Dowel-elhelyezés — a Dowel Hole-okkal ténylegesen módosított geometriájú Slice Set, valamint a Dowel/Dowel Hole pozíció-lista. Az ADR-0003 nyomán a Gap Engine felelőssége kizárólag a Spacer geometria előállítása. Az ADR-0005 nyomán a Spacer-elhelyezés előnyben részesíti a már meghatározott Dowel-pozíciókat — csak ott generál önálló Spacer-pozíciót, ahol a Dowel-pozíciók nem elegendők a célszámhoz. Az ADR-0004 nyomán a Gap Engine csak akkor kerül meghívásra, ha a Project `use_spacers` kapcsolója igaz.

## 2. Felelősség

ARCHITECTURE.md-ből átvéve, nem bővítve (ADR-0003, ADR-0005 szerint): a Gap fizikai megvalósítását biztosító Spacer specifikáció előállítása, a Slice Engine által már a Gap figyelembevételével pozicionált Slice Set alapján, a Dowel Engine által már meghatározott Dowel-pozíciók figyelembevételével és előnyben részesítésével.

## 3. Bemenet

| Attribútum | Típus | Kötelező |
|---|---|---|
| Slice Set | Dowel Engine kimenete (a Dowel Hole-okkal már módosított geometriájú Slice Set, Gap-referenciával) | igen |
| Dowel-pozíciók | Dowel Engine kimenete (Dowel/Dowel Hole pozíció-lista: koordináta, átmérő, érintett szeletek) | nem (üres, ha nem volt Dowel-elhelyezés) |
| `spacer_diameter_mm` | szám, mm | igen |
| `spacer_count_per_gap` | egész szám | nem (alapérték: `3`) |
| `min_spacers_per_region` | egész szám | nem (alapérték: `1`) |

## 4. Kimenet

**Slice Set** — változatlanul továbbadva (a Gap Engine a Slice Set geometriáját nem módosítja, lásd 6. szakasz).

**Spacer-ek listája.** Minden Gap-hez (N-1 db, szomszédos szeletpáronként) tartozik a metszet elkülönülő régióinak listája; minden régióhoz a ténylegesen elhelyezett Spacer-ek listája.

Minden Spacer:

| Attribútum | Típus | Mértékegység |
|---|---|---|
| geometriai forma | henger | — |
| átmérő | = `spacer_diameter_mm` | mm |
| vastagság | = az adott Gap mérete (`gap_mm`) | mm |
| pozíció | koordináta a metszet-régión belül | mm |
| tartozó Gap / régió azonosító | hivatkozás — a régió-azonosító minden Gap-en belül 1-től újraindul (nem a teljes Slice Set-en át folyamatos sorszám) | — |

## 5. Paraméterek

| Név | Alapérték | Érvényességi tartomány | Jelentés |
|---|---|---|---|
| `spacer_diameter_mm` | nincs (kötelező) | `> 0` | A henger alakú Spacer átmérője. Ha `use_dowels` igaz, ennek az értéknek meg kell egyeznie a Dowel Engine saját `spacer_diameter_mm` paraméterével — az egyeztetés a Project felelőssége. |
| `spacer_count_per_gap` | `3` | `≥ 1` | Az elhelyezendő Spacer-ek célszáma metszet-régiónként. |
| `min_spacers_per_region` | `1` | `0 ≤ x ≤ spacer_count_per_gap` | A minimálisan elfogadható Spacer-szám egy metszet-régióban, ha a cél (`spacer_count_per_gap`) nem fér el. `0` explicit megengedi, hogy egy régióban egyáltalán ne legyen Spacer (pl. egy apró, Dowel-lel önmagában megfelelően megtámasztott kapcsolódási pontnál) — ez tudatos, projektgazdai beállítást igényel, nem az alapértelmezett (`1`) viselkedés. |

## 6. Viselkedés

1. Ha a Slice Set Gap-referenciája (`gap_mm`) = 0 → üres Spacer-lista visszaadása, feldolgozás vége.
2. Minden egymást követő szeletpár (Slice_i, Slice_i+1) esetén: a két szelet teljes geometriájának (összes kontúrjuk uniója) metszetének meghatározása.
3. A metszet egymástól elkülönülő (össze nem függő) régiókra bontása.
4. Minden régióban:
   - a. Az adott régióba eső, mindkét szeletet érintő Dowel-pozíciók azonosítása — ezek mindegyike kötelezően Spacer-helyet kap (a Dowel-re fűzött Spacer).
   - b. Ha az így kapott Spacer-szám eléri `spacer_count_per_gap`-et → nincs szükség további, önálló pozícióra.
   - c. Ha kevesebb → a hiányzó darabszámig önálló, a Dowel-pozíciókkal és egymással sem átfedő `spacer_diameter_mm` átmérőjű henger-pozíciók generálása, amíg el nem érjük a célszámot vagy be nem telik a régió.
5. Ha az így kapott összes Spacer-szám egy régióban nem éri el `spacer_count_per_gap`-et, de legalább `min_spacers_per_region`-t igen → a ténylegesen elférő darabszám elhelyezése; figyelmeztetés rögzítése.
6. Ha még `min_spacers_per_region` sem érhető el egy régióban (ideértve a nulla átfedésű, "lebegő" kontúr esetét is) → hiba (7. szakasz).
7. A Spacer-lista összeállítása és visszaadása a Project felé — a Gap Engine a Slice Set geometriáját nem módosítja tovább.

## 7. Hibakezelés

Fail-fast elven:

* Érvénytelen (`≤ 0`) `spacer_diameter_mm` → **hiba**.
* Érvénytelen (`< 1`) `spacer_count_per_gap` → **hiba**.
* Érvénytelen (`< 0`) `min_spacers_per_region`, vagy `min_spacers_per_region > spacer_count_per_gap` → **hiba**.
* Egy metszet-régió nem képes befogadni legalább `min_spacers_per_region` db Spacert (a Dowel-alapú és önálló pozíciókat együtt számítva, ideértve a nulla átfedésű esetet is) → **hiba**. `min_spacers_per_region = 0` esetén ez a feltétel sosem teljesül (a régió mindig elfogadott, akár nulla Spacerrel is) — ilyenkor a 6. szakasz 5. pontja szerinti figyelmeztetés rögzítése akkor is megtörténik, ha a ténylegesen elhelyezett Spacer-szám nulla.

## 8. Kapcsolódó engine-ek és Domain Model fogalmak

* **Dowel Engine** — a bemeneti, már módosított Slice Set és a Dowel-pozíciók forrása (ADR-0005).
* **Project** — az ADR-0004 szerint dönt a Gap Engine meghívásáról/kihagyásáról (`use_spacers` kapcsoló).
* Domain Model: Gap, Spacer, Slice Set, Dowel.

## 9. Nyitott kérdések

Nincs megválaszolatlan pont.

## 10. Elfogadási kritériumok

* A specifikáció mind a 10 szakaszt hiánytalanul tartalmazza.
* A Bemenet egyértelműen jelzi, hogy a Slice Set forrása a Dowel Engine (nem a Slice Engine közvetlenül).
* A Spacer-elhelyezés bizonyíthatóan előnyben részesíti a Dowel-pozíciókat, és csak a hiányzó darabszámig generál önálló pozíciót (ADR-0005).
* A régiónkénti minimum/cél Spacer-szám logika (Dowel-alapú és önálló pozíciók együttesen) egyértelműen rögzített.
* A `min_spacers_per_region` `0` értékének explicit megengedettsége és jelentése egyértelműen rögzített.
* A régió-azonosító Gap-enkénti újraindítása egyértelműen rögzített.
* A Hibakezelés fail-fast elven, egyértelműen felsorolja a blokkoló eseteket.
