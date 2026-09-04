# Image Relief Generator — Orchestration

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-09-03
Kapcsolódó dokumentumok: [IMAGE_RELIEF_RAW_MESH.md](IMAGE_RELIEF_RAW_MESH.md), [ADR-0017](../adr/0017-plugin-discovery-and-parameter-schema.md), [ADR-0020](../adr/0020-image-relief-raw-mesh-sampling-and-generator-independence.md), tervezési előzmény: `docs/drafts/image_relief_generator/IMAGE_RELIEF_GENERATOR_PLANNING.md` (16. szakasz, 17.8 tervezési lépés)

## Cél

Ez a dokumentum rögzíti az Orchestration réteg kontraktusát — a Semantic
World, a Relief World és a Geometry World komponenseinek összefűzését, és az
eredmény becsomagolását a `MeshSource` kontraktusba — a ROADMAP Phase 13.8
alfázis kimenete.

## 1. Kontextus és hatókör

```text
Region hierarchy (13.1-13.2)
  ↓
Region Resolver (13.3)
  ↓
EffectSpec[]
  ↓
Effect Processing (13.4, `combine`)
  ↓
Orchestration   ← ez a dokumentum
  ↓
GeometricSurface (13.6) → Raw Mesh (13.7) → core Mesh
```

Nem tárgya: az interaktív, GUI-alapú hozzárendelés (Phase 13.9, a jelenlegi
fájl-alapú mechanizmust váltja ki), az integrációs teszt (Phase 13.10).

## 2. Komponens-modell — MeshSource-adapter

Nincs külön, önálló "Orchestrator" domainfogalom — a felelősséget egy
MeshSource-adapter osztály viseli, a meglévő `ReliefGeneratorMeshSource`
precedense szerint:

```text
ImageReliefGeneratorParameters (carrier dataclass)
        ↓
ImageReliefGeneratorMeshSource.get_mesh()
├── interpret_assignment(image_path, assignment_path) → Region-erdő
│     (13.9: 'strategy' mező szerint interpret_image/interpret_image_blob)
├── resolve_regions(region_tree)                        → EffectSpec[]
├── PIL.Image.open(image_path).size                     → (image_width, image_height)
├── raw_relief(x_norm, y_norm) closure (l. 3. szakasz)
├── GeometricSurface(..., raw_relief=raw_relief)
├── GeometricSurfaceMeshGenerator().generate(surface, sampling_distance)
└── core Mesh(..., source_path=None)
```

## 3. A `raw_relief` closure — normalizált → kép-pixel-koordináta leképezés

```python
def raw_relief(x_norm: float, y_norm: float) -> float:
    px = x_norm * (image_width - 1)
    py = (1.0 - y_norm) * (image_height - 1)
    return combine(effect_specs, px, py)
```

A Raw Mesh normalizált mintapontjai a kép diszkrét pixel-rácsának
határpontjaihoz vannak leképezve — `x_norm=0 → px=0`, `x_norm=1 →
px=image_width−1`, közte lineárisan. **Az Y-tengely szándékosan
tükrözött**: `y_norm=0` (a fizikai modell kis-Y pereme) a kép
**utolsó** pixel-sorára (`py=image_height−1`, a kép alja), `y_norm=1`
(a modell nagy-Y pereme) a kép **első** pixel-sorára (`py=0`, a kép
teteje) képződik le — így a fizikai modell szabvány felülnézeti
tájolásában a kép teteje a modell nagy-Y ("távoli") pereméhez kerül,
megőrizve az emberi szemmel felismerhető, megszokott tájolást. A
leképezés folytonos marad, nem kerekít/csonkol pixelre; az egész-pixel
értelmezés a `Mask`-backend (`PixelSetMask.member`) belső döntése. A
pontos indoklást l. `ADR-0020` "Kiegészítés (2026-09-04)" szakasza (az
eredeti, 2026-09-03-i kiegészítés a pixel-index határkérdést — N vagy
N−1 — rögzítette, ez a mostani kiegészítés egy attól független, korábban
észre nem vett kérdést, a tengely-tájolást korrigálja).

## 4. Kép-dimenzió forrása

Az `interpret_image()` (13.2, Elfogadva) szerződése **nem** módosul — nem
adja vissza a kép méretét. Az Orchestration önállóan olvassa be
(`PIL.Image.open(image_path).size`), egy második, redundáns fájl-I/O árán —
ez tudatosan vállalt egyszerűsítés, nem nyúl hozzá egy már lezárt alfázis
kontraktusához.

## 5. Paraméterátadás

Az `ImageReliefGeneratorParameters` carrier dataclass (`image_path`,
`assignment_path`, öt fizikai paraméter, `sampling_distance`) a meglévő
`ParameterSpec`/`MeshSourceDescriptor` mechanizmuson (ADR-0017) keresztül
érkezik, a plugin saját `image_relief_generator_registration.py`
entry-pointján át, a meglévő `relief_generator` entry point mellett, azt nem
helyettesítve.

## 6. `"file"` `ParameterType`

Két kötelező fájl-paraméter (`image_path`, `assignment_path`) — a core GUI
form-builderje a már meglévő `_build_file_picker` segédfüggvényt használja
fel (ADR-0017 kiegészítés). Üres fájlválasztás esetén a `values()` üres
stringet ad — a validáció a `get_mesh()` szintjén, az `interpret_image()`
saját, meglévő fail-fast hibáján (`ImageInterpretationError`) keresztül
történik, külön mechanizmus nélkül.

## 7. Lifecycle és hibaterjesztés

A meglévő discovery-mechanizmus, a generikus form-builder és a
háttérszálas generálás (Phase 8 precedens) közvetlenül újrafelhasználható.
A downstream rétegek saját kivételei (`ImageInterpretationError`,
`RegionResolutionError`, `EffectProcessingConflictError`,
`GeometricSurfaceValueError`, `GeometricSurfaceMeshGenerationError`,
`MeshValidationError`) nem kerülnek újracsomagolásra, változatlanul
propagálnak a `get_mesh()`-ből.

**Kiegészítés (2026-09-04, ROADMAP Phase 13.9, 1. rész):** a fenti
`interpret_image()` hívás `interpret_assignment()`-re cserélődött — l.
`ADR-0021`, `docs/plugins/relief_generator/IMAGE_RELIEF_BLOB_INTERPRETATION.md`.
Ez egy vékony dispatch-réteg, ami a hozzárendelési fájl opcionális
`"strategy"` mezője alapján a változatlan, 13.2-es `interpret_image()`-hez
vagy az új, blob-alapú `interpret_image_blob()`-hoz irányít — minden
meglévő, `"strategy"` mező nélküli hozzárendelési fájl (l. a jelen
dokumentum 6. szakaszának `"file"` `ParameterType`-hoz kapcsolódó
tesztjei) változtatás nélkül, azonos eredménnyel fut tovább.

## 8. Réteghatár — mit NEM dönt el ez a dokumentum

- Az interaktív, GUI-alapú régió-hozzárendelés (Phase 13.9).
- A `sampling_distance` ajánlott alapértékének kép natív felbontásából való
  származtatása — tudatosan nyitva marad, statikus alapértékkel.
- A `TieBreakPriority` beállítási mechanizmusa — a Resolver kimenetén
  továbbra is mindig `None`.
- Footprint/mask kérdés (`BACKLOG.md` 1. tétele).

## 9. Státusz

**Elfogadva.**
