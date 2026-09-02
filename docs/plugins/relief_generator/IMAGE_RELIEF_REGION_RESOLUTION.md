# Image Relief Generator — Region Resolution

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-09-02
Kapcsolódó dokumentumok: [IMAGE_RELIEF_REGION_MODEL.md](IMAGE_RELIEF_REGION_MODEL.md), [ADR-0019](../adr/0019-image-relief-depth-occlusion-semantics.md), tervezési előzmény: `docs/drafts/image_relief_generator/IMAGE_RELIEF_GENERATOR_PLANNING.md` (7–8. szakasz, 17.3/17.10 tervezési lépés)

## Cél

Ez a dokumentum rögzíti a Region Resolver kontraktusát — a Region-fa/-erdő EffectSpec[]-szé történő feloldásának mechanizmusát — a ROADMAP Phase 13.3 alfázis kimenete.

## 1. Kontextus és hatókör

```text
Image
  ↓
Image Interpretation
  ↓
Region hierarchy
  ↓
Region Resolver   ← ez a dokumentum
  ↓
EffectSpec[]
  ↓
Effect Processing (Phase 13.4)
```

Nem tárgya: a `combine` algoritmus (`S'` szűrő, `envelope`, `tiebreak` — Phase 13.4, ahol a `TieBreakPriority` ténylegesen felhasználásra kerül).

## 2. A Resolver definíciója és felelőssége

A Region Resolver a Region-fa relatív, hierarchiafüggő állapotát alakítja át EffectSpec[] konkrét, hierarchiafüggetlen állapottá, két, egymásra épülő lépésben:

1. **Irány feloldása**: `DepthBehavior = Inherit` → konkrét `EffectiveDepthBehavior` (belső, tranziens — nem kerül át az EffectSpecbe).
2. **Elevation felhalmozása**: `Contribution` + a fenti `EffectiveDepthBehavior` → `elevation` (végleges EffectSpec-mező).

**1:1 leképezés**: minden bejárt Region — nem csak a levelek — pontosan egy EffectSpecet termel; a Region-csomópontok száma megegyezik az EffectSpec-ek számával.

## 3. EffectSpec modell

```text
EffectSpec
├── Mask                 (a Region.Mask-ból, változtatás nélkül)
├── elevation             (előjeles, felhalmozott skalár)
├── ParentRef             (Optional — ős-utód reláció teszteléséhez)
└── TieBreakPriority      (Optional[int] — l. 7. szakasz)
```

Az EffectSpec jelentése: *egy Region már feloldott, önálló, a lineage mentén már felhalmozott relief-hozzájárulása.*

A `Mask` a Resolveren keresztül változtatás nélkül kerül át `Region.Mask`-ból (a Masknak nincs `Inherit`-szerű állapota, nincs szükség szülői kontextusra hozzá).

A `ParentRef` egy opcionális (top-level Regionnél `None`) mutató a szülő Region már létrehozott EffectSpecjére — kizárólag az ős-utód reláció teszteléséhez (13.4 `S'` szűrője). **Nem** szemantikai azonosító.

## 4. ParentContext (tranziens)

A `ParentContext` a Resolver belső, tranziens kontextusa — **nem** része az EffectSpecnek, resolválás után eldobódik. Pontosan két mezőt hordoz:

```text
ParentContext
├── effectiveDepthBehavior   (a szülő resolvált EffectiveDepthBehaviorja)
└── elevation                 (a szülő resolvált, felhalmozott elevationje)
```

A gyerekeknek szánt kimenő `ParentContext`-et minden csomópont a **saját, már feloldott** értékeiből építi fel — sosem a nyers `Region`-mezőkből.

**Top-level Region esetén** nincs beérkező `ParentContext`:

- `DepthBehavior = Inherit` egy top-level Regionön **kontraktussértés**, nem defaultolt eset;
- a felhalmozás baseline-ja `elevation = 0`.

## 5. `DepthBehavior = Inherit` feloldása

Egylépéses szabály minden szinten:

```text
EffectiveDepthBehavior(node) :=
    ha node.DepthBehavior ≠ Inherit  →  node.DepthBehavior
    egyébként                          →  ParentContext.effectiveDepthBehavior
```

Mivel a `ParentContext.effectiveDepthBehavior` mindig a szülő már feloldott értéke, ez a szabály tetszőlegesen hosszú `Inherit`-láncot helyesen felold anélkül, hogy a Resolvernek fel kellene "másznia" a láncban.

## 6. Elevation felhalmozása

```text
elevation(node) := ParentContext.elevation + signed(node.Contribution, EffectiveDepthBehavior(node))
signed(c, Raised)   := +c
signed(c, Recessed) := -c
```

Példa (House/Window):

```text
elevation(House)  = 0 + signed(0.5, Raised)     = 0.5
elevation(Window) = 0.5 + signed(0.3, Recessed) = 0.2
```

Ez adja az `EffectSpec.elevation` végleges értékét — a `Contribution` és az `EffectiveDepthBehavior` innentől nem kerül át külön-külön, a jelentésük teljes egészében az `elevation`-ban összegződik. Ld. ADR-0019.

## 7. TieBreakPriority — jelenlegi állapot

Az `EffectSpec.TieBreakPriority` mező a Resolver kimenetén **mindig `None`**. Sem a Region modell (13.1), sem az Image Interpretation (13.2), sem ez a Resolver nem szolgáltat hozzá értéket — a mező jelenléte a 13.4 (Effect Processing) jövőbeli, konfliktus-feloldási mechanizmusának előkészítése. A tényleges beállítási mechanizmus külön, jövőbeli döntés tárgya (l. ADR-0019 "Következmények").

## 8. Traverzálás

A Resolvernek egyetlen kemény függőséget kell tiszteletben tartania: **egy csomópont csak azután resolválható, hogy a szülője resolválva van** — parciális rendezés, nem teljes, lineáris sorrend. Testvér Regionök között, és különböző top-level Regionök (erdő) között nincs sorrendi elvárás.

## 9. Réteghatár — mit NEM dönt el ez a dokumentum

- A `Contribution`/`DepthBehavior` fizikai (magasság/mélység) jelentése — a Resolver ezeket opak értékként kezeli.
- A `combine` algoritmus, több EffectSpec együttes hatása — Phase 13.4 tárgya.
- Geometry World fogalmai (Relief Representation, GeometricSurface, Raw Mesh) — Phase 13.5–13.7.
- Az eredeti szemantikai identitás (pl. hogy egy EffectSpec "House" volt) — sosem kerül át.

## 10. Visszafelé kompatibilitás

Tisztán additív — új, plugin-belső modul. A meglévő öt generátor-típus és a core érintetlen.

## 11. Státusz

**Elfogadva.**
