# Projekt Struktúra

Státusz: Piszkozat
Tulajdonos:
Létrehozva: 2026-07-30
Utolsó módosítás: 2026-08-01
Kapcsolódó dokumentumok: [PROJECT_CONSTITUTION.md](PROJECT_CONSTITUTION.md), [ARCHITECTURE.md](ARCHITECTURE.md), [README.md](../README.md)

## Cél

Ez a dokumentum leírja a Slice Designer könyvtárszerkezetét, és elmagyarázza, hogy az egyes mappák miért léteznek.

## 1. A könyvtárszerkezet áttekintése

```
slicedesigner/                    # repo gyökér
├── src/
│   └── slicedesigner/            # a Python csomag (import: slicedesigner)
│       ├── engines/               # Domain réteg — 8 engine
│       ├── project/               # Koordinációs réteg
│       └── gui/                   # Prezentációs réteg (PySide)
├── tests/                         # a src/ struktúráját tükrözi
├── examples/                      # minta STL-ek, minta mentett Project-ek
├── assets/                        # GUI ikonok, statikus erőforrások
├── docs/
│   ├── adr/                       # architekturális döntések
│   └── specifications/            # Phase 2 funkcionális specifikációk
├── README.md
└── pyproject.toml                 # Python csomag-manifeszt
```

## 2. `docs/` – dokumentáció

A projekt teljes tervezési és döntési dokumentációja. Minden dokumentum a jelen fájlban rögzített szerkezetet követi (fejléc metaadatok, majd tartalom). A `docs/`-ban lévő fájlok az egyetlen hivatalos igazságforrás (Constitution 2. elv).

## 3. `docs/adr/` – architekturális döntési dokumentumok

Minden jelentős, alternatívák közötti architekturális döntés itt kerül rögzítésre. Elnevezési konvenció (a már létrehozott ADR-0001 mintáját követve): `NNNN-rövid-kebab-case-cím.md`, négyjegyű, nullákkal kitöltött sorszámmal, időrendi sorrendben.

## 4. `docs/specifications/` – részletes specifikációk

A ROADMAP Phase 2 (Functional Specifications) alatt készülő, egy-egy engine-hez tartozó specifikációk helye — egy fájl / fő funkció (Slice Engine, Gap System, Dowel System, Backplate, Numbering, Nesting, DXF Export). Elnevezési konvenció: a meglévő dokumentumstílust követő `NAGYBETŰS_ALÁHÚZÁSOS.md` (pl. `SLICE_ENGINE_SPEC.md`). A pontos tartalmi sablon a Phase 2 megkezdésekor, a `PROMPT_STANDARD.md` mintájára készül majd.

## 5. `src/` – alkalmazáskód

A `src/slicedesigner/` a telepíthető Python csomag gyökere (src-layout — elkerüli a véletlen helyi importot teszteléskor). Almappái az Architecture három rétegét tükrözik:

* **`engines/`** — a 8 domain engine, egy modul / engine: `mesh_import.py`, `slice_engine.py`, `gap_engine.py`, `dowel_engine.py`, `backplate_engine.py`, `numbering_engine.py`, `nesting_engine.py`, `dxf_export_engine.py`.
* **`project/`** — a koordinációs réteg: a Project állapota, pipeline-vezérlés, mentés/betöltés.
* **`gui/`** — a PySide-alapú prezentációs réteg. Belső felbontása (ablakok, widgetek) a Phase 5 (Integration) megkezdésekor kerül kidolgozásra — itt csak a csomag helyét rögzítjük.

## 6. `tests/` – tesztek

A `src/slicedesigner/` struktúráját tükrözi (`tests/engines/`, `tests/project/`, `tests/gui/`), egy teszt-modul / forrás-modul. A konkrét tesztelési keretrendszer és konvenciók a `CODING_STANDARDS.md` "Tesztelés" fejezetében kerülnek rögzítésre.

## 7. `examples/` – példák

Minta STL-modellek és minta mentett Project-fájlok, amelyek manuális teszteléshez és bemutatáshoz használhatók. Tartalma a Phase 4 (Implementation) előrehaladtával bővül.

## 8. `assets/` – statikus erőforrások

A GUI-hoz tartozó statikus fájlok (ikonok, stílusok). Nem tartalmaz logikát vagy konfigurációt.

## 9. Konvenciók új fájlok/mappák hozzáadásához

* Új domain fogalom → először a `DOMAIN_MODEL.md`-ben rögzítendő, csak utána kaphat kódbeli megfelelőt.
* Új engine → a `docs/specifications/` alatt specifikáció, majd az `ARCHITECTURE.md` 2. szakaszának bővítése, csak ezután `src/slicedesigner/engines/` alatt modul.
* Új architekturális döntés → ADR a `docs/adr/` alatt, a fenti névkonvenció szerint.
* Fájlnevek: a `docs/` gyökerében NAGYBETŰS_ALÁHÚZÁSOS séma; a Python kódban `snake_case` (PEP 8).
