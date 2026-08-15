# Projekt Struktúra

Státusz: Elfogadva
Tulajdonos:
Létrehozva: 2026-07-30
Utolsó módosítás: 2026-08-15
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
├── plugins/                       # opcionális pluginok (pl. relief_generator/)
├── tests/                         # a src/ struktúráját tükrözi
├── examples/                      # minta STL-ek, minta mentett Project-ek
├── assets/                        # GUI ikonok, statikus erőforrások
├── docs/
│   ├── adr/                       # architekturális döntések
│   ├── specifications/            # Phase 2 funkcionális specifikációk
│   ├── drafts/                    # ideiglenes tervezetek
│   └── plugins/                   # plugin-specifikus dokumentáció
├── README.md
└── pyproject.toml                 # Python csomag-manifeszt
```

## 2. `docs/` – dokumentáció

A projekt teljes tervezési és döntési dokumentációja. Minden dokumentum a jelen fájlban rögzített szerkezetet követi (fejléc metaadatok, majd tartalom). A `docs/`-ban lévő fájlok az egyetlen hivatalos igazságforrás (Constitution 2. elv).

## 3. `docs/adr/` – architekturális döntési dokumentumok

Minden jelentős, alternatívák közötti architekturális döntés itt kerül rögzítésre. Elnevezési konvenció (a már létrehozott ADR-0001 mintáját követve): `NNNN-rövid-kebab-case-cím.md`, négyjegyű, nullákkal kitöltött sorszámmal, időrendi sorrendben.

## 4. `docs/specifications/` – részletes specifikációk

A ROADMAP Phase 2 (Functional Specifications) alatt készülő, egy-egy engine-hez tartozó specifikációk helye — egy fájl / fő funkció (Mesh Import, Slice Engine, Gap System, Dowel System, Backplate, Numbering, Nesting, DXF Export). Elnevezési konvenció: a meglévő dokumentumstílust követő `NAGYBETŰS_ALÁHÚZÁSOS.md` (pl. `SLICE_ENGINE_SPEC.md`). A pontos tartalmi sablont a `SPECIFICATION_STANDARD.md` rögzíti.

## 5. `src/` – alkalmazáskód

A `src/slicedesigner/` a telepíthető Python csomag gyökere (src-layout — elkerüli a véletlen helyi importot teszteléskor). Almappái az Architecture három rétegét tükrözik:

* **`engines/`** — a 8 domain engine, egy modul / engine: `mesh_import.py`, `slice_engine.py`, `gap_engine.py`, `dowel_engine.py`, `backplate_engine.py`, `numbering_engine.py`, `nesting_engine.py`, `dxf_export_engine.py`; valamint `exceptions.py` (a közös `SliceDesignerError`-alapú kivétel-hierarchia, CODING_STANDARDS.md 5. szakasz).
* **`project/`** — a koordinációs réteg: `pipeline.py` (Project állapota, pipeline-vezérlés), `persistence.py` (mentés/betöltés), `exceptions.py` (`PipelineConfigurationError`, a koordinációs réteg saját kivétele).
* **`gui/`** — a PySide6-alapú prezentációs réteg: `app.py` (belépési pont — `QApplication`/`MainWindow` indítása), `main_window.py` (fő ablak), `parameter_panel.py`, `run_panel.py`, `preview_panel.py` (3D előnézet), `render_geometry.py` (megjelenítési geometria-segédfüggvények), `config_builder.py`/`config_loader.py` (widget ↔ `PipelineConfig` leképezés), `app_settings.py` (alkalmazás-szintű alapértelmezések).

## 6. `tests/` – tesztek

A `src/slicedesigner/` struktúráját tükrözi (`tests/engines/`, `tests/project/`, `tests/gui/`), egy teszt-modul / forrás-modul. A konkrét tesztelési keretrendszer és konvenciók a `CODING_STANDARDS.md` "Tesztelés" fejezetében kerülnek rögzítésre.

## 7. `examples/` – példák

Minta STL-modellek és minta mentett Project-fájlok, amelyek manuális teszteléshez és bemutatáshoz használhatók. Négy, leíró nevű alkönyvtárra tagolva (ROADMAP Phase 6, 6.5–6.8 tétel):

* `basic_example/` — egyszerű 3D modell, minimális szeletelési beállítások; az alap workflow bemutatására.
* `complex_example/` — több szelet, Gap, Dowel, Numbering, Backplate és export együttes bemutatására.
* `nesting_example/` — több alkatrész, Nesting használata, gyártási elrendezés.
* `reference_project/` — egy reális, összetett modell teljes beállításkészlettel, bemeneti modellel, exportált eredményekkel és rövid leírással.

Minden alkönyvtár tartalma reprodukálható (Phase 6, 6.9 tétel).

## 8. `assets/` – statikus erőforrások

A GUI-hoz tartozó statikus fájlok (ikonok, stílusok). Nem tartalmaz logikát vagy konfigurációt.

## 9. `docs/drafts/` – ideiglenes tervezetek

A `docs/drafts/` egy adott, még nem véglegesített funkció vagy komponens (jellemzően egy plugin) kezdeti, közösen kialakított tervezési dokumentumainak ideiglenes gyűjtőhelye, témánként elkülönítve (pl. `docs/drafts/relief_generator_plugin/`).

**Az itt elhelyezett dokumentumok nem tekinthetők elfogadott specifikációnak vagy architekturális döntésnek**, függetlenül attól, hogy tartalmuk mennyire részletes vagy kész hatású. A `docs/` többi részével ellentétben a `docs/drafts/` alatti tartalom nem minősül hivatalos igazságforrásnak (Constitution 2. elv) — kizárólag a Szoftverarchitekt és a Projektgazda közös tervezési munkájának bemeneteként, illetve a végleges dokumentáció és a Claude Code-nak szánt promptok elkészítésének alapjaként szolgál.

Minden `docs/drafts/` alatti dokumentumnak tartalmaznia kell a `Státusz: Tervezet` fejlécmezőt.

**Kilépési szabály:** amint egy `docs/drafts/<téma>/` alatti tartalom a szokásos munkafolyamaton (Döntési javaslat → Hatásvizsgálat → Projektgazdai jóváhagyás → Dokumentáció módosítása) átment, a végleges tartalom a megfelelő végleges helyre kerül (pl. `docs/plugins/<plugin_neve>/`, `docs/adr/`, illetve a `DOMAIN_MODEL.md`/`ARCHITECTURE.md` megfelelő szakasza) — a `docs/drafts/<téma>/` mappa ezután törlésre kerül.

## 10. `docs/plugins/` – plugin-specifikus dokumentáció

A `docs/plugins/` az egyes opcionális SliceDesigner-pluginok véglegesített, elfogadott dokumentációjának gyűjtőhelye, pluginonként külön almappában (pl. `docs/plugins/relief_generator/`).

A `docs/plugins/<plugin_neve>/` alatti dokumentumok a `docs/` többi részével azonos módon hivatalos igazságforrásnak számítanak (Constitution 2. elv) — ezzel szemben a `docs/drafts/<téma>/` alatti tartalom (9. szakasz) nem az. Egy dokumentum a `docs/drafts/` alól a szokásos munkafolyamaton (Döntési javaslat → Hatásvizsgálat → Projektgazdai jóváhagyás → Dokumentáció módosítása) átesve kerül át a `docs/plugins/<plugin_neve>/` alá, `Tervezet` helyett `Elfogadva` státusszal.

A plugin core-tól független, saját architektúráját, domain modelljét és plugin-specifikus döntéseit ez a mappa tartalmazza — a core-t érintő architekturális döntések (pl. a `MeshSource` bővítési pont) továbbra is a `docs/adr/` és a projekt fő dokumentumaiban (`ARCHITECTURE.md`, `DOMAIN_MODEL.md`) maradnak.

## 11. `plugins/` – opcionális pluginok kódja

A `plugins/` a SliceDesigner opcionális, külön telepíthető pluginjainak forráskódját tartalmazza, pluginonként külön almappában (pl. `plugins/relief_generator/`), a `src/slicedesigner/` mellett, azzal azonos szinten a repo gyökerében.

A pluginok kizárólag a `MeshSource` contracton (ADR-0014) keresztül kapcsolódnak a core-hoz — a core nem függ egyetlen plugintól sem, és nem tartalmazhat plugin-specifikus logikát (pl. `if relief_generator_installed: ...`). A függőség iránya egyirányú: Plugin → Core, fordítva nem.

Egy plugin belső felépítése a saját domain-határait tükrözi (pl. `domain/`, `generators/`, `geometry/`, `mesh/`, `source/` — lásd a plugin saját dokumentációját a `docs/plugins/<plugin_neve>/` alatt).

A pluginok tesztjei a `tests/plugins/<plugin_neve>/` alatt kapnak helyet, a meglévő `tests/engines/`, `tests/project/`, `tests/gui/` mellett — a core tesztjeinek plugin nélkül is futniuk kell.

A repository-struktúra és a plugin-architektúra teljes indoklását és a mérlegelt alternatívákat az [ADR-0016](adr/0016-plugin-repository-structure.md) rögzíti.

## 12. Konvenciók új fájlok/mappák hozzáadásához

* Új domain fogalom → először a `DOMAIN_MODEL.md`-ben rögzítendő, csak utána kaphat kódbeli megfelelőt.
* Új engine → a `docs/specifications/` alatt specifikáció, majd az `ARCHITECTURE.md` 2. szakaszának bővítése, csak ezután `src/slicedesigner/engines/` alatt modul.
* Új architekturális döntés → ADR a `docs/adr/` alatt, a fenti névkonvenció szerint.
* Fájlnevek: a `docs/` gyökerében NAGYBETŰS_ALÁHÚZÁSOS séma; a Python kódban `snake_case` (PEP 8).
