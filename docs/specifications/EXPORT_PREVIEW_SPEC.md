# 2D Export-előnézet — Specifikáció

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-13
Utolsó módosítás: 2026-08-13
Kapcsolódó dokumentumok: [PROJECT_CONSTITUTION.md](../PROJECT_CONSTITUTION.md), [ARCHITECTURE.md](../ARCHITECTURE.md), [DOMAIN_MODEL.md](../DOMAIN_MODEL.md), [SPECIFICATION_STANDARD.md](../SPECIFICATION_STANDARD.md), [ENGINEERING_PRINCIPLES.md](../ENGINEERING_PRINCIPLES.md), [NESTING_SPEC.md](NESTING_SPEC.md), [DXF_EXPORT_SPEC.md](DXF_EXPORT_SPEC.md), [ROADMAP.md](../ROADMAP.md)

## 1. Kontextus

A 2D export-előnézet a GUI réteg (`PreviewPanel`) bővítése, a ROADMAP Phase 7.1 tétele. Célja, hogy a felhasználó a DXF Export gomb megnyomása — vagyis tényleges fájl generálása — előtt vizuálisan ellenőrizhesse a Nesting Engine kimenetét: mely alkatrészek kerülnek melyik anyaglapra, milyen elrendezésben, és ez belefér-e a lap méretébe.

Megjegyzés a hatókörről: a `SPECIFICATION_STANDARD.md` sablonja formálisan a Phase 2 domain engine-ekre készült. Ez a specifikáció egy GUI-réteg widgetet ír le, nem új domain engine-t — a sablon szerkezetét (10 szakasz) a konzisztencia kedvéért megtartja, de egyes szakaszok tartalma (Bemenet/Kimenet) ennek megfelelően GUI-kontextusban értendő, nem domain-adatcsereként.

Nem épít új domain-adatra: a Nesting Engine (`NESTING_SPEC.md`) kimenete, a `Nest` lista, már tartalmaz minden szükséges geometriát a megjelenítéshez — ugyanazt, amit a DXF Export Engine (`DXF_EXPORT_SPEC.md`) is felhasznál.

## 2. Felelősség

A `PreviewPanel` egy új nézet-módja: a legutóbbi sikeres Futtatás `Nest`-jeinek laponkénti, kétdimenziós, nagyítható/mozgatható vizuális megjelenítése — vágási kontúrokkal, azonosítókkal és a lap fizikai méretével —, kizárólag ellenőrzési célra. Nem generál fájlt, nem módosít domain-adatot, nem hívja meg a DXF Export Engine-t.

## 3. Bemenet

| Forrás | Típus | Kötelező |
|---|---|---|
| `Nest`-ek listája | a Nesting Engine kimenete (`NESTING_SPEC.md` 4. szakasz), a `MainWindow`-ban már tárolt legutóbbi sikeres Futtatás eredménye | igen (2D mód csak akkor aktiválható, ha van) |
| Anyag-lapméret (`material_definitions` szélesség/magasság mm) | a Futtatáshoz megadott GUI-paraméter, anyagazonosító szerint | igen, a háttér-téglalap rajzolásához |

Nincs új domain-számítás — a szakasz kizárólag a már meglévő adat GUI-oldali felhasználását írja le.

## 4. Kimenet

Nincs domain-kimenet (nem hoz létre `Export` objektumot, nem ír fájlt). GUI-állapot:

| Állapot | Típus |
|---|---|
| aktuálisan megjelenített lap (anyag + laponkénti sorszám) | munkamenet-szintű, nem mentett |
| nézet nagyítási/eltolási állapota | munkamenet-szintű, nem mentett |
| 3D/2D nézet-mód | munkamenet-szintű, nem mentett |

## 5. Paraméterek

| Név | Alapérték | Jelentés |
|---|---|---|
| `preview_cut_color` | fekete | A vágási kontúrok előnézeti színe. Független a tényleges DXF export réteg-színeitől (`cut_layer_color`), mert azok Futtatáskor még nem feltétlenül állítottak be. |
| `preview_engrave_color` | kék | Az azonosítók (Numbering + toldási al-azonosítók) előnézeti színe, ugyanezen okból független a `engrave_layer_color`-tól. |
| `preview_min_zoom` / `preview_max_zoom` | 0.1× / 10× | A nagyítás megengedett tartománya. |

Rejtett, nem paraméterezett szín/határérték nincs (Engineering Principles, paraméterezhetőség).

## 6. Viselkedés

1. A `PreviewPanel` tetején egy 3D/2D nézet-váltó jelenik meg. A 2D opció csak akkor választható, ha van legutóbbi sikeres Futtatás eredménye (`_last_nests` nem üres) — enélkül inaktív, tooltippel jelezve az okot.
2. 2D módban a jelenlegi 3D-specifikus vezérlők (szeletenkénti kiemelés, nézet-váltó rádiógombok) elrejtésre kerülnek; helyettük Előző/Következő lap navigáció jelenik meg.
3. A lapok sorrendje determinisztikus: anyagazonosító (ábécésorrend), azon belül laponkénti sorszám szerint. Ha csak egy lap van, a navigációs gombok inaktívak.
4. Új Futtatás sikeres lezárása után a 2D nézet (ha aktív) automatikusan az első lapra áll vissza, mivel az adat megváltozott — a 3D/2D mód-választás maga viszont megmarad (nem kényszerít vissza 3D-re).
5. Laponkénti megjelenítés: a lap fizikai mérete (`material_definitions` szerint) háttér-téglalapként; a `PlacedPart.contours` a `preview_cut_color` színnel; a `PlacedPart.numbering_marks` (és a `SeamRecord.sub_identifiers`, ha az adott lapon van toldott darab) a `preview_engrave_color` színnel.
6. Lapváltáskor a nézet alapállapotban "illessz ablakhoz" nagyítású és középre igazított.
7. A nézet egérgörgővel nagyítható (a `preview_min_zoom`/`preview_max_zoom` határok között), kattintva-húzva mozgatható (pan).

## 7. Hibakezelés

Ez a szakasz GUI-állapotokat ír le, nem domain-kivételeket (fail-fast a domain rétegben már megtörtént a Futtatáskor):

* Nincs még sikeres Futtatás eredménye → a 2D nézet-opció inaktív, tooltip magyarázattal; nem hiba.
* Egy `Nest`-nek nincs egyetlen `placed_part`-ja sem (elméleti eset) → a lap üres háttér-téglalapként jelenik meg, hibaüzenet nélkül.

## 8. Kapcsolódó komponensek és Domain Model fogalmak

* **Nesting Engine** — a bemeneti `Nest`-ek forrása.
* **DXF Export Engine** — a preview vizuálisan tükrözi, amit ez exportálna, de nem hívja meg és nem függ tőle futásidőben.
* **`MainWindow`/`PreviewPanel`** (GUI réteg) — a `_last_nests` adat és a nézet-váltó gomb hostja.
* Domain Model: Nest, Placed Part (szeletkontúr-elhelyezés), Numbering-azonosító.

## 9. Nyitott kérdések

Nincs megválaszolatlan pont.

## 10. Elfogadási kritériumok

* A specifikáció mind a 10 szakaszt hiánytalanul tartalmazza.
* A 3D/2D váltás elérhetősége (csak sikeres Futtatás után) és az adatforrás (`_last_nests`, nincs új domain-számítás) egyértelműen rögzített.
* A lap fizikai mérete (anyag szélesség/magasság) mint háttér-referencia egyértelműen rögzített.
* A lapok navigációjának determinisztikus sorrendje (anyag, majd laponkénti sorszám) rögzített.
* A nagyítás/mozgatás viselkedése és a nagyítási tartomány paraméterezett.
* A Hibakezelés szakasz egyértelműen jelzi: nincs domain-szintű hibaeset, kizárólag GUI-állapot.
