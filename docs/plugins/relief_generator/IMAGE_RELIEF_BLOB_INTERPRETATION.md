# Image Relief Generator — Blob Interpretation

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-09-04
Kapcsolódó dokumentumok: [IMAGE_RELIEF_INTERPRETATION.md](IMAGE_RELIEF_INTERPRETATION.md), [ADR-0021](../adr/0021-image-relief-blob-based-region-assignment.md)

## Cél

Ez a dokumentum rögzíti a blob-alapú (seed-pixel flood-fill) Image Interpretation stratégia kontraktusát — a ROADMAP Phase 13.9, 1. rész (Domain-réteg) kimenete. Ez **kiegészíti**, nem váltja ki a `IMAGE_RELIEF_INTERPRETATION.md`-ben leírt, színenkénti stratégiát — a kettő testvér-mechanizmus, l. 4. szakasz (Dispatch).

## 1. Kontextus és hatókör

```text
Image
  ↓
Image Interpretation — Blob (ez a dokumentum)
  ↓
Region hierarchy
  ↓
Region Resolver (13.3, változatlan)
```

Nem tárgya: a GUI-interakció, ami a `seed_pixel`-eket és a bejegyzéseket ténylegesen előállítja (Phase 13.9, 2. rész — `RegionAssignmentDialog`); a Region Resolution (Phase 13.3, ADR-0019).

## 2. Hozzárendelési séma

```json
{
  "strategy": "blob",
  "regions": [
    {"seed_pixel": [34, 12], "color_tolerance": 12.0, "contribution": 0.5, "depth_behavior": "raised", "parent": null},
    {"seed_pixel": [40, 18], "color_tolerance": 5.0, "contribution": 0.2, "depth_behavior": "recessed", "parent": [34, 12]}
  ]
}
```

- `strategy` — kötelező érték `"blob"` ehhez a stratégiához (l. 4. szakasz).
- `regions` — kötelező, nem lehet üres.
- `seed_pixel` — kötelező, `[x, y]` egész pixelkoordináta-pár, a kép abszolút koordinátarendszerében. Minden bejegyzésnek egyedi `seed_pixel`-je kell legyen.
- `color_tolerance` — opcionális, alapértelmezett `0.0`. Nem lehet negatív. Folt-szintű — két bejegyzés eltérő értéket használhat.
- `contribution` — kötelező, a `Region.contribution` kontraktusa szerint (nem negatív — a `Region.__post_init__` ellenőrzi).
- `depth_behavior` — kötelező, `"raised"` | `"recessed"` | `"inherit"`.
- `parent` — opcionális, `null` vagy egy másik bejegyzés `seed_pixel`-ével pontosan (elemenként) egyező `[x, y]` pár.

Nincs `background` mező — l. 3.3 szakasz.

## 3. Algoritmus

### 3.1 Flood-fill

Minden bejegyzés `seed_pixel`-jéből indulva, **4-szomszédos** (nem 8-szomszédos) bejárás: egy szomszédos pixel akkor kerül a foltba, ha a `seed_pixel` színéhez (nem a bejárás során legutóbb hozzáadott pixel színéhez) viszonyított Euklideszi RGB-távolsága legfeljebb az adott bejegyzés `color_tolerance`-a. A bejárás **iteratív** (explicit verem), nem rekurzív.

### 3.2 Egyediség és érvényesség

- A `seed_pixel`-nek a kép határain belül kell esnie — egyébként `ImageInterpretationError`.
- Két bejegyzés nem hivatkozhat azonos `seed_pixel`-re — egyébként `ImageInterpretationError`.
- A `parent` értékének pontosan egyeznie kell egy másik bejegyzés `seed_pixel`-jével — feloldhatatlan hivatkozás vagy körkörös lánc esetén `ImageInterpretationError` (l. 5. szakasz — ez szándékosan szigorúbb, mint a színenkénti stratégia hasonló esete).

### 3.3 Nincs "kötegelt hiba" a le nem fedett pixelekre

A színenkénti stratégiával (13.2) ellentétben itt nincs olyan elvárás, hogy a kép minden pixele valamely deklarált régióhoz vagy a háttérhez tartozzon — egy blob-alapú hozzárendelés természeténél fogva részleges: a felhasználó csak a ténylegesen releváns foltokra kattint. Minden, egyetlen folt Mask-ja által sem lefedett pixel implicit "nincs hozzájárulás" — ez a Region Resolver/`combine` (13.3–13.4, változatlan) szintjén már ma is természetes, 0 elevation-t jelentő eset, külön mechanizmus nélkül.

## 4. Dispatch — együttélés a színenkénti stratégiával

A hozzárendelési fájl opcionális, top-level `"strategy"` mezője (`"color"` | `"blob"`, alapértelmezett `"color"`) dönti el, melyik stratégia fut. Egy vékony `interpret_assignment(image_path, assignment_path)` függvény (`assignment_dispatch.py`) végzi a döntést és hívja a megfelelő stratégiát — ez veszi át `interpret_image()` szerepét minden felsőbb rétegben (pl. `ImageReliefGeneratorMeshSource`).

Mivel a hiányzó `"strategy"` mező `"color"`-ra oldódik fel, **minden meglévő, 13.2/13.8 alatt keletkezett hozzárendelési fájl változtatás nélkül, azonos eredménnyel** fut tovább.

## 5. Hibakezelés

Nincs új kivétel-osztály — minden hiba (l. 3.2 szakasz, valamint érvénytelen/hiányzó `depth_behavior`, `contribution`, olvashatatlan fájl) a meglévő `ImageInterpretationError`-t használja.

## 6. Determinizmus

Azonos kép + azonos hozzárendelési fájl esetén azonos Region-erdő jön létre — a flood-fill kimenete (halmazként) és a hierarchia-építés egyaránt determinisztikus, a bejárás sorrendjétől függetlenül.

## 7. Réteghatár — mit NEM dönt el ez a dokumentum

- A `seed_pixel`-eket és a bejegyzéseket ténylegesen előállító GUI-interakció — Phase 13.9, 2. rész.
- Region Resolution (`elevation`/`ParentRef`/`TieBreakPriority`, `combine`) — Phase 13.3, ADR-0019, változatlan.
- A színenkénti stratégia (`interpret_image()`, `IMAGE_RELIEF_INTERPRETATION.md`) — Phase 13.2, változatlan.

## 8. Visszafelé kompatibilitás

Tisztán additív — új, plugin-belső modulok. A 13.2-es `interpret_image()`, a hozzá tartozó séma és minden meglévő teszt/hozzárendelési fájl változatlan és érvényes marad.

## 9. Státusz

**Elfogadva.**
