# Nesting — Specifikáció

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-01
Utolsó módosítás: 2026-08-01
Kapcsolódó dokumentumok: [PROJECT_CONSTITUTION.md](../PROJECT_CONSTITUTION.md), [ARCHITECTURE.md](../ARCHITECTURE.md), [DOMAIN_MODEL.md](../DOMAIN_MODEL.md), [SPECIFICATION_STANDARD.md](../SPECIFICATION_STANDARD.md), [ENGINEERING_PRINCIPLES.md](../ENGINEERING_PRINCIPLES.md), [GAP_SYSTEM_SPEC.md](GAP_SYSTEM_SPEC.md), [BACKPLATE_SPEC.md](BACKPLATE_SPEC.md), [NUMBERING_SPEC.md](NUMBERING_SPEC.md)

## 1. Kontextus

A Nesting Engine a pipeline hetedik lépése, a Numbering Engine után. Bemenete a teljesen feldolgozott Slice Set (Dowel Hole, csap, számozás már rajta), az opcionális Backplate objektum és az opcionális Spacer-lista. Mivel a szeletek, a Backplate és a Spacer-ek eltérő anyagból/vastagságból készülhetnek, a Nesting Engine anyagonként (a ténylegesen hivatkozott `material_id` szerint) külön Nest-et állít elő — ha több alkatrész-kategória ugyanarra a `material_id`-re hivatkozik, azok egy közös Nest-be kerülnek. Az elérhető laptól nagyobb alkatrészeket (bármely típus: szelet/sziget, Backplate) toldáshoz szükséges, okosan elhelyezett vágásvonal(ak)kal osztja fel.

## 2. Felelősség

ARCHITECTURE.md-ből átvéve, nem bővítve: az elkészült alkatrészek (Slice, Backplate) optimális elrendezése a rendelkezésre álló Material-okon — kiegészítve a Spacer-ek (lapos korongokként történő) elrendezésével, és a laptól nagyobb alkatrészek toldás céljából történő felosztásával.

## 3. Bemenet

| Attribútum | Típus | Kötelező |
|---|---|---|
| Slice Set | Numbering Engine kimenete | igen |
| Backplate objektum | Backplate Engine kimenete | nem |
| Spacer lista | Gap Engine kimenete | nem |
| `material_definitions` | lista `{material_id, thickness_mm, sheet_width_mm, sheet_height_mm, kerf_mm}` | igen |
| `slice_material_id` | hivatkozás `material_definitions`-re | igen |
| `backplate_material_id` | hivatkozás `material_definitions`-re | nem (csak ha van Backplate) |
| `spacer_material_id` | hivatkozás `material_definitions`-re | nem (csak ha van Spacer) |
| `nesting_rotation_mode` | enum `{none, orthogonal, free}` | nem (alapérték: `orthogonal`) |
| `seam_marking_height_mm` | szám, mm | igen |
| `seam_marking_min_height_mm` | szám, mm | nem (alapérték: `seam_marking_height_mm / 2`) |
| `seam_marking_margin_mm` | szám, mm | nem (alapérték: `seam_marking_height_mm / 4`) |

## 4. Kimenet

**Nest-ek listája** — a ténylegesen hivatkozott `material_id`-nként egy Nest (több alkatrész-kategória is kerülhet egy közös Nest-be, ha ugyanarra a `material_id`-re hivatkoznak):

| Attribútum | Típus |
|---|---|
| `material_id` | hivatkozás |
| lapok száma | egész szám (nyitott végű, a tényleges kihasználtság alapján) |
| elrendezett elemek | lista `{alkatrész-hivatkozás (esetleg toldott résznek megfelelő al-hivatkozással), lap sorszáma, pozíció, forgatás}` |
| toldási varratok | lista `{alkatrész-hivatkozás, varratvonal geometriája, darabonkénti al-azonosító szövege és vektoros geometriája}` — csak toldott alkatrészeknél |

## 5. Paraméterek

| Név | Alapérték | Érvényességi tartomány | Jelentés |
|---|---|---|---|
| `material_definitions` | nincs (kötelező) | — | Elérhető anyagtípusok/vastagságok, lapmérettel és kerf-fel. |
| `nesting_rotation_mode` | `orthogonal` | `{none, orthogonal, free}` | `none`: nincs forgatás; `orthogonal`: csak 0°/90°; `free`: tetszőleges szög. |
| `seam_marking_height_mm` | nincs (kötelező) | `> 0` | A toldott darabok al-azonosítójának célzott magassága. |
| `seam_marking_min_height_mm` | `seam_marking_height_mm / 2` | `0 <` és `≤ seam_marking_height_mm` | A minimálisan elfogadható magasság, ha a cél nem fér el. |
| `seam_marking_margin_mm` | `seam_marking_height_mm / 4` | `≥ 0` | Az al-azonosító távolsága a varratvonaltól. |

## 6. Viselkedés

1. Validálás: `slice_material_id` vastagsága megegyezik-e a Slice Set szeletvastagságával; `backplate_material_id` (ha van) a `backplate_thickness_mm`-mel. Eltérés esetén hiba (7. szakasz).
2. A Spacer-ek átalakítása lapos korongokká: minden Spacer-hez `⌈gap_mm / spacer_material vastagsága⌉` db kör alakú alkatrész, `spacer_diameter_mm` átmérővel.
3. Az alkatrészek csoportosítása kizárólag a saját hozzárendelt `material_id` szerint (a szelet/sziget a `slice_material_id`, a Backplate a `backplate_material_id`, a Spacer-korong a `spacer_material_id` alapján kapja meg a magáét) — ha két vagy több kategória ugyanarra a `material_id`-re hivatkozik, azok egyetlen közös csoportba, és így egyetlen közös Nest-be kerülnek.
4. Minden alkatrész esetén: ha egyetlen elérhető forgatásban (a `nesting_rotation_mode` szerint) sem fér el a hozzá rendelt anyag lapméretén belül → felosztás egy vagy több egyenes vágásvonallal, minimális darabszámra, amíg minden rész elfér egy lapon. A vágásvonal(ak) elhelyezésekor a rendszer törekszik (best-effort, nem kötelező feltétel) elkerülni, hogy azok egybeessenek egy sziget érintkező szakaszának (csap/fészek) területével, vagy Dowel-/Spacer-pozíciókkal. A varrat pusztán vágásvonal — automatikus illesztő-geometria (pl. furat) nem kerül hozzáadásra; a tényleges összekötés kézi, gyártás utáni folyamat.
5. Minden felosztott alkatrész minden keletkező darabjához: az eredeti (Numbering Engine által adott) azonosító kiegészítése sorszámozott utótaggal (`-1`, `-2`, ...); ennek vektoros geometriaként történő elhelyezése a varrat közelében, `seam_marking_margin_mm` távolságra, `seam_marking_height_mm` célmérettel, `seam_marking_min_height_mm`-ig zsugorítható; ha még az sem fér el → hiba (7. szakasz).
6. Minden anyagcsoportra (a felosztott részekkel együtt) valódi alak (true-shape) szerinti elrendezés: a `kerf_mm` minimális távolságként alkalmazva a darabok között; a `nesting_rotation_mode` szerinti forgatási szabadsággal; törekvés a lehető legjobb kihasználtságra, nyitott végű lapszámmal ("ami ráfér, az ráférjen").
7. A Nest-ek összeállítása és visszaadása a Project felé.

## 7. Hibakezelés

Fail-fast elven:

* `slice_material_id` vastagsága nem egyezik a szeletvastagsággal → **hiba**.
* `backplate_material_id` vastagsága nem egyezik `backplate_thickness_mm`-mel → **hiba**.
* Érvénytelen (`< 0`) `kerf_mm` bármely `material_definitions` bejegyzésben → **hiba**.
* Hiányzó `spacer_material_id`, ha van Spacer-lista → **hiba**.
* Hiányzó `backplate_material_id`, ha van Backplate objektum → **hiba**.
* Érvénytelen (`≤ 0`) `seam_marking_height_mm` → **hiba**.
* Érvénytelen `seam_marking_min_height_mm` (nem esik a `(0, seam_marking_height_mm]` tartományba) → **hiba**.
* Érvénytelen (`< 0`) `seam_marking_margin_mm` → **hiba**.
* Egy toldott darab al-azonosítója még a minimális méretben sem fér el → **hiba**.

## 8. Kapcsolódó engine-ek és Domain Model fogalmak

* **Numbering Engine** — a bemeneti Slice Set forrása.
* **Gap Engine** — a Spacer-lista forrása.
* **Backplate Engine** — a Backplate objektum forrása.
* **DXF Export Engine** — a Nesting Engine kimenetét fogadja majd.
* Domain Model: Nest, Material, Slice, Backplate, Spacer.

## 9. Nyitott kérdések

Nincs megválaszolatlan pont.

## 10. Elfogadási kritériumok

* A specifikáció mind a 10 szakaszt hiánytalanul tartalmazza.
* Az anyagonkénti (nem kategóriánkénti) Nest-képzés — beleértve a közös `material_id` esetén történő összevonást — egyértelműen rögzített.
* A Spacer korong-alapú realizációja (darabszám-számítás) rögzített.
* A toldási szabály (bármely alkatrészre, egyenes vágással, csap/fészek- és Dowel/Spacer-tudatos, best-effort vágásvonal-elhelyezéssel, automatikus illesztő-geometria nélkül) egyértelműen rögzített.
* A toldott alkatrészek darabonkénti al-azonosítása (sorszámozott utótaggal, méretezési fallback-kal) egyértelműen rögzített.
* A Hibakezelés fail-fast elven, egyértelműen felsorolja a blokkoló eseteket.
