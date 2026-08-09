# Release dokumentáció

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-09
Utolsó módosítás: 2026-08-09
Kapcsolódó dokumentumok: [ROADMAP.md](ROADMAP.md), [USER_GUIDE.md](USER_GUIDE.md), [ARCHITECTURE.md](ARCHITECTURE.md)

## Cél

Ez a dokumentum rögzíti a Slice Designer jelenlegi kiadási állapotát: a verziószámot, a rendszerkövetelményeket, a támogatott platformokat, az ismert korlátozásokat és hibákat, valamint a főbb fejlesztési mérföldköveket.

## 1. Verziószám és állapot

**Verzió:** `0.1.0` (`pyproject.toml`)

**Állapot:** Release Candidate — a ROADMAP Phase 6 folyamatban van. A domain-logika (mind a nyolc engine), a Project-réteg és a teljes GUI elkészült és automatizált teszttel lefedett; a jelenlegi kiadás a Release Candidate szakasz dokumentációs munkájának része.

## 2. Rendszerkövetelmények

* Python 3.11 vagy újabb.
* `uv` csomagkezelő.
* Fő függőségek (ADR-0006): `PySide6` (GUI), `trimesh` (mesh-kezelés, STL beolvasás), `ezdxf` (DXF írás), `shapely` (2D geometria).

Telepítési és indítási lépések: `USER_GUIDE.md` 1. szakasz.

## 3. Támogatott platformok

A Slice Designer technológiája (tiszta Python, PySide6, a 2. szakaszban felsorolt könyvtárak) platformfüggetlen — Windows, macOS és Linux alatt egyaránt elvileg futtatható.

**Fontos, őszinte korlát:** nincs dokumentált, formális többplatformos teszt-mátrix vagy build-pipeline, amely ezt ellenőrizné — a fenti állítás a felhasznált technológiák jellegéből következik, nem külön, platformonkénti tesztelésből. Ha platform-specifikus probléma merül fel, az jelenleg nem ismert, dokumentált eset.

## 4. Ismert korlátozások

* **Nesting — nem "true-shape" elrendezés (ADR-0008):** az elrendezési algoritmus tengelyfüggő befoglaló téglalapokkal dolgozik, nem a tényleges alkatrész-kontúr szerint. Erősen konkáv vagy egyenetlen alakú alkatrészeknél ez rosszabb lapkihasználtságot eredményezhet, mint egy ipari nesting szoftver.
* **Toldási varrat kézi utómunkát igényel:** a laptól nagyobb alkatrészek toldásakor a varrat pusztán vágásvonal — nincs hozzá automatikusan generált illesztő-geometria (pl. saját furat vagy csap); az összeillesztés a vágás utáni, kézi lépés.
* **Nincs kényelmi parancssori indító parancs:** a `pyproject.toml` nem tartalmaz `[project.scripts]` bejegyzést — az alkalmazás a `uv run python -m slicedesigner.gui.app` teljes paranccsal indítható, nincs rövidebb `slicedesigner` parancs. (Backlog-javaslatként rögzítve.)
* **Kizárólag STL bemenet:** a Mesh Import más 3D formátumot (pl. STEP, OBJ) nem fogad el — ez a Vision szerint tudatos, jelenlegi hatókör-döntés, nem hiányosság.
* **Nincs gépvezérlés:** a program a DXF Export előállításával lezárul; G-code generálás vagy bármilyen gépirányítás szándékosan nem célja (PROJECT_VISION.md).

## 5. Ismert hibák

Jelenleg nincs nyitott, dokumentált hiba.

A korábban azonosított, valódi felhasználói modelleken ("Wobbly Toad", "face-in-the-brick-wall") végzett élő teszteléssel feltárt hibák — a szelet-kontúr és a Backplate (kontúr és felirat) tükröződése (ADR-0010), a Backplate-csapok DXF-beli szétválása, valamint a Dowel-re fűzött Spacer-ek hiányzó furata — mindegyike javítva és élő teszttel megerősítve (ROADMAP Phase 6, "végső tesztelés" szakasz).

## 6. Release notes / Changelog

**0.1.0 — Release Candidate**

*Domain-logika (engine-ek):*

* Mesh Import, Slice Engine, Dowel Engine, Gap Engine, Backplate Engine, Numbering Engine, Nesting Engine, DXF Export Engine — mind a nyolc engine elkészült, a `docs/specifications/` alatti jóváhagyott specifikációk szerint.
* Pipeline-sorrend: Mesh Import → Slice → Dowel → Gap → Backplate → Numbering → Nesting, gap-tudatos szeletelés (ADR-0003), opcionális összeépítési mechanizmusok (ADR-0004), Dowel-elsőbbségű Gap-illesztés (ADR-0005).
* Kontúr körüljárási irány mint szolid/lyuk-konvenció (ADR-0007).
* Nesting: befoglaló-téglalap alapú polc-csomagolás (ADR-0008).

*Koordinációs réteg és GUI:*

* Project-réteg: pipeline-vezérlés, mentés/betöltés (`.json`), automatikus beállítás-perzisztencia.
* Teljes PySide6 GUI: paraméter-panel, 3D előnézet (PyVista, ADR-0002), futtatás/export/állapot-panel.
* DXF Export leválasztása a Futtatásról, önálló felhasználói interakcióként (ADR-0009).
* GUI-előnézet teljesítmény-optimalizálás: a geometria-építés és -renderelés háttérszálra vitele, mind a Futtatás utáni első megjelenítésnél, mind a kiemelés-/nézet-váltásnál (ADR-0011, ADR-0012).

*Hibajavítások:*

* A szelet-kontúr és a Backplate vetítési tükröződésének gyökérokig visszavezetett javítása, megosztott tengely-/glyph-táblákkal (ADR-0010).
* A Backplate-csapok DXF-beli szétválásának javítása.
* A Dowel-re fűzött Spacer-ek hiányzó furatának pótlása (`dowel_diameter_mm` attribútum).

*Dokumentáció:*

* Felhasználói kézikönyv (`USER_GUIDE.md`), munkafolyamat-leírás (`WORKFLOW.md`), ez a release dokumentáció, valamint a technikai dokumentáció (README, ARCHITECTURE, PROJECT_STRUCTURE, specifikációk) auditált, naprakész állapotban.

*Ismert hiány ebben a kiadásban:* példaprojektek (`examples/`) — ld. ROADMAP Phase 6, 6.5–6.9 tétel.
