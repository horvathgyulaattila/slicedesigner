# Image Relief Generator — Region Model

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-09-02
Kapcsolódó dokumentumok: [RELIEF_GENERATOR_DOMAIN.md](RELIEF_GENERATOR_DOMAIN.md), [MESH_SOURCE.md](../../MESH_SOURCE.md), tervezési előzmény: `docs/drafts/image_relief_generator/IMAGE_RELIEF_GENERATOR_PLANNING.md` (4–6. szakasz, 17.1 tervezési lépés)

## Cél

Ez a dokumentum rögzíti az Image Relief Generator Semantic World rétegének alap-adatmodelljét, a `Region` fogalmát és mezőit — a ROADMAP Phase 13.1 alfázis kimenete.

## 1. Kontextus és hatókör

Az Image Relief Generator tervezett feldolgozási lánca:

```text
Image
  ↓
Image Interpretation
  ↓
Region hierarchy
  ↓
Region Resolver
  ↓
EffectSpec[]
```

Ez a dokumentum kizárólag a **Region hierarchy** adatszerkezetét rögzíti. Nem tárgya:

* hogyan áll elő egy Region-fa egy tényleges képből (Image Interpretation konkrét mechanizmusa — ROADMAP Phase 13.2);
* hogyan oldódik fel a Region-fa `EffectSpec[]`-szé (`elevation`, `ParentRef`, `TieBreakPriority`, a `combine` függvény — ROADMAP Phase 13.3, ADR-0019);
* a Relief World és Geometry World rétegei (Phase 13.4–13.7).

## 2. Region modell

A minimális Region modell:

```text
Region
├── Mask
├── Contribution
├── DepthBehavior
└── Children
```

Nem szabad további mezőket bevezetni pusztán elméleti lehetőségek miatt — a modellhez csak akkor nyúlunk vissza, ha egy konkrét új követelmény tényleges hiányosságot mutat.

## 3. Mask

A `Mask` azt határozza meg, hol érvényes a Region.

A Mask kontraktusának egyetlen, bizonyítottan szükséges alapművelete a **membership query**: egy adott térbeli pontra eldönthető, hogy a Mask ott érvényes-e. A membership **bináris**.

```text
Mask.member(x, y) -> bool
```

A Mask **nem** geometriai objektum, nem heightmap, nem relief-profil, nem mesh — funkcionális kontraktus, nincs domain-szintű materializált reprezentáció. A konkrét reprezentáció (raszter/vektor/implicit függvény) Image Interpretation belső backend-döntés, nem architekturális kérdés.

Intersection/union/difference **nem** része a Mask kontraktusának — ezeket a fogyasztó rétegek vezetik le ismételt membership query-kből.

## 4. Contribution

A `Contribution` azt határozza meg, milyen erősséggel járul hozzá a Region a reliefhez.

```text
0 = nincs saját hozzájárulás
>0 = egyre hangsúlyosabb hozzájárulás
```

Negatív Contribution nincs.

```text
Contribution ≠ physical height
```

A Contribution nem közvetlen fizikai magasság- vagy mélységérték; a fizikai értelmezés egy későbbi réteg feladata.

A Contribution jelentése **a szülő már resolvált állapotához képest relatív**, nem abszolút, globális skálán mért érték — nem önmagában értelmezett "hangsúlyosság", hanem egy előjeles eltolás a szülő állapotához képest. A tényleges felhalmozási mechanizmus (`elevation`) a ROADMAP Phase 13.3 (Region Resolution, ADR-0019) tárgya.

## 5. DepthBehavior

A `DepthBehavior` azt határozza meg, milyen irányban viselkedik a Region a relief szempontjából:

```text
Raised
Recessed
Inherit
```

A DepthBehavior nem fizikai mélységet vagy magasságot jelent, hanem irányt.

## 6. Children

A `Children` a Regionök szemantikai hierarchiáját hordozza. Például:

```text
Scene
└── House
    ├── Wall
    ├── Roof
    ├── Window
    └── Door
```

A parent-child kapcsolat szemantikai, hierarchikus, kontextuális — **nem geometriai Boolean-fa**.

Egy Child Region kizárólag a saját Mask-tartalmát hordozza — nem tartalmazza és nem is kell tartalmaznia a Parent abszolút pozícióját vagy térbeli kiterjedését.

## 7. Child Region térbeli viszonya a Parenthez

A Child Region Mask-ja a kép közös, abszolút koordinátarendszerében értelmezett, ugyanúgy, mint bármely más Region Mask-ja — **nincs a Parenthez képesti relatív értelmezés**.

Ebből következik:

* a Child térbeli kiterjedése nem korlátozódik a Parent tartományára;
* kilóghat a Parent térbeli tartományából;
* nem kerül automatikusan clippingre;
* a parent-child kapcsolat önmagában nem jelent geometriai Boolean műveletet.

Például egy `House → Roof` kapcsolatnál a Roof túlnyúlhat a House falának térbeli tartományán — ez triviálisan adódik abból, hogy mindkét Mask önmagában, abszolút módon van definiálva, semmilyen külön garancia vagy mechanizmus nem szükséges hozzá.

**Ez a szakasz kizárólag térbeli (spatial) kérdésekről szól.** A behaviorális (Contribution/DepthBehavior) relatívság önálló fogalom (4. szakasz) — a kettő nem tévesztendő össze.

## 8. ReliefRole — elvetve

A `ReliefRole` nem része a minimális modellnek. Nem vezetünk be például ilyen kategóriákat:

```text
PrimaryForm
SecondaryForm
Detail
SurfaceDetail
```

Indok: nem szükségesek a relief-hozzájárulás kifejezéséhez; a hierarchia + Mask + Contribution + DepthBehavior elegendő; könnyen redundánssá válhatnának; feldolgozási kategóriákat nem akarunk előre beégetni a domainmodellbe.

## 9. Réteghatár — mit NEM dönt el ez a dokumentum

* Hogyan áll elő egy Region-fa egy tényleges képből (Image Interpretation konkrét mechanizmusa) — Phase 13.2 tárgya.
* `elevation`, `ParentRef`, `TieBreakPriority`, `EffectSpec`, a `combine` függvény — Phase 13.3 tárgya, ADR-0019.
* `GeometricSurface`, Raw Mesh — Phase 13.6/13.7 tárgya, ADR-0018.

## 10. Visszafelé kompatibilitás

Tisztán additív — új, plugin-belső domain-fogalom. A meglévő öt generátor-típus (Wave/Voronoi/Crater/Dune/WoodGrain), a `HeightField`/`ReliefGeometry` kontraktus és a core érintetlen.

## 11. Státusz

**Elfogadva.**

A dokumentum a Region adatmodell alapjait rögzíti; az Image Interpretation konkrét mechanizmusát, a Region Resolution algoritmusát és a Geometry World rétegeit a kapcsolódó, később elfogadásra kerülő dokumentumok (Phase 13.2–13.7) részletezik.
