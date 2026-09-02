# Image Relief Generator — Relief Representation

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-09-02
Kapcsolódó dokumentumok: [IMAGE_RELIEF_EFFECT_PROCESSING.md](IMAGE_RELIEF_EFFECT_PROCESSING.md), tervezési előzmény: `docs/drafts/image_relief_generator/IMAGE_RELIEF_GENERATOR_PLANNING.md` (13. szakasz, 17.5 tervezési lépés)

## Cél

Ez a dokumentum rögzíti a Relief Representation kontraktusát — a hidat az Effect Processing és a Geometry World között — a ROADMAP Phase 13.5 alfázis kimenete.

## 1. Kontextus és hatókör

```text
EffectSpec[]
  ↓
Effect Processing (`combine`)
  ↓
Relief Representation   ← ez a dokumentum
  ↓
Geometric Surface (Phase 13.6, ADR-0018)
```

Nem tárgya: a `GeometricSurface` fizikai leképezése (Phase 13.6), a Falloff tényleges implementációja (opcionális, csak jövőbeli igazolt igény esetén).

## 2. Definíció és felelősség

A Relief Representation egyetlen felelőssége hidat képezni az Effect Processing és a Geometry World között: hordozza a downstream fizikai leképezéshez szükséges információt, anélkül hogy maga fizikai jelentést, mértékegységet vagy konkrét materializációt tartalmazna.

## 3. Absztrakciós forma — funkcionális kontraktus

A Relief Representation minimális, bizonyítottan szükséges kontraktusa: egy **"pont → ReliefValue" függvény**, reprezentációfüggetlen — analóg a Mask funkcionális kontraktusával (`IMAGE_RELIEF_REGION_MODEL.md`). Konkrét materializáció (raszter/rács/egyéb) nem szükséges: a downstream igényei function-kompozícióval kielégíthetők, a mintavételezés a Geometry → Raw Mesh lépés (Phase 13.7) felelőssége.

## 4. Üres bemenet — perem-feltétel

Ha egy ponton egyetlen EffectSpec sem ad membershipet, az érték nulla: `combine(∅) := 0`. Ez már a `combine` (Phase 13.4) implementációjában biztosított — a Relief Representation nem ad hozzá külön logikát.

## 5. `ReliefValue` doménje

Előjeles skalár:

```text
pozitív  → Raised irányú nettó hatás
negatív  → Recessed irányú nettó hatás
0        → nincs hatás
```

A tartomány korlátlan/nem előre vizsgált — a fizikai leképezés (Phase 13.6) adaptívan, a realizált szélsőértékekből normalizál majd, nem egy előre feltételezett skálafaktorból.

## 6. Falloff/smoothing — pontosítás

Ha a jövőben konkrét követelmény igazolja a szükségességét, a falloff a **teljes Relief Representation függvényen** értelmezett transzformáció (`Relief Representation → Relief Representation`), NEM pontonkénti (`ReliefValue → ReliefValue`) — egy neighborhood-alapú művelet (pl. élkerekítés) nem vezethető le egyetlen pont értékéből. Ez a dokumentum és a hozzá tartozó kód nem implementál falloffot.

## 7. Fizikai határ a Geometry felé

```text
ReliefValue ≠ physical height
```

Mértékegység, base plane, Z-tartomány kizárólag a Relief → Geometry lépés (Phase 13.6, ADR-0018) tárgya.

## 8. Réteghatár — mit NEM dönt el ez a dokumentum

- Az eredeti szemantikai identitás.
- A `combine` belső algoritmusa — csak a kimeneti kontraktusa.
- A Geometry World fogalmai (base plane, Z-tartomány, mesh, sampling) — Phase 13.6–13.7.
- A Mask konkrét reprezentációja.

## 9. Visszafelé kompatibilitás

Tisztán additív — vékony, új, plugin-belső modul, ami a meglévő `combine`-ot csomagolja be egy formálisan elnevezett típusba. A meglévő öt generátor-típus és a core érintetlen.

## 10. Státusz

**Elfogadva.**
