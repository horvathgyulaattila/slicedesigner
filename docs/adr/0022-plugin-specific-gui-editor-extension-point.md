# ADR-0022: Plugin-specifikus GUI-szerkesztő extension point (`ParameterSpec.editor`)

Dátum: 2026-09-04
Státusz: Elfogadva
Döntéshozó: Horváth Gyula Attila (projektgazda)

## Kontextus

A ROADMAP Phase 13.9 (Interaktív GUI a régió-hozzárendeléshez) megkövetel egy módot, ahogy egy `MeshSource` plugin (Image Relief Generator) egy saját, összetett, domain-specifikus GUI-szerkesztőt (`RegionAssignmentDialog`) ajánlhat fel egy `"file"` típusú `ParameterSpec` mezőjéhez (`assignment_path`) — a `"Tallózás..."` gomb mellett egy `"Szerkesztés..."` gombként.

Két megközelítés merült fel:

**(1) `"custom"` `ParameterType` + `ParameterSpec.widget_factory: Callable[[], tuple[QWidget, Callable[[], Any]]]`.** Ez a plugintól kapott, tetszőleges `QWidget`-et közvetlenül beágyazná a core form-builderébe. Elvetve — l. "Mérlegelt alternatívák".

**(2) Egy szélesebb, `MeshSourceDescriptor`-szintű `actions` lista** (tetszőleges számú, plugin-definiált GUI-művelet). Elvetve, túl általános egy jelenleg pontosan egyetlen, validált használati esethez képest.

## Döntés

**1.** `ParameterSpec` egy új, opcionális mezőt kap:

```python
editor: Callable[[dict[str, Any]], str | None] | None = None
```

Kizárólag `"file"` típusú `ParameterSpec`-nél értelmezett. A callable a form **jelenlegi** `values()`-ét kapja (így pl. hozzáfér a már kitöltött `image_path`-hoz), és egy útvonalat ad vissza — vagy `None`-t, ha a felhasználó megszakította, vagy a plugin egy előfeltétel hiányában (pl. üres `image_path`) elutasította a szerkesztést.

**2.** A core form-builder (`_GeneratorParameterForm._build_widget`, `parameter_panel.py`) a `"file"` ágban, ha `spec.editor is not None`, egy második gombot (`"Szerkesztés..."`) ad a meglévő `_build_file_picker` konténeréhez. Kattintáskor `spec.editor(self.values())`-t hív; nem-`None` válasz esetén a `path_label` szövege frissül — pontosan úgy, mint sikeres `"Tallózás..."` után.

**3.** A core (`mesh_source_registry.py`, `parameter_panel.py`) **egyetlen Qt-import nélkül** fogadja be ezt a mezőt — a callable szignatúrája tiszta Python (`dict[str, Any] -> str | None`), pontosan a meglévő `MeshSourceDescriptor.build: Callable[[dict[str, Any]], Any]` mintáját követve, ami szintén nem árulja el, mi történik a hívás belsejében.

**4.** A plugin (`image_relief_generator_registration.py`) az `assignment_path` `ParameterSpec`-hez ad `editor=`-t, egy saját, kicsi függvényt, ami megnyitja a `RegionAssignmentDialog`-ot (`plugins/relief_generator/gui/region_assignment_dialog.py`, ez a prompt hozza létre) és visszaadja az eredményt.

**5.** Ez a plugin **első, közvetlen PySide6-függősége** (`plugins/relief_generator/pyproject.toml` bővül) — eddig kizárólag Pillow volt. Ez nem sérti az ADR-0015/0016 egyirányú szabályát (az a `slicedesigner.*` core-internal modulok importját tiltja, nem harmadik féltől való Qt-t), de új függőségtípus, amit itt explicit megnevezünk. Ebből **egyenesen következik** egy másik, ugyanide tartozó szabály: a plugin GUI-kódja (`region_assignment_dialog.py`) sem importálhat `slicedesigner.gui.*` core-internal modult — a zoom/pan-technikát (`_NestingGraphicsView` mintája) önálló, plugin-belső kódként tükrözi, nem osztja meg.

## Mérlegelt alternatívák

- **`"custom"` `ParameterType` + `widget_factory`** — elvetve. A `mesh_source_registry.py` modul-docstringje explicit kimondja: "a core sosem szembesül plugin-specifikus fogalommal — kizárólag az itt rögzített, generikus típusokkal dolgozik". Egy plugintól kapott, a core számára átlátszatlan `QWidget` közvetlen beágyazása minőségi váltás lenne: a `ParameterSpec` többé nem "milyen adatot kell bekérni", hanem "milyen GUI-komponenst futtass a plugin kódjából" kérdésre válaszolna — és közvetlenül Qt-típust vinne be a jelenleg teljesen Qt-mentes core szerződésbe (`mesh_source_registry.py`).
- **Szélesebb, `MeshSourceDescriptor.actions` lista** — mérlegelve, elvetve. Jelenleg pontosan egy validált használati esetünk van (`assignment_path` szerkesztése); egy általános "plugin action" lista validált szükséglet nélkül korai absztrakció lenne, és könnyen egy általános GUI-plugin-framework első lépésévé válhatna — amit az ADR-0017 már korábban, szándékosan elkerült.

## Következmények

- `src/slicedesigner/project/mesh_source_registry.py`: `ParameterSpec.editor` új mező.
- `src/slicedesigner/gui/parameter_panel.py`: `"Szerkesztés..."` gomb, csak ha `spec.editor is not None`.
- `plugins/relief_generator/gui/region_assignment_dialog.py` (új): `RegionAssignmentDialog`.
- `plugins/relief_generator/source/image_relief_generator_registration.py`: `assignment_path` `ParameterSpec` `editor=`-t kap.
- `plugins/relief_generator/pyproject.toml`: új, közvetlen PySide6-függőség.
- `plugins/relief_generator/domain/image_interpretation_blob.py` (13.9/1. rész, Elfogadva): `_flood_fill` → publikus `flood_fill_region` — l. 2.6 szakasz (a fő promptban).
