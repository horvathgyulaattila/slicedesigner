# ADR-0007: Kontúr körüljárási irány mint szolid/lyuk megkülönböztetés

Dátum: 2026-08-03
Státusz: Elfogadva
Döntéshozó: Horváth Gyula Attila (projektgazda)

## Kontextus

A `DOWEL_SYSTEM_SPEC.md` 4. szakasza a Slice Engine "1 vagy több zárt kontúr" kimenetét pontosítva jelezte, hogy a kontúrok szolid anyag vagy kivágott lyuk közötti megkülönböztetésének pontos technikai konvenciója Phase 4 implementációs döntés. Ez a döntés a Dowel Engine implementációs promptjában született meg, de azóta minden további, geometriával dolgozó engine (Gap, Backplate, Numbering, Nesting, DXF Export) erre a konvencióra épül — a `slice_engine.py` `is_ccw()`/`reconstruct_islands()` publikus segédfüggvényein keresztül.

## Döntés

Egy zárt kontúr (`Contour.points`) körüljárási iránya hordozza a jelentést:

* **Óramutató járásával ellentétes (CCW)** = szilárd anyag (sziget) határa.
* **Óramutató járásával megegyező (CW)** = kivágott lyuk határa.

A körüljárási irányt minden kontúr-előállító helyen (Slice Engine `create_slice_set()`, Dowel Engine `_circle_contour_cw()`, Backplate Engine csap-protrúzió, Nesting Engine `_geometry_to_contours()`) explicit módon kikényszerítjük (a `shapely.geometry.polygon.orient()` segítségével), nem a felhasznált geometriai könyvtár (Shapely/trimesh) alapértelmezett, dokumentálatlan konvenciójára hagyatkozva.

Egy szigeten belül a hozzá tartozó lyukak point-in-polygon teszttel (`Polygon.contains()`) kerülnek hozzárendelve a megfelelő szolid határhoz (`reconstruct_islands()`, `slice_engine.py`).

## Mérlegelt alternatívák

* **A geometriai könyvtár saját, alapértelmezett körüljárási konvenciójára hagyatkozás** — elvetve: nem dokumentált, verzió- és bemenetfüggő lehet, sértené a CODING_STANDARDS.md 7. szakaszának (Determinizmus) "nincs kikényszerített, implicit sorrendfüggés" elvét.
* **Külön, explicit `is_hole: bool` mező a `Contour`-on** — elvetve: redundáns adatot vezetne be (a körüljárási irányból már levezethető), és nem védene a kontúr esetleges utólagos, közvetlen pontlista-manipulációjából fakadó inkonzisztenciától úgy, mint egy egységesen kikényszerített geometriai invariáns.

## Következmények

* Minden geometriát előállító/módosító kód felelőssége a CCW/CW invariáns fenntartása — ezt a `ruff`/`mypy` nem tudja automatikusan ellenőrizni, kizárólag a tesztek (pl. a Slice Engine teszt-készletében található, előjeles terület alapú ellenőrzések).
* A `DOWEL_SYSTEM_SPEC.md` 4. szakaszában jelzett nyitott pont ezzel lezárva.
* Jövőbeli, geometriával dolgozó engine-eknek ugyanezt a konvenciót kell követniük, hacsak egy külön ADR másként nem dönt.
