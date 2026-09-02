# Image Relief Generator — Image Interpretation

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-09-02
Kapcsolódó dokumentumok: [IMAGE_RELIEF_REGION_MODEL.md](IMAGE_RELIEF_REGION_MODEL.md), tervezési előzmény: `docs/drafts/image_relief_generator/IMAGE_RELIEF_GENERATOR_PLANNING.md` (17.2 tervezési lépés)

## Cél

Ez a dokumentum rögzíti (a) az Image Interpretation absztrakt kontraktusát, és (b) egy konkrét, ideiglenes stratégiát a kontraktus kitöltésére — a ROADMAP Phase 13.2 alfázis kimenete.

## 1. Kontextus és hatókör

```text
Image
  ↓
Image Interpretation   ← ez a dokumentum
  ↓
Region hierarchy
  ↓
Region Resolver
  ↓
EffectSpec[]
```

Nem tárgya: hogyan oldódik fel a Region-fa `EffectSpec[]`-szé (Phase 13.3, ADR-0019); az interaktív, GUI-alapú hozzárendelés (Phase 13.9 — ez a jelen dokumentumban leírt, fájl-alapú mechanizmust váltja ki).

## 2. Image Interpretation — absztrakt kontraktus

**Definíció**: az Image Interpretation felelőssége, hogy egy input képi forrásból előállítson egy, a `Region`-kontraktusnak (`IMAGE_RELIEF_REGION_MODEL.md`) megfelelő Region-fát (vagy -erdőt).

**Bemenet**: domain-szinten nincs rögzítve konkrét reprezentáció.

**Kimenet**: Region-fa vagy -erdő.

**Region-hood kritérium**: egy terület akkor válik saját Regionná, ha hozzá megkülönböztethető (Contribution, DepthBehavior) pár tartozik.

**Hierarchia (parent-child) kritérium — "coordinate coupling"**: Region B akkor és csak akkor gyermeke Region A-nak, ha (a) B térbeli kiterjedése természetes módon A-hoz van kötve, vagy (b) B DepthBehavior-ja vagy Contributionje A-tól függ. **Térbeli átfedés vagy közelség önmagában nem indokolja a parent-child kapcsolatot.**

**Gyökér/erdő**: a Region-fa alakja nincs megkötve — lehet több gyökér Region is (erdő).

**Interpretation stratégia**: konkrét szegmentálási/interpretation stratégia domain-szinten nem rögzített — a 3. szakasz egy konkrét, de nem kizárólagos stratégiát ír le.

**OPEN**: a Region-hood kritérium konkrét küszöbe/mértéke stratégia-szintű kérdés (a 3. szakaszban leírt stratégia ezt konkrétan megválaszolja).

**REJECTED**: szemantikai tartalmazás mint önálló hierarchia-kritérium; strukturális szükségesség mint önálló Region-hood kritérium; általános, kötelező explicit mélységi sorrend/z-order mező.

## 3. Konkrét stratégia — színkódolt régió-térkép

### 3.1 Hozzárendelési fájl

Egy JSON fájl írja le, milyen szín milyen Regiont jelöl:

```json
{
  "background": "#FFFFFF",
  "color_tolerance": 12.0,
  "regions": [
    {"color": "#8B4513", "contribution": 0.5, "depth_behavior": "raised", "parent": null},
    {"color": "#FF0000", "contribution": 0.2, "depth_behavior": "recessed", "parent": "#8B4513"}
  ]
}
```

* `background` — opcionális. Egy, a felhasználó által kifejezetten "nincs itt régió"-ként megjelölt szín.
* `color_tolerance` — opcionális, alapértelmezett `0.0` (szigorú egyezés). Nem lehet negatív.
* `regions` — kötelező, nem lehet üres. Minden bejegyzés: `color` (egyedi, `#RRGGBB`), `contribution` (a `Region.contribution` validációja szerint, `≥0`), `depth_behavior` (`"raised"`/`"recessed"`/`"inherit"`), `parent` (opcionális, egy másik bejegyzés `color`-ja, vagy `null`).

Validáció: nincs duplikált `color`; minden `parent` létező `color`-ra mutat; a `parent`-láncok nem alkotnak kört.

### 3.2 Színkvantálás (`color_tolerance`)

Minden képpont a hozzá **legközelebbi** deklarált színhez (a `regions` valamelyikéhez, vagy a `background`-hoz) sorolódik, ha a távolság a `color_tolerance`-en belül van. Ez kezeli egy tárgyon belüli természetes árnyalatingadozást — enélkül egy árnyékolt/színátmenetes felület szinte minden pixele technikailag más színű lenne.

Egyenlő távolság esetén a döntés determinisztikus: előbb a `regions` lista bejárási sorrendje dönt, csak ha egyik `regions`-szín sem talál, akkor kerül sor a `background`-ra.

Azok a pixelek, amelyek egyik deklarált színhez sem sorolhatók a toleranciával, **nem hozzárendelt** pixelek — l. 4. szakasz.

### 3.3 Régió-építés színenként

Mivel minden `regions`-bejegyzéshez **egyetlen** Region tartozik — függetlenül attól, hogy a hozzá sorolt pixelek térben összefüggőek-e —, nincs szükség komponens-szintű (connected-component) elemzésre: egy adott szín Mask-ja egyszerűen az adott színhez sorolt ÖSSZES pixel halmaza. Ez azt jelenti, hogy egy adott szín két, egymástól távoli előfordulása (pl. egy ház két külön ablaka, azonos színnel) **egyetlen, közös** Regionba kerül.

### 3.4 Hierarchia felépítése

A `parent`-mutatókból épül fel a Region-fa/-erdő: minden `parent: null` bejegyzés egy gyökér Region; a többi a `parent`-je szerinti Region gyermeke lesz (`Region.children`).

### 3.5 Mask konkrét reprezentáció

Egy pixelkoordináta-halmaz (`PixelSetMask`), `member(x, y)` egész pixelindexre vágva dönt. **Ismert korlát**: nagy képeknél a pixelenkénti halmaz memóriaigénye jelentős lehet — ez az ideiglenes (13.9 által kiváltandó) mechanizmus tudatosan vállalt egyszerűsítése. Backlog-jelölt, ha a gyakorlatban problémának bizonyul.

## 4. Hibakezelés

**Azonnali hiba** (a hozzárendelési fájl feldolgozásakor): üres `regions` lista; duplikált `color`; negatív `color_tolerance`; hiányzó vagy nem létező `color`-ra mutató `parent`; kör a `parent`-láncban; érvénytelen `#RRGGBB` formátum.

**Kötegelt hiba** (a kép feldolgozása után): minden, sem `regions`-hez, sem `background`-hoz nem sorolható színű pixel egyetlen, összegyűjtött hibaüzenetben jelenik meg — színenként a pixelszámmal és egy példa-koordinátával, pixelszám szerint csökkenő sorrendben. Ez sem nem hallgat el semmit (nincs csendes "háttérré" nyilvánítás), sem nem áll meg az első ilyen pixelnél — a felhasználó egy körben látja, mi maradt ki a hozzárendelésből.

## 5. Determinizmus

Azonos kép + azonos hozzárendelési fájl esetén azonos Region-erdő jön létre — a színkvantálás és a hierarchia-építés egyaránt determinisztikus (l. 3.2, 3.4).

## 6. Réteghatár — mit NEM dönt el ez a dokumentum

* Region Resolution (`elevation`/`ParentRef`/`TieBreakPriority`, `combine`) — Phase 13.3, ADR-0019.
* Az interaktív, GUI-alapú hozzárendelés — Phase 13.9 (ez a fájl-alapú mechanizmust váltja ki).

## 7. Visszafelé kompatibilitás

Tisztán additív — új, plugin-belső modul és egy új plugin-szintű függőség (Pillow, kép-fájl beolvasásához). A meglévő öt generátor-típus és a core érintetlen.

## 8. Státusz

**Elfogadva.**
