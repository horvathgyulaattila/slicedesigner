# Image Relief Generator — Raw Mesh

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-09-03
Kapcsolódó dokumentumok: [IMAGE_RELIEF_GEOMETRIC_SURFACE.md](IMAGE_RELIEF_GEOMETRIC_SURFACE.md), [ADR-0020](../adr/0020-image-relief-raw-mesh-sampling-and-generator-independence.md), tervezési előzmény: `docs/drafts/image_relief_generator/IMAGE_RELIEF_GENERATOR_PLANNING.md` (15. szakasz, 17.7 tervezési lépés)

## Cél

Ez a dokumentum rögzíti a Raw Mesh réteg kontraktusát — a `GeometricSurface` tényleges mesh-sé mintavételezését — a ROADMAP Phase 13.7 alfázis kimenete.

## 1. Kontextus és hatókör

```text
Geometric Surface (Phase 13.6)
        ↓
Raw Mesh   ← ez a dokumentum
        ↓
Orchestration (Phase 13.8)
```

Ez az utolsó lépés a Geometry World-ön belül, mielőtt az eredmény elhagyja az Image Relief Generatort.

## 2. Definíció és felelősség

```text
(GeometricSurface, sampling_distance) -> GeneratedMesh
```

Közvetlen analógia a meglévő, implementált `MeshGenerator.generate(geometry, sampling_distance)` szignatúrájával (`MESH_GENERATION_MODEL.md` §36–37), csak `ReliefGeometry` helyett `GeometricSurface` bemenettel.

## 3. Mintavételezési koordináta-konvenció

`raw_relief` doménje **normalizált `[0,1] × [0,1]`** (`ADR-0020`), a meglévő `HeightField.query(x,y) -> [0,1]` mintáját követve. A Raw Mesh réteg a rácspontokat `x_norm = i/(Nx-1)`, `y_norm = j/(Ny-1)` alakban számítja (nem a fizikai `X_i/width` úton — a rács-határokon lebegőpontos kerekítés miatt), és ezt adja át közvetlenül a `raw_relief`-nek. A fizikai vertex-koordináták (`X_i = x_norm·width`, `Y_j = y_norm·height`) ettől független, külön számítás.

**Ez a réteg tudatosan semmit nem tud a kép natív pixel-felbontásáról** — a normalizált → kép-pixel-koordináta leképezés az Orchestration (Phase 13.8) felelőssége, a `raw_relief` closure belsejében.

## 4. Rács és mintavételezés

```text
Nx = ceil(width / sampling_distance)
Ny = ceil(height / sampling_distance)
```

A meglévő `MeshGenerator` mintázatának változtatás nélküli átvétele.

## 5. `v_min`/`v_max` levezetése — egyetlen mintavételezési kör

1. **Egyetlen mintavételezési kör**: `raw_relief(x_norm, y_norm)` kiértékelése a rács minden pontján, pontosan egyszer — az eredmény pontonként cache-elve.
2. **Bounds-redukció**: `v_min = min(0, min(cache))`, `v_max = max(0, max(cache))` — tiszta min/max-redukció, nincs második `raw_relief`-hívássorozat.
3. **Z-leképezés**: `physical_z(cached_value, v_min, v_max)` alkalmazása a cache-elt értékekre — ez adja a top-felület vertexeinek `Z`-koordinátáját.

## 6. Topológia

A meglévő top+bottom+4 oldalfal, watertight, kifelé mutató normálú séma (`MESH_GENERATION_MODEL.md` §36) változtatás nélkül újrafelhasználható — kizárólag a Z-érték forrása tér el (`top_z` helyett `physical_z`). Bottom-felület `Z = 0` marad. A Raw Mesh réteg **nem validálja újra** a `base_thickness − relief_height_recessed > 0` feltételt — azt a `GeometricSurface` már elvégezte konstrukciókor.

## 7. Erőforráskorlát

A meglévő `MeshGenerator` mintázatának megfelelő, önálló `MAX_SAMPLE_COUNT = 2_000_000` és `Nx/Ny < 2` ellenőrzések, `GeometricSurfaceMeshGenerationError`-t dobva (l. `ADR-0020` — ez az önálló, nem megosztott implementáció része).

## 8. Bounds-aliasing kockázat

Tudatosan vállalt, dokumentált közelítés — a `v_min`/`v_max` csak a mintarács pontjaiban ismert, nem a teljes folytonos tartományon. Külön mitigáció nélkül, a `sampling_distance` az egyetlen levere. A degenerált, teljesen lapos eset (minden mintapont azonos `ReliefValue`) helyesen viselkedik, nullával osztás nélkül — ha minden érték nulla, a `physical_z` mindenhol a `raw_value == 0` ágán át `base_thickness`-et ad, sosem oszt `v_min`/`v_max`-szal.

## 9. Réteghatár — mit NEM dönt el ez a dokumentum

- A `physical_z` belső levezetését — a `GeometricSurface`-ből ténylegesen csak `width`, `height`, `raw_relief`, `physical_z` lép át a határon.
- A normalizált → kép-pixel-koordináta leképezést (Phase 13.8, Orchestration).
- A `MeshSource`-kontraktusba csomagolást, GUI-integrációt, lifecycle-t, hibaterjesztést (Phase 13.8).
- A Footprint/mask kérdést (`BACKLOG.md` 1. tétele) — tudatosan nyitva marad ezen a rétegen is.

## 10. Státusz

**Elfogadva.**
