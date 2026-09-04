# Image Relief Generator — Region Assignment GUI

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-09-04
Kapcsolódó dokumentumok: [IMAGE_RELIEF_BLOB_INTERPRETATION.md](IMAGE_RELIEF_BLOB_INTERPRETATION.md), [ADR-0022](../adr/0022-plugin-specific-gui-editor-extension-point.md)

## Cél

Ez a dokumentum rögzíti a `RegionAssignmentDialog` interakciós kontraktusát — a ROADMAP Phase 13.9, 2. rész (GUI-réteg) kimenete, a 13.9 lezáró alfázisa.

## 1. Kontextus és hatókör

```text
"Szerkesztés..." gomb (ParameterSpec.editor, ADR-0022)
  ↓
RegionAssignmentDialog   ← ez a dokumentum
  ↓
"strategy": "blob" hozzárendelési fájl (ideiglenes)
  ↓
interpret_image_blob() (13.9, 1. rész, változatlan)
```

Nem tárgya: a blob-alapú interpretation algoritmusa (Phase 13.9, 1. rész, `IMAGE_RELIEF_BLOB_INTERPRETATION.md`); a `ParameterSpec.editor` core-mechanizmusa (ADR-0022).

## 2. Elrendezés

```text
┌───────────────────────────┬──────────────────────────┐
│                            │ Tolerancia: [====|----]  │
│                            │ 12.0                     │
│       kép-vászon           │ ───────────────────────  │
│   (zoom/pan, kattintás)    │ Régiók (húzható fa)      │
│                            │  ▸ Ház                   │
│   flood-fill overlay       │    ▾ Tető                │
│                            │    ▾ Ablakok              │
│                            │ ───────────────────────  │
│                            │ Kijelölt régió:           │
│                            │ Contribution: [___]       │
│                            │ DepthBehavior: [Raised▾]  │
│                            │ Tolerancia (ennél): [__]  │
│                            │ [Újraszámol]  [Törlés]    │
├────────────────────────────┴──────────────────────────┤
│                                    [Mégse]   [Kész]    │
└─────────────────────────────────────────────────────────┘
```

## 3. Interakciós logika

### 3.1 Kattintás a vásznon

- **Fedetlen pixelre**: háttérszálon flood-fill indul (`flood_fill_region`, 4-szomszédság, a jelenlegi tolerancia-csúszka értékével). Sikeres befejezéskor egy új, inert alapértékű (`contribution=0.0`, `depth_behavior=Raised`, nincs szülő) régió jön létre, bekerül a fába és az overlay-be, és kiválasztódik szerkesztésre.
- **Már hozzárendelt pixelre** (bármelyik meglévő régió maszkjának tagja): a megfelelő régió kiválasztódik a fában és a szerkesztő-panelen — **nem** indul új flood-fill.

### 3.2 Tolerancia és "Újraszámol"

A tolerancia-csúszka módosítása **önmagában nem** módosítja egyetlen meglévő régió maszkját sem — csak a *következő*, fedetlen pixelre irányuló kattintás toleranciáját állítja be. Egy már kiválasztott régió maszkjának a szerkesztő-panel tolerancia-mezőjében megadott új értékkel való újraszámolása kizárólag az explicit **"Újraszámol"** gombra kattintva történik (ismét háttérszálon).

### 3.3 Hierarchia

A jobb oldali fa (`QTreeWidget`, `InternalMove` húzás engedélyezve) az **egyetlen igazságforrás** a szülő-kapcsolatokra — nincs vele párhuzamosan tartott, külön `parent`-állapot. Egy elem másikra húzása azt teszi a szülőjévé; a fa gyökerébe (üres területre) húzva törli a szülő-kapcsolatot.

### 3.4 Törlés

A kiválasztott régió törlésekor a gyermekei **nem** törlődnek — a fa gyökerébe kerülnek (a szülő-kapcsolatuk törlődik, a régió maga, a maszkjával és tulajdonságaival együtt megmarad). Indoklás: egy törlés soha ne semmisítsen meg több, kézzel felvitt adatot, mint amit a felhasználó ténylegesen ki akart törölni.

## 4. Validáció és mentés

A **"Kész"** gombra kattintva a dialógus validál, **mielőtt** bármit a diszkre írna:

- Nincs-e olyan gyökér (szülő nélküli) régió, aminek `depth_behavior`-ja `Inherit` — ez a `resolve_regions()` (13.3) szintjén amúgy is hibázna, itt csak korábban, a felületen jelezzük.

Hiba esetén inline üzenet a dialógusban, a dialógus **nem** zárható be "Kész"-szel, amíg a hiba fennáll.

Sikeres validáció esetén a régiók `"strategy": "blob"` sémájú JSON-ná szerializálódnak (`IMAGE_RELIEF_BLOB_INTERPRETATION.md` 2. szakasz — `seed_pixel`, `color_tolerance`, `contribution`, `depth_behavior`, `parent`), egy `tempfile.NamedTemporaryFile(delete=False, suffix=".json")`-ba íródnak; a dialógus `result_path` attribútuma erre az útvonalra áll, a dialógus elfogadott (`QDialog.Accepted`) állapotban zárul.

Az ideiglenes fájlok takarítása jelenleg nem megoldott — tudatosan nyitva hagyott, backlog-szintű pont (nem blokkolja a 13.9 lezárását).

## 5. Dialógus újranyitása — meglévő állapot betöltése

Ha a dialógus egy `existing_assignment_path`-tal nyílik meg, és az adott fájl (a) létezik, (b) érvényes JSON, és (c) `"strategy": "blob"` — a dialógus ezt tölti be kiinduló állapotként (a maszkokat **nem** kell újraszámolni, a fájl `seed_pixel`/`color_tolerance` párjaiból közvetlenül előállíthatók `flood_fill_region`-nel). Minden más esetben (hiányzó/olvashatatlan fájl, vagy `"strategy": "color"`) a dialógus **üresen** indul, hiba/figyelmeztetés nélkül — ez nem hibaállapot, csak azt jelenti, hogy nincs korábbi blob-alapú állapot, amit be lehetne tölteni.

## 6. Háttérszálas flood-fill

Minden `flood_fill_region()` hívás (új kattintás VAGY explicit "Újraszámol") háttérszálon fut (a core `_PreviewComputeWorker` mintáját tükrözve, önálló, plugin-belső `QThread`-alosztályként) — így egy nagy, lassan kiszámítható kijelölés sem fagyasztja be a felületet. Nincs mesterséges méretkorlát a kijelölésre.

## 7. Réteghatár — mit NEM dönt el ez a dokumentum

- A blob-alapú interpretation algoritmusa (`flood_fill_region`, `interpret_image_blob`) — Phase 13.9, 1. rész, változatlan.
- A `ParameterSpec.editor` core-mechanizmusa — ADR-0022.
- Ideiglenes fájlok takarítása — nyitva, backlog-szintű.

## 8. Visszafelé kompatibilitás

Additív — új plugin-modul, új plugin-szintű függőség (PySide6). A 13.9/1. rész domain-rétege és minden meglévő teszt/hozzárendelési fájl változatlan marad.

## 9. Státusz

**Elfogadva.**
