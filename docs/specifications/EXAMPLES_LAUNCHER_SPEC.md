# Példák megnyitása — Specifikáció

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-13
Utolsó módosítás: 2026-08-13
Kapcsolódó dokumentumok: [PROJECT_CONSTITUTION.md](../PROJECT_CONSTITUTION.md), [ARCHITECTURE.md](../ARCHITECTURE.md), [SPECIFICATION_STANDARD.md](../SPECIFICATION_STANDARD.md), [ENGINEERING_PRINCIPLES.md](../ENGINEERING_PRINCIPLES.md), [ROADMAP.md](../ROADMAP.md)

## 1. Kontextus

A `examples/` mappa négy, önállóan reprodukálható példaprojektet tartalmaz (`basic_example/`, `complex_example/`, `nesting_example/`, `reference_project/`), mindegyik saját `generate_example.py`-jal és `README.md`-vel (ROADMAP Phase 6.5–6.9). Jelenleg ezek kizárólag az általános "Fájl → Projekt megnyitása..." dialógussal, kézzel navigálva nyithatók meg.

**Fontos, dokumentált korlátozás, ami ennek a specifikációnak az alapja:** minden példa `README.md`-je kifejezetten figyelmezet, hogy a mentett `.json` projektfájl a generálás időpontjában érvényes, **gépspecifikus, abszolút útvonalakat** tartalmaz (`mesh_import.file_path`, `dxf_export.output_directory`) — más gépen (vagy a repó más helyre klónozva) a közvetlen megnyitás nem biztos, hogy működik. A projektgazda döntése ezért nem egyszerű fájl-megnyitás, hanem **"regenerálás + megnyitás"**: a funkció minden használatkor újra lefuttatja a kiválasztott példa `generate_example.py`-ját (ami mindig a saját, relatív `EXAMPLE_DIR`-jából — `Path(__file__).parent` — dolgozik, gépfüggetlenül), majd a frissen mentett `.json`-t tölti be.

A `SPECIFICATION_STANDARD.md` sablonja formálisan Phase 2 domain engine-ekre készült; ez a specifikáció egy GUI-réteg funkciót ír le — a szerkezet megtartva, a tartalom GUI-kontextusban értendő.

## 2. Felelősség

A "Fájl" menü egy új akciója ("Példák megnyitása..."), ami egy listázó dialógust nyit meg a repó `examples/` mappájának érvényes alkönyvtáraival (név + rövid leírás, a README.md-ből származtatva). Egy elemre kattintva a hozzá tartozó `generate_example.py` háttérben lefut, majd a frissen mentett projektfájl a meglévő "Projekt megnyitása" logikával (`persistence.load_project_config()` + `config_loader.apply_pipeline_config()`) betöltődik a felületre.

## 3. Bemenet

| Forrás | Típus | Kötelező |
|---|---|---|
| A repó `examples/` mappája, `main_window.py`-hoz képest relatív útvonallal (`Path(__file__).resolve().parents[3] / "examples"`) | fájlrendszer | igen (ha nem található, l. 7. szakasz) |
| Minden érvényes alkönyvtár: `generate_example.py` ÉS `README.md` jelenléte | fájlrendszer | egy alkönyvtár csak akkor jelenik meg a listában, ha mindkettő megvan |

A lista **dinamikusan** épül fel minden dialógus-megnyitáskor (nem hardkódolt névlista) — új példa hozzáadása a jövőben nem igényel kódmódosítást ehhez a funkcióhoz.

## 4. Kimenet

Nincs új domain-kimenet a GUI szempontjából — a `generate_example.py` már dokumentált, meglévő viselkedése (STL, projektfájl, DXF-ek írása lemezre) változatlan. GUI-állapot:

| Állapot | Típus |
|---|---|
| A betöltött widget-konfiguráció (mint bármely "Projekt megnyitása" után) | perzisztens (a felhasználó a normál "Projekt mentése"-vel elmentheti) |
| Folyamat-/siker-/hibaüzenet a `status_log`-ban | munkamenet-szintű |

## 5. Paraméterek

Nincs felhasználó által GUI-ban konfigurálható paraméter. Az `examples/` mappa helye kódszintű, dokumentált konstans (l. 3. szakasz) — ez egyúttal korlátozás is (6. szakasz).

## 6. Viselkedés

1. A "Fájl" menü egy új "Példák megnyitása..." akciót kap, a meglévő "Projekt mentése..."/"Projekt megnyitása..." mellé.
2. Kattintásra egy listázó dialógus nyílik meg: minden érvényes `examples/` alkönyvtárhoz egy sor, névvel (a README.md első, `#`-jelű sorának szövege) és rövid leírással (a cím utáni első bekezdés szövege). A sorrend ábécésorrend, a mappanév szerint (determinisztikus).
3. Ha az `examples/` mappa nem található, vagy nincs benne érvényes alkönyvtár, a dialógus ezt egyértelműen jelzi (nem hibaként, hanem tájékoztató szövegként — pl. "Nincs elérhető példaprojekt.").
4. Egy sorra kattintva (vagy kiválasztás + "Megnyitás" gomb) a dialógus bezárul, és a kiválasztott példa `generate_example.py`-ja elindul, **háttérben**, a UI blokkolása nélkül — a script lefutása (mesh-generálás, teljes pipeline, DXF export, projektmentés) néhány másodpercig tarthat.
5. A folyamat alatt: a `status_log`-ba egy indító üzenet kerül ("Példa generálása: <név> — kérem várjon."); a "Fájl" menü mindhárom akciója ("Projekt mentése...", "Projekt megnyitása...", "Példák megnyitása...") a folyamat végéig letiltott, ugyanúgy, ahogy a "Futtatás" a pipeline alatt. Az ablakbezárás a folyamat alatt ugyanúgy védett (elutasított), mint egy futó Futtatás vagy 3D-előnézet-építés alatt.
6. Sikeres lefutás után: a frissen mentett `.json` betöltése **szó szerint ugyanazzal a logikával**, mint a meglévő "Projekt megnyitása" (`persistence.load_project_config()` + `config_loader.apply_pipeline_config()`), majd "Példa betöltve: <név>." üzenet a `status_log`-ba (a meglévő felülbírálás-figyelmeztetés logikájával együtt, ha releváns).
7. Sikertelen lefutás esetén (a script nem nulla kilépő kóddal tér vissza, vagy egyáltalán nem indítható) a `status_log`-ba hibaüzenet kerül, a betöltés NEM történik meg, a jelenlegi widget-állapot változatlan marad.

## 7. Hibakezelés

* `examples/` mappa nem található (pl. nem teljes repó-checkoutból fut az alkalmazás) → informatív dialógus-tartalom, nem hiba/kivétel.
* Egy alkönyvtárban hiányzik a `generate_example.py` vagy a `README.md` → az adott alkönyvtár kimarad a listából, nem hiba.
* A README.md nem a várt formátumú (nincs `#`-cím vagy utána bekezdés) → a mappanév jelenik meg névként, üres leírással — defenzív, nem omlik el.
* A `generate_example.py` nem nulla kilépő kóddal tér vissza, vagy az indítás maga dob kivételt (pl. hiányzó Python-értelmező) → `status_log` hibaüzenet, a widget-állapot változatlan.
* A sikeres generálás után a `.json` mégsem tölthető be (elméleti eset) → ugyanaz a hibakezelés-ág, mint a rendes "Projekt megnyitása" `PipelineConfigurationError`/`SliceDesignerError` eseteinél.

## 8. Kapcsolódó komponensek és Domain Model fogalmak

* **`MainWindow._on_open_project_clicked()`** — a betöltési logika mintája és közvetlen újrahasználása.
* **`persistence.load_project_config()` / `config_loader.apply_pipeline_config()`** — változatlanul, közvetlenül felhasználva.
* **Az egyes `examples/*/generate_example.py` scriptek** (Phase 6.5–6.8) — nem módosulnak, kizárólag meghívásra kerülnek.
* Nincs domain model fogalom — tisztán GUI- és folyamatindítási réteg.

## 9. Nyitott kérdések

Nincs megválaszolatlan pont.

## 10. Elfogadási kritériumok

* A "Példák megnyitása..." akció elérhető a "Fájl" menüben.
* A dialógus dinamikusan, ábécésorrendben sorolja fel az `examples/` érvényes alkönyvtárait, README.md-ből származtatott névvel/leírással.
* Kattintásra a megfelelő `generate_example.py` a UI blokkolása nélkül lefut, majd a friss `.json` betöltődik, a "Projekt megnyitása" logikájával.
* A folyamat alatt a releváns menüakciók letiltottak, és az ablakbezárás védett.
* Hiba esetén (hiányzó mappa, sikertelen generálás, sikertelen betöltés) informatív `status_log`-üzenet, a widget-állapot nem sérül.
