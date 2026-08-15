# ADR-0013: Nesting Engine — valódi alak (true-shape) szerinti csomagolás bevezetése

Dátum: 2026-08-13
Státusz: Elfogadva
Döntéshozó: Horváth Gyula Attila (projektgazda)

## Kontextus

Az ADR-0008 (2026-08-03) a Nesting Engine tényleges csomagolási algoritmusaként a tengelyfüggő befoglaló téglalap alapú, polc-alapú (shelf) heurisztikát rögzítette, tudatos eltérésként a `NESTING_SPEC.md` 6. szakaszának szó szerinti "valódi alak (true-shape) szerinti elrendezés" megfogalmazásától — Engineering Principles, Egyszerűség hivatkozással, egy teljes no-fit-polygon (NFP) alapú megoldás aránytalanul nagy komplexitására hivatkozva.

A projektgazda a ROADMAP Phase 7 megnyitásakor (l. ROADMAP.md, "folytatás 14" megjegyzés) újranyitotta ezt a döntést: a gyakorlati használat során a befoglaló-téglalap alapú elrendezés elégtelennek bizonyult ("hiába, hogy jóváhagyott döntés volt, de nem sok értelme van így a nestingnek — kézzel kell utólag elrendezni a darabokat"), és — a nagyobb implementációs ráfordítás tudatában, azt vállalva — a valódi alak szerinti elrendezés bevezetését kérte. Ez pontosan az az eset, amit maga az ADR-0008 "Következmények" szakasza előre jelzett: "ha a gyakorlati használat során a kihasználtság elégtelennek bizonyul, egy finomabb algoritmus bevezetése külön Döntési javaslat és Hatásvizsgálat tárgya lesz."

Fontos, hogy a `NESTING_SPEC.md` maga **soha nem változott** — a specifikáció mindvégig a jelen ADR-ben bevezetett célállapotot írta elő; kizárólag az ADR-0008-ban dokumentált, tudatos implementációs eltérés szűnik meg.

## Döntés

A Nesting Engine csomagolási algoritmusa **Bottom-Left Fill (BLF) heurisztikára** vált, **valódi Shapely-poligon ütközésteszttel** — nem teljes no-fit-polygon (NFP) alapú optimalizálásra. Ez egy tudatosan vállalt köztes megoldás: genuinely true-shape (a tényleges alkatrész-kontúr, nem a befoglaló téglalapja számít az illesztésnél), de nem ipari-optimalitású.

**Az algoritmus, anyagcsoportonként/laponként:**

1. Az alkatrészek terület szerint csökkenő sorrendbe kerülnek (a korábbi, magasság szerint csökkenő sorrend helyett — a bin-packing egyik legjobban bevált, elterjedt heurisztikája).
2. Minden alkatrészhez, a `nesting_rotation_mode` szerinti szögkészletből (l. lent) sorban, az elsőként **illeszkedő** (szög, pozíció) párt fogadja el a rendszer — nem a "legjobbat" a teljes készletből.
3. Egy adott szöghöz tartozó jelölt pozíciók: a lapon már elhelyezett alkatrészek (elforgatott) befoglaló téglalapjainak sarokpontjaiból képzett rács, plusz a lap (0, 0) sarka — nem egy tetszőlegesen választott felbontású, önálló raszter. A jelölt pozíciók a "legalsó, azon belül legbaloldalibb" (bottom-left) sorrendben kerülnek kiértékelésre.
4. Egy jelölt pozíció **érvényes**, ha az adott szöggel elforgatott alkatrész-geometria (a) teljes egészében a lap határain belül esik, ÉS (b) minden már elhelyezett alkatrész-geometriától legalább `kerf_mm` távolságra van (Shapely `distance()` — nem befoglaló téglalap-alapú, hanem a tényleges kontúrok közötti legkisebb távolság).
5. Ha egyetlen szög egyetlen jelölt pozíciója sem érvényes az aktuális lapon, egy új lap nyílik (nyitott végű lapszám, mint eddig).
6. Ha egy alkatrész (a Phase 6-ban már meglévő, toldást kiváltó felosztás után is) egyetlen szögben, egyetlen üres lapon sem fér el → `InvalidNestingError` (változatlan hibakezelési szerződés).

**Forgatási módok, szögkészletként értelmezve** (a korábbi, "egyetlen előre kiszámított legjobb orientáció" heurisztika helyett — az mostantól nem konzisztens azzal, hogy a pozicionálás true-shape alapú):

| `nesting_rotation_mode` | Kipróbált szögek |
|---|---|
| `none` | `{0°}` |
| `orthogonal` | `{0°, 90°}` |
| `free` | `{0°, 45°, 90°, 135°, 180°, 225°, 270°, 315°}` |

A szögek kipróbálási sorrendje maga is a felsorolás sorrendje — determinisztikus, nincs véletlenszerűség vagy halmaz-alapú (sorrend nélküli) bejárás.

**A `NESTING_SPEC.md` NEM módosul** — a specifikáció szövege (6. szakasz, 6. lépés) mindvégig ezt az állapotot írta elő; a jelen ADR kizárólag az implementációt hozza összhangba vele. Az ADR-0008 `Státusz` mezője erre az ADR-ra hivatkozva `Felváltva — ld. ADR-0013`-ra frissül; maga az ADR-0008 dokumentum tartalma egyébként (történeti feljegyzésként) változatlan marad.

## Mérlegelt alternatívák

* **Teljes no-fit-polygon (NFP) alapú algoritmus** — elvetve: a projektgazdával lezajlott egyeztetés során is megerősítve, hogy a jelentősen nagyobb implementációs/karbantartási teher (pontos NFP-számítás konkáv poligonokra, párhuzamos elforgatás-optimalizálás) nem áll arányban a hobby-célú eszköz méretével — az Engineering Principles Egyszerűség-elve továbbra is érvényes indok, csak a "hol húzzuk meg a határt" tolódott el.
* **Finomabb szögfelbontás (pl. 15° vagy 5°)** — elvetve/elhalasztva: a projektgazdával lezajlott egyeztetés szerint a kontúr-alapú pozicionálás (a befoglaló téglalap lecserélése) adja a kihasználtság-javulás nagy részét; a szögfelbontás finomítása csökkenő hozamú, és a keresési költséget a felbontással arányosan növeli (45°-nál nagyságrendileg 8×, 15°-nál 24× szorzó a tiszta pozicionáláshoz képest) — 45° jó középút, a durvább felbontásnál elérhető haszon jó részét megtartja, lényegesen kisebb költséggel.
* **"Legjobb" (szög, pozíció) pár kiválasztása minden szög/pozíció kiértékelése után, nem az első illeszkedő elfogadása** — elvetve: a projektgazda kifejezetten az első-illeszkedő megoldást választotta; a "legjobb" definiálása (pl. felhasznált lapterület, origótól vett távolság) önálló tervezési kérdés lenne, ami nélkül nem is értelmezhető egyértelműen — az első-illeszkedő megoldás egyértelmű, determinisztikus, és nem zárja ki, hogy egy jövőbeli kör finomítsa.
* **Külső nesting-könyvtár bevonása** — továbbra is elvetve, változatlan indokkal (ADR-0008).

## Következmények

* **Teljesítmény:** az algoritmus a lapon lévő alkatrészek számával **négyzetes-köbös nagyságrendben lassulhat** (minden új alkatrészhez minden korábbi elhelyezetthez képest ütközésvizsgálat, minden jelölt pozíción, minden szögön) — sok (több tucat–száz) alkatrészt tartalmazó lapoknál ez érezhető Futtatás-idő-növekedést okozhat a korábbi, O(n log n) polc-csomagoláshoz képest. A Nesting a `_PipelineWorker` háttérszálon fut (ADR-0009 kontextusában bevezetett minta), ezért ez NEM fagyasztja a GUI-t, csak a Futtatás végeredményének megjelenéséig eltelő időt növelheti. **Backlog-jelölt:** ha a gyakorlati használat során ez problémának bizonyul, egy hatékonyabb jelölt-pozíció-generálás (pl. térbeli indexeléssel) külön Döntési javaslat tárgya lesz.
* A meglévő tesztek egy része (pl. a pontos, elvárt `PlacedPart.position`-értékeket ellenőrző esetek) a konkrét elhelyezési koordináták megváltozása miatt frissítésre szorul — ez a tényleges implementációs prompt tárgya, nem ennek az ADR-nek.
* A `Nest`/`PlacedPart`/`MaterialDefinition` adatszerkezetek, a publikus `create_nests()` szignatúra és a `NESTING_SPEC.md` Kimenet-szerződése (4. szakasz) változatlan — kizárólag a belső elrendezési algoritmus cserélődik.
* Az ADR-0008 `Státusz` mezője `Felváltva — ld. ADR-0013`-ra módosul; a `docs/ARCHITECTURE.md` 5. szakaszának ADR-0008-ra hivatkozó sora, valamint egy új sor ADR-0013-hoz, ennek megfelelően frissül.
