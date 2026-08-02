# ADR-0004: Opcionális összeépítési mechanizmusok (Spacer / Dowel / Backplate)

Dátum: 2026-08-01
Státusz: Elfogadva
Döntéshozó: Horváth Gyula Attila (projektgazda)

## Kontextus

A GAP_SYSTEM_SPEC.md kidolgozása során merült fel, hogy egyes projekteknél (pl. 2,5D modell, Backplate-hez rögzített szeletekkel) nincs szükség Spacer-ekre — a jelenlegi ARCHITECTURE.md pipeline viszont feltétel nélküli: minden engine, így a Gap Engine, Dowel Engine és Backplate Engine is, mindig lefut. Ez nem teszi lehetővé, hogy egy adott projekt csak a számára releváns összeépítési mechanizmusokat használja.

## Döntés

Három, egymástól független, Project-szintű kapcsoló kerül bevezetésre: `use_spacers`, `use_dowels`, `use_backplate`. A Project ezek alapján dönti el, lefuttatja-e a Gap Engine-t, a Dowel Engine-t, illetve a Backplate Engine-t — kikapcsolt kapcsoló esetén az adott engine nem fut le, kimenete üres. A Project a pipeline indítása előtt egyetlen, konfiguráció-teljességi előfeltételt ellenőriz: a három kapcsoló közül legalább egynek bekapcsoltnak kell lennie, különben hiba. Ez nem geometriai vagy üzleti döntés, csak alapvető konfiguráció-ellenőrzés — összhangban azzal, hogy a Project "nem tartalmaz geometriai vagy üzleti logikát, kizárólag koordinál" (ARCHITECTURE.md, Project).

A kapcsoló-kombinációk finomabb, kontextus-függő (geometria-alapú) redundancia-vizsgálata jelenleg nem kerül bevezetésre.

## Mérlegelt alternatívák

* **Mindig minden engine lefut** (jelenlegi/eredeti architektúra) — egyszerűbb, de felesleges alkatrészeket (pl. Spacer Backplate-es projektnél) eredményezhet, és nem felel meg a projektgazda tervezési szándékának.
* **Engine-enkénti kontextus-függő figyelmeztetés** a kapcsoló-kombinációkról — elvetve: a vizsgált eset (Backplate + Spacer együtt) megmutatta, hogy nincs egyszerű, statikus szabály; ehhez geometria-függő elemzés kellene, ami jelentősen bővítené a hatókört egy olyan pontban, ami jelenleg nem prioritás.
* **Három független kapcsoló + feltételes engine-futtatás, egyetlen konfiguráció-teljességi szabállyal** (*választott*) — egyszerű, a projektgazda tervezési szándékát (2,5D Backplate-es eset Spacer nélkül) közvetlenül lehetővé teszi, és nem igényel geometria-függő logikát.

## Következmények

* A `DOMAIN_MODEL.md` Project fogalmának attribútumai kiegészülnek a három kapcsolóval.
* Az `ARCHITECTURE.md` 4. szakasza (Komponensek közötti felelősségmegosztás) kiegészül a feltételes engine-futtatás és a konfiguráció-teljességi ellenőrzés leírásával.
* A `GAP_SYSTEM_SPEC.md` (még jóváhagyás előtt álló Phase 2 specifikáció) Bemenet/Viselkedés szakaszát a `use_spacers` kapcsoló figyelembevételével kell újrafogalmazni.
* A jövőbeli `DOWEL_SYSTEM_SPEC.md` és `BACKPLATE_SPEC.md` specifikációknak hasonlóan figyelembe kell venniük a saját kapcsolójukat (`use_dowels`, `use_backplate`).
* Nincs érintett forráskód (Phase 4 még nem kezdődött el).
