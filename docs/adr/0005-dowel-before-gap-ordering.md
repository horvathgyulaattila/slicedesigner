# ADR-0005: Pipeline-sorrend csere — Dowel Engine a Gap Engine elé kerül

Dátum: 2026-08-01
Státusz: Elfogadva
Döntéshozó: Horváth Gyula Attila (projektgazda)

## Kontextus

A DOWEL_SYSTEM_SPEC.md kidolgozása során derült ki, hogy a Dowelnek át kell mennie a Spacereken is, hogy azokat a helyükön tartsa, és hogy a Dowel pozícióinak meghatározása a modell geometriájától függ (annyi szeleten megy át, amennyin csak lehet, anélkül, hogy kifutna a modell külső palástján). A jelenlegi pipeline-sorrend (Mesh Import → Slice Engine → Gap Engine → Dowel Engine → ...) ezt fordítva kényszerítené: a Gap Engine már a Dowel Engine előtt elhelyezné a Spacereket, így azok nem tudnának a Dowel pozícióihoz igazodni.

A projektgazda megerősítette: a Dowel legyen az elsődleges illesztési mechanizmus, a Spacer ehhez igazodjon, nem fordítva.

## Döntés

A pipeline sorrendje megváltozik:

Mesh Import → Slice Engine → Dowel Engine → Gap Engine → Backplate Engine → Numbering Engine → Nesting Engine → DXF Export Engine

A Dowel Engine a Slice Engine kimenete (a pozicionált Slice Set) alapján, önállóan határozza meg a Dowel és Dowel Hole pozícióit — a modell külső palástján belül maradva, a Gap Engine (és így a Spacer) ismerete nélkül. A Gap Engine ezután a Spacereket a már meghatározott Dowel-pozíciók figyelembevételével és előnyben részesítésével helyezi el: ahol lehetséges, a Spacer a Dowel pozíciójára kerül, és csak ott generál önálló pozíciót, ahol a Dowel-pozíciók nem elegendők a Spacer-hez elvárt célszámhoz.

## Mérlegelt alternatívák

* **Gap Engine előbb fut, a Dowel Engine igazodik a Spacer-pozíciókhoz** (eredeti sorrend) — elvetve, mert logikailag fordított: a Dowel pozícióját a modell geometriája (hol fér át a legtöbb szeleten) határozza meg, nem a Spacer elhelyezése.
* **A két engine teljesen független marad, egymástól függetlenül helyezi el a saját elemeit** — elvetve, mert nem biztosítaná, hogy a Dowel ténylegesen áthaladjon a Spacereken, ahogy a projektgazda tervezte.
* **Dowel Engine előbb fut, a Gap Engine hozzá igazodik** (*választott*) — a Dowel, mint elsődleges illesztési mechanizmus, önállóan, a modell geometriája alapján kerül elhelyezésre; a Spacer ehhez igazodik, ahol lehetséges.

## Következmények

* Az `ARCHITECTURE.md` 2. szakaszában a Dowel Engine és a Gap Engine leírásának sorrendje és tartalma frissül (Dowel Engine előbb, a Gap Engine Domain Model kapcsolata kiegészül a Dowel-lel).
* Az `ARCHITECTURE.md` 3. szakaszának pipeline-diagramja és szöveges leírása az új sorrendet tükrözi.
* Az `ARCHITECTURE.md` 5. szakasza kiegészül az ADR-0005-re mutató hivatkozással.
* A `DOMAIN_MODEL.md` "Fogalmi kapcsolatok" szakasza kiegészül egy új tétellel a Spacer-Dowel viszonyról.
* A már elfogadott `GAP_SYSTEM_SPEC.md`-t külön lépésben újra kell nyitni és módosítani, hogy a Dowel-pozíciók figyelembevételét tükrözze.
* A `DOWEL_SYSTEM_SPEC.md` ez alapján, önálló logikával (a Gap Engine kimenetétől függetlenül) készül.
* Nincs érintett forráskód (Phase 4 még nem kezdődött el).
