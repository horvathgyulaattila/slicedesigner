# ADR-0006: Build backend és a Domain réteg alapkönyvtárai

Dátum: 2026-08-02
Státusz: Elfogadva
Döntéshozó: Horváth Gyula Attila (projektgazda)

## Kontextus

Az ADR-0001 rögzítette a Python + PySide implementációs alapot, de nem foglalkozott a `pyproject.toml` build-rendszerével, a csomagkezelő/munkafolyamat-eszközzel, sem a Mesh Import és a DXF Export specifikációk (MESH_IMPORT_SPEC.md, SLICE_ENGINE_SPEC.md, DXF_EXPORT_SPEC.md) implementálásához szükséges konkrét geometriai és fájlformátum-könyvtárakkal. A Phase 4 (Implementation) tényleges megkezdése előtt ezeket rögzíteni kell, hogy a `pyproject.toml` és a hozzá tartozó eszközkonfiguráció (CODING_STANDARDS.md 1., 2., 4. szakasza: ruff, mypy, pytest) elkészülhessen.

## Döntés

* **Build backend / munkafolyamat-eszköz:** `uv` mint csomagkezelő és munkafolyamat-eszköz (virtuális környezet, függőségtelepítés, lockfile), a `[build-system]` tényleges backendje `hatchling` — az `uv` saját alapértelmezett párosítása.
* **Minimum Python-verzió:** 3.11.
* **Mesh-kezelő könyvtár:** `trimesh` — az STL beolvasáshoz (ASCII és bináris, automatikus felismeréssel), a nem-manifold/nem-vízzáró ellenőrzéshez, valamint a Slice Engine sík-menti keresztmetszet-előállításához (`section()`).
* **GUI-keretrendszer konkrét kiadása:** `PySide6` (az ADR-0001 "PySide" megnevezésének pontosítása).
* **DXF-író könyvtár:** `ezdxf`.

## Mérlegelt alternatívák

**Build backend:**

* `setuptools` — a legkonzervatívabb, de src-layout mellett verbózabb konfiguráció, és nincs natív lockfile.
* `hatchling` (önmagában, uv nélkül) — minimális konfig, de a reprodukálható fejlesztői környezethez külön eszköz kellene.
* `Poetry` — teljes csomagkezelés, de saját, nehezebb gépezet (resolver, CLI, publikálási funkciók), amelyekre egy nem publikált, saját célú eszköznél (PROJECT_VISION.md 2. szakasz) nincs szükség — ellentétben állna az Engineering Principles Egyszerűség elvével.
* `uv` + `hatchling` — *választott*: ugyanaz a fejlesztői műhely (Astral), mint a már kötelező `ruff`, natív lockfile-lal a reprodukálható környezethez, minimális konfiguráció.

**Mesh-kezelő könyvtár:**

* `numpy-stl` — minimális, csak STL I/O; a watertight-ellenőrzést és a sík-menti metszésszámítást (SLICE_ENGINE_SPEC.md 6. szakasz, 7. lépés) teljes egészében saját kódban kellene megvalósítani.
* `meshio` — formátum-agnosztikus I/O, de geometriai műveletek nélkül, ugyanaz a hiányosság.
* `trimesh` — *választott*: az ADR-0001 már "trimesh-szerű mesh-kezelést" nevezett meg indoklásként; natívan biztosítja az STL I/O-t, a watertight-ellenőrzést és a sík-menti keresztmetszet-előállítást, amivel a Mesh Import és a Slice Engine specifikáció kulcsfunkciói készen elérhetők.

## Következmények

* A `pyproject.toml` a fenti döntéseknek megfelelő `[build-system]` és függőség-deklarációkat tartalmazza.
* A `docs/ARCHITECTURE.md` 5. szakasza kiegészül egy erre az ADR-re mutató hivatkozással.
* A `docs/CODING_STANDARDS.md` egy új, 7. szakasszal egészül ki a determinizmus Python-specifikus részleteiről (hash randomization, lebegőpontos pontosság) — ezt az ADR-0001 "Következmények" szakasza már előre jelezte, eddig nem valósult meg.
* Jövőbeli specifikációk implementációja esetén, ha a `trimesh` vagy `ezdxf` funkciói nem elegendők egy adott feladatra, azt külön ADR-ben kell rögzíteni.
* Nincs érintett korábbi forráskód (Phase 4 kódja e feladat előtt nem létezett).

## Frissítés (2026-08-03)

A Phase 4 előrehaladtával az eredeti döntés (geometriai alapkönyvtárak) természetes bővüléseként további, közvetlen függőségek kerültek a `pyproject.toml`-ba — mindegyik a már itt rögzített `trimesh` funkcióinak kiegészítéseként, saját, célzott indoklással a bevezetésük idején (Dowel/Gap/Backplate/Numbering/Nesting Engine promptjai):

* `numpy` — a `trimesh` által visszaadott tömbök API-jának közvetlen, explicit függőségként rögzítve (Slice Engine).
* `shapely` — 2D poligon-műveletek (unió, metszet, körüljárási irány kikényszerítése) — a Slice Engine `section()`-alapú keresztmetszet-előállításának természetes kiegészítése.
* `scipy`, `networkx` — a `trimesh` `section_multiplane()`/`Path2D.is_closed` opcionális, futásidejű függőségei, célzottan hozzáadva a `trimesh[easy]` extra helyett (Slice/Dowel Engine).

Ez a döntés (geometriai ökoszisztéma választása) tartalmilag nem változott — csak a ténylegesen szükséges könyvtárak listája vált konkréttá, ahogy az implementáció haladt.
