# PLUGIN_REPOSITORY_STRUCTURE_PROPOSAL.md

## 1. Cél

Jelen dokumentum célja a SliceDesigner opcionális pluginjainak repository- és package-struktúrájának meghatározása.

A dokumentum első konkrét alkalmazási esete a Parametric Relief Generator plugin.

A cél olyan struktúra kialakítása, amely:

* egyértelműen elválasztja a SliceDesigner core-t a pluginoktól;
* lehetővé teszi az opcionális pluginok használatát;
* nem teszi a pluginokat a core architektúra részévé;
* egyetlen repositoryban kezelhetővé teszi a közös fejlesztést;
* később lehetővé teszi egy plugin külön repositoryba történő kiemelését;
* nem kényszerít korai multi-repo infrastruktúrát a projektre.

---

# 2. Javasolt repository modell

A javasolt modell:

> **Monorepo, külön plugin namespace-szel.**

A SliceDesigner és az opcionális pluginok ugyanabban a Git repositoryban helyezkednek el, de fizikailag és package-szinten is elkülönülnek.

Javasolt alapstruktúra:

```text
slicedesigner/
│
├── slicedesigner/
│   ├── domain/
│   ├── project/
│   ├── engine/
│   └── ...
│
├── plugins/
│   └── relief_generator/
│       ├── ...
│       └── ...
│
├── tests/
│
├── docs/
│
├── examples/
│
├── pyproject.toml
└── ...
```

A konkrét alkönyvtárak a repository aktuális struktúrájához igazítandók.

Ez a dokumentum **nem írja elő a meglévő SliceDesigner core könyvtárstruktúrájának átszervezését**.

---

# 3. Miért monorepo?

A jelenlegi projektállapotban a monorepo a preferált megoldás.

Ennek oka, hogy a plugin és a SliceDesigner:

* közös fejlesztési folyamatban vesz részt;
* közös architekturális dokumentációra támaszkodik;
* közös `MeshSource` contractot használ;
* közös tesztkörnyezetben ellenőrizhető;
* kezdetben szorosan összefüggő fejlesztési fázisban van.

A külön repositoryk használata jelenleg olyan többletterhet jelentene, amelyhez nincs megfelelő architekturális vagy üzleti indok.

Nem cél:

* külön CI-rendszer;
* külön release pipeline;
* külön verziókezelési workflow;
* cross-repository kompatibilitási rendszer

bevezetése pusztán a plugin miatt.

---

# 4. Miért nem kerül a plugin a core package-be?

A plugin opcionális.

Ezért a következő struktúra nem kívánatos:

```text
slicedesigner/
└── slicedesigner/
    ├── core/
    └── relief_generator/
```

Ebben a modellben a plugin könnyen a core package részévé válhatna.

A kívánt modell:

```text
slicedesigner/
├── slicedesigner/
│
└── plugins/
    └── relief_generator/
```

A fizikai elválasztás az architekturális határt is láthatóvá teszi.

---

# 5. Plugin dependency irány

A dependency irány egyirányú:

```text
Plugin
   ↓
SliceDesigner Core
```

A core nem függhet a pluginoktól:

```text
SliceDesigner Core
        X
        ↑
Plugin
```

A plugin használhatja a core által biztosított stabil contractokat, például:

* `MeshSource`;
* szükséges domain típusokat;
* extension pontokat.

A core azonban nem importálhat közvetlenül plugin-specifikus implementációkat.

---

# 6. Plugin mint opcionális komponens

A SliceDesignernek plugin nélkül is működőképesnek kell maradnia.

```text
SliceDesigner
│
├── Core
│
└── Optional Plugins
       └── Relief Generator
```

Plugin telepítve:

```text
Core + Relief Plugin
```

Plugin nincs telepítve:

```text
Core
```

Mindkét állapot érvényes rendszerállapot.

---

# 7. Python package-határ

A repository könyvtárszerkezete és a Python package-struktúra nem feltétlenül azonos fogalom.

A plugin saját Python package-ként kezelendő.

A plugin saját namespace-szel rendelkezik.

Például:

```text
plugins/
└── relief_generator/
    └── ...
```

és egy ennek megfelelő plugin package.

A pontos import namespace-et az implementációs szakaszban kell rögzíteni, figyelembe véve a jelenlegi `pyproject.toml` és build-rendszer működését.

E dokumentum nem rögzít konkrét Python import-nevet, mert az már a tényleges package-struktúra implementációs döntése.

---

# 8. Plugin belső szerkezete

A Relief Generator plugin belső struktúrájának követnie kell a már elfogadott domain-határokat.

Javasolt modell:

```text
relief_generator/
│
├── domain/
│
├── generators/
│
├── geometry/
│
├── mesh/
│
├── source/
│
└── ...
```

A felelősségek:

```text
generators/
    Surface generation

domain/
    Relief domain model

geometry/
    ReliefGeometry

mesh/
    Mesh generation

source/
    MeshSource adapter
```

A tényleges struktúra csak akkor bővítendő, ha valós implementációs igény indokolja.

---

# 9. Core és plugin közötti contract

A plugin és a core közötti elsődleges contract:

```text
MeshSource
```

A Relief Generator plugin belső működése:

```text
Generator
    ↓
HeightField
    ↓
ReliefGeometry
    ↓
Mesh
```

A core felé:

```text
MeshSource
    ↓
Mesh
```

A core nem ismeri a plugin belső reprezentációit.

Nem kell ismernie például:

* Wave Generatort;
* Height Fieldet;
* ReliefGeometry-t;
* direction spreadet;
* wave paramétereket.

---

# 10. Plugin-specifikus domain nem kerül a core-ba

A következő típusok nem kerülhetnek a SliceDesigner core domainjébe csak azért, mert a Relief Generator használja őket:

```text
WaveParameters
HeightField
ReliefGeometry
WaveGenerator
ReliefMeshGenerator
```

Ezek a plugin domainjének részei.

A core kizárólag a saját contractjaihoz szükséges absztrakciókat tartalmazza.

---

# 11. Plugin discovery

A pluginok felismerésének módja külön extension/discovery mechanizmuson keresztül történjen.

A core nem tartalmazhat ilyen típusú logikát:

```text
if relief_generator_installed:
    import relief_generator
```

A konkrét discovery mechanizmust az implementációs szakaszban kell meghatározni, a meglévő plugin architektúrával összhangban.

A jelen dokumentum alapelve:

> A core ne legyen plugin-specifikus.

---

# 12. Plugin telepítés

A Relief Generator opcionális komponens.

A kívánt felhasználói modell:

```text
Base installation
    ↓
SliceDesigner
```

vagy:

```text
Base installation
    ↓
SliceDesigner
    +
Relief Generator Plugin
```

A plugin telepítése nem változtathatja meg a core működésének alapvető módját.

---

# 13. Fejlesztési workflow

A monorepo lehetővé teszi, hogy:

```text
Core change
     ↓
Plugin compatibility test
```

és:

```text
Plugin change
     ↓
Core contract test
```

egy repositoryban legyen ellenőrizhető.

Ez különösen fontos a kezdeti fejlesztési szakaszban, amikor a plugin és a core közötti contract még aktív használatban van.

---

# 14. Tesztelési struktúra

A tesztek logikailag különíthetők el:

```text
tests/
├── core/
│
└── plugins/
    └── relief_generator/
```

A plugin tesztjei nem kerülhetnek olyan helyzetbe, hogy a teljes plugin működése szükséges legyen a core alaptesztjeinek lefutásához.

A core tesztjeinek plugin nélkül is futniuk kell.

---

# 15. Dokumentáció

A plugin dokumentációja nem kerülhet automatikusan a core dokumentációba.

Javasolt:

```text
docs/
├── architecture/
├── domain/
└── plugins/
    └── relief_generator/
```

A közös architekturális döntések továbbra is a core projekt dokumentációjában maradnak.

A plugin-specifikus döntések a plugin dokumentációjában helyezkednek el.

---

# 16. Example projektek

Az example projektek szintén elkülöníthetők:

```text
examples/
├── core/
└── relief_generator/
```

A Relief Generator példaprojektjeinek célja:

* a plugin működésének bemutatása;
* a dokumentált contractok igazolása;
* reprodukálható példák biztosítása;
* későbbi regressziós tesztalap biztosítása.

---

# 17. Későbbi pluginok

A struktúra több plugin számára is használható:

```text
plugins/
├── relief_generator/
├── future_plugin_a/
└── future_plugin_b/
```

Ez azonban **nem jelenti azt, hogy jelenleg további pluginokat kell tervezni vagy létrehozni**.

A struktúra csak biztosítja a lehetőséget.

A jelenlegi projektcél továbbra is a Relief Generator.

---

# 18. Külön repositoryba költözés lehetősége

A monorepo nem jelent végleges repository-stratégiai kötelezettséget.

Ha egy plugin később:

* önálló termékké válik;
* saját release ciklust kap;
* más alkalmazások számára is használható;
* önálló felhasználói bázist kap;
* jelentősen eltérő fejlesztési életciklust követ;

akkor külön repositoryba helyezhető.

A jelenlegi struktúrát ezért úgy kell kialakítani, hogy a plugin belső kódja ne legyen összekeverve a core kódjával.

---

# 19. Későbbi külön repo esetén

A kívánt migráció:

```text
Jelenleg:

slicedesigner/
└── plugins/
    └── relief_generator/


Később:

slicedesigner/
└── core


relief-generator/
└── plugin
```

A migráció akkor lehet egyszerű, ha:

* a plugin saját package-határral rendelkezik;
* a core dependency irány egyértelmű;
* a plugin nem importál core-internal modulokat;
* a core-plugin contract stabil.

---

# 20. Mit nem jelent ez a struktúra?

A `plugins/` könyvtár bevezetése nem jelenti:

* plugin marketplace bevezetését;
* dinamikus plugin marketplace infrastruktúrát;
* több plugin egyidejű támogatásának kötelező megvalósítását;
* külön plugin SDK létrehozását;
* külön plugin verziókezelési rendszert;
* külön repositoryk létrehozását.

Ezek későbbi döntések lehetnek.

---

# 21. Hatásvizsgálat

## Érintett dokumentumok

* ROADMAP
* Plugin Architecture dokumentáció
* Relief Generator dokumentáció
* Implementation Plan
* kapcsolódó MeshSource dokumentáció

A korábbi relief-domain dokumentumok tartalmát ez a döntés nem módosítja.

## Érintett könyvtárak

Új plugin namespace szükséges:

```text
plugins/
```

és azon belül:

```text
plugins/relief_generator/
```

A meglévő core struktúrát nem szükséges átszervezni.

## Szükséges dokumentummódosítások

A plugin architecture dokumentációját ki kell egészíteni a repository/package elhelyezkedésével.

Az `IMPLEMENTATION_PLAN.md`-ben a plugin létrehozásának könyvtárstruktúráját ehhez kell igazítani.

A ROADMAP módosítása akkor szükséges, ha a repository-struktúra döntése külön taskként jelenik meg.

## Szükséges ADR

Javasolt egy ADR létrehozása, ha a projekt architektúra dokumentációja a repository/package struktúrát önálló architekturális döntésként kezeli.

Javasolt cím:

```text
ADR – Plugin Repository and Package Structure
```

## Visszafelé kompatibilitás

A döntésnek:

* nem szabad megváltoztatnia a core API-t;
* nem szabad kötelező pluginfüggőséget létrehoznia;
* nem szabad módosítania a meglévő MeshSource contractot;
* nem szabad megszüntetnie a plugin nélküli működést.

---

# 22. Döntési javaslat

A SliceDesigner pluginjai **egyetlen monorepo részeként**, de külön `plugins/` namespace alatt legyenek elhelyezve.

A Relief Generator:

```text
plugins/relief_generator/
```

alatt kapjon saját package-határt.

A plugin a SliceDesigner core-tól függjön, fordított függőség ne legyen.

A plugin saját domain-, geometry-, mesh- és source-logikáját a plugin határain belül tartsa.

A külön repositoryba költözés lehetőségét a struktúra biztosítsa, de jelenleg ne legyen cél.

---

# 23. Javasolt döntés státusza

**Tervezet – projektgazdai jóváhagyásra vár.**

A jóváhagyás után:

1. a plugin architecture dokumentáció kiegészítése;
2. szükség esetén ADR létrehozása;
3. az `IMPLEMENTATION_PLAN.md` pontosítása;
4. repository-struktúra implementációja

következhet.

**A tényleges könyvtárak létrehozása csak ezután történik.**
