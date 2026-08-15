# ADR-0016: Plugin repository- és package-struktúra

Dátum: 2026-08-15
Státusz: Elfogadva
Döntéshozó: Horváth Gyula Attila (projektgazda)

## Kontextus

A SliceDesigner opcionális MeshSource pluginjai (ADR-0015) számára rögzíteni kell, hol és hogyan helyezkedjenek el a repository-ban és a Python package-struktúrában. A cél olyan struktúra, amely egyértelműen elválasztja a SliceDesigner core-t a pluginoktól, lehetővé teszi az opcionális pluginok használatát, nem teszi a pluginokat a core architektúra részévé, egyetlen repositoryban kezelhetővé teszi a közös fejlesztést, és később lehetővé teszi egy plugin külön repositoryba történő kiemelését — anélkül, hogy korai multi-repo infrastruktúrát kényszerítene a projektre. Az első konkrét alkalmazás a Relief Generator Plugin (ROADMAP Phase 8).

## Döntés

A SliceDesigner pluginjai **egyetlen monorepo részeként**, de a core-tól fizikailag elkülönített `plugins/` névtér alatt kapnak helyet, a meglévő `src/` mellett, azzal azonos szinten a repo gyökerében:

```text
slicedesigner/                    # repo gyökér
├── src/
│   └── slicedesigner/            # core Python csomag
├── plugins/
│   └── relief_generator/         # első konkrét plugin
│       ├── domain/
│       ├── generators/
│       ├── geometry/
│       ├── mesh/
│       └── source/
├── tests/
│   └── plugins/
│       └── relief_generator/
├── docs/
│   └── plugins/
│       └── relief_generator/
├── examples/
└── pyproject.toml
```

A döntés részletei:

* a függőség iránya egyirányú: Plugin → Core; a core nem importálhat plugin-specifikus implementációt, és nem tartalmazhat plugin-specifikus logikát (pl. `if relief_generator_installed: ...`);
* a plugin kizárólag a `MeshSource` contracton (ADR-0014) keresztül kapcsolódik a core-hoz; a plugin belső felépítése (pl. Wave Generator, HeightField) a core számára ismeretlen és irreleváns;
* mindkét állapot érvényes: `Core` (plugin nélkül) és `Core + Relief Plugin` (telepítve) — a plugin telepítése nem változtathatja meg a core alapvető működési módját;
* a plugin belső mappastruktúrája a saját domain-határait tükrözi: `domain/` (Relief domain modell), `generators/` (Surface generation), `geometry/` (ReliefGeometry), `mesh/` (Mesh generation), `source/` (MeshSource adapter) — ez már összhangban van az `IMPLEMENTATION_PLAN.md`-vel;
* plugin-specifikus domain típusok (pl. `WaveParameters`, `HeightField`, `ReliefGeometry`, `WaveGenerator`) nem kerülnek a SliceDesigner core domainjébe, kizárólag azért, mert egy adott plugin használja őket;
* a pluginok tesztjei a `tests/plugins/<plugin_neve>/` alatt kapnak helyet, a meglévő `tests/engines/`, `tests/project/`, `tests/gui/` mellett; a core tesztjeinek plugin nélkül is futniuk kell;
* a plugin dokumentációja a `docs/plugins/<plugin_neve>/` alatt van (`PROJECT_STRUCTURE.md` 10. szakasza) — ez a döntés már korábban, külön lépésben megtörtént;
* a plugin discovery (a telepített pluginok felismerésének) konkrét technikai mechanizmusa jelen ADR hatókörén kívül esik, későbbi implementációs döntés tárgya;
* a pontos Python import-namespace-t az implementáció során, a tényleges `pyproject.toml`/build-rendszer figyelembevételével kell rögzíteni — jelen ADR ezt nem dönti el;
* a monorepo nem jelent végleges repository-stratégiai kötelezettséget — ha egy plugin később önálló termékké, saját release-ciklussal válik, külön repositoryba helyezhető át, feltéve, hogy a plugin saját package-határral rendelkezik, és nem importál core-internal modulokat.

## Mérlegelt alternatívák

* **A plugin a core package részeként** (pl. `src/slicedesigner/relief_generator/`) — elutasítva: a fizikai elválasztás teszi láthatóvá az architekturális határt; ebben a modellben a plugin könnyen a core package részévé válhatna.
* **Külön repository pluginonként, már most** — elutasítva: a plugin és a core jelenleg közös fejlesztési folyamatban, közös `MeshSource` contracton és közös tesztkörnyezetben áll; a külön repository felesleges többletterhet (külön CI, release pipeline, verziókezelési workflow, cross-repo kompatibilitási rendszer) jelentene indok nélkül.
* **Általános plugin-marketplace vagy plugin SDK bevezetése már most** — elutasítva: nincs rá dokumentált igény, szükségtelen komplexitást vezetne be (Engineering Principles, egyszerűség elve).

## Következmények

* Létrejön a `plugins/` könyvtár a repo gyökerében, a `src/` mellett, valamint a `tests/plugins/` könyvtár — mindkettő kezdetben üres vázként, a Relief Generator Plugin (`relief_generator/`) almappájával és annak öt belső mappájával (`domain/`, `generators/`, `geometry/`, `mesh/`, `source/`).
* A meglévő `src/slicedesigner/` core struktúra nem változik.
* A `PROJECT_STRUCTURE.md`-t ezzel egy időben, külön szakasszal egészítjük ki.
* A pontos Python csomagolási/discovery mechanizmus továbbra is nyitott, implementáció közben eldöntendő kérdés.
* A `docs/architecture/` és `docs/domain/` alkönyvtárak (amelyeket a `PLUGIN_REPOSITORY_STRUCTURE_PROPOSAL.md` eredeti vázlata javasolt) **nem** kerülnek bevezetésre — az `ARCHITECTURE.md` és a `DOMAIN_MODEL.md` továbbra is a `docs/` gyökerében maradó, önálló fájlok maradnak, a már kialakult konvenció szerint; a plugin-dokumentáció helye a már elfogadott `docs/plugins/<plugin_neve>/`.
