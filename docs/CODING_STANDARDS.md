# Kódolási Sztenderdek

Státusz: Elfogadva
Tulajdonos:
Létrehozva: 2026-07-30
Utolsó módosítás: 2026-08-01
Kapcsolódó dokumentumok: [PROJECT_CONSTITUTION.md](PROJECT_CONSTITUTION.md), [ENGINEERING_PRINCIPLES.md](ENGINEERING_PRINCIPLES.md), [AI_WORKFLOW.md](AI_WORKFLOW.md)

## Cél

Ez a dokumentum fogja rögzíteni a Slice Designer kódbázisára vonatkozó kódolási elvárásokat.

## 1. Formázás

* A kódformázás és a linting kizárólag **ruff**-fal történik (`ruff format` + `ruff check`), egyetlen konfigurációs forrásból (`pyproject.toml`, a Phase 4 megkezdésekor).
* Az import-sorrendet is a ruff rendezi (isort-kompatibilis szabályok).
* Formázási vita nem lehetséges: a ruff kimenete a mérvadó, kézi felülbírálás nincs.

## 2. Típusannotáció

* Minden publikus függvény és metódus szignatúrája (paraméterek és visszatérési érték) kötelezően típusannotált.
* A domain fogalmak (Slice, Mesh, Gap stb.) explicit típusokként (pl. `dataclass`) jelennek meg — nem generikus `dict`/`tuple` struktúrákként, összhangban az Engineering Principles paraméterezhetőségi és "nincs rejtett struktúra" szellemével.
* Statikus típusellenőrzés: **mypy**, a Domain rétegben (engine-ek) szigorú módban.

## 3. Dokumentáció

* Minden publikus modul, osztály és függvény docstring-gel rendelkezik, Google-stílusban.
* A docstring nem ismétli meg, amit a típusannotáció már kifejez — a viselkedést, a paraméterek jelentését és a dobható kivételeket írja le.

## 4. Tesztelés

* Tesztelési keretrendszer: **pytest**.
* A `tests/` a `src/slicedesigner/` struktúráját tükrözi (PROJECT_STRUCTURE.md 6. szakasza).
* Minden engine publikus viselkedése GUI nélkül, önállóan tesztelt (Engineering Principles: "a domain logika GUI nélkül is futtatható és tesztelhető").
* A tesztek determinisztikusak: nincs valós fájlrendszer- vagy hálózatfüggés a domain rétegben; ha véletlenszerűség szerepel, rögzített, dokumentált seeddel.
* Nincs kikényszerített numerikus lefedettségi célszám (az arányszám maga is "magic number" lenne) — az elvárás, hogy minden engine minden publikus viselkedése lefedett legyen.

## 5. Hibakezelés

* Egyedi kivétel-hierarchia: egy közös `SliceDesignerError` bázisosztály, ebből származtatott konkrét kivételek (pl. `InvalidMeshError`, `InvalidGapError`) — nem generikus `Exception` vagy `ValueError`.
* Kivétel csendes elnyelése tilos (`except: pass` nem megengedett); minden elkapott kivétel vagy újra dobásra, vagy explicit, naplózott kezelésre kerül — az Engineering Principles fail-fast elvének közvetlen, Python-szintű megvalósítása.
* A domain réteg kivételei technikai jellegűek, nem tartalmaznak felhasználóbarát szöveget — ennek megfogalmazása a GUI réteg felelőssége.

## 6. Naplózás

* Kizárólag a beépített `logging` modul; `print()` végleges kódban nem megengedett.
* Minden modul saját logger-t használ (`logging.getLogger(__name__)`).
* A naplózási szint kívülről paraméterezhető, nincs hardkódolt szint (Engineering Principles, paraméterezhetőség).
