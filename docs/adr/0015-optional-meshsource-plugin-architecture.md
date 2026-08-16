# ADR-0015: Opcionális MeshSource plugin architektúra

Dátum: 2026-08-15
Státusz: Elfogadva
Döntéshozó: Horváth Gyula Attila (projektgazda)

## Kontextus

A SliceDesigner modellfeldolgozási architektúrájában a `MeshSource` absztrakció (ADR-0014) választja el a modell létrehozását a modell további feldolgozásától. A SliceDesigner elsődleges működése jelenleg fájlból importált Mesh-re épül, de a projekt céljai között szerepelnek olyan modellgeneráló képességek is, amelyek nem egy meglévő modellfájlból indulnak — az első ilyen a Parametric Relief Generator (ROADMAP Phase 8).

Ennek megvalósításához nem szükséges és nem kívánatos a SliceDesigner core módosítása minden új modellforrás bevezetésekor. Ugyanakkor jelenleg nincs szükség általános plugin-frameworkre sem — a projekt jelenlegi célja kizárólag az, hogy új `MeshSource` megvalósítások opcionálisan, külön telepíthető komponensként kapcsolódhassanak a SliceDesignerhez.

## Döntés

A SliceDesigner támogatja az **opcionális, külön telepíthető MeshSource pluginokat**. A plugin architektúra kizárólag a `MeshSource` bővítési pontra vonatkozik:

```text
Plugin
   ↓
MeshSource
   ↓
Mesh
   ↓
meglévő SliceDesigner pipeline
```

A döntés részletei:

* a SliceDesignernek plugin nélkül is teljes értékűen kell működnie — egy plugin hiánya nem akadályozhatja a core indulását, az STL importot vagy a downstream pipeline-t;
* a plugin a SliceDesigner core-tól elkülönített Python package-ként telepíthető; a core telepítése nem igényli az opcionális plugin jelenlétét;
* a plugin kizárólag a `MeshSource` contracton keresztül kapcsolódik — nem kap közvetlen hozzáférést a SliceDesigner belső architektúrájához, és nem kap jogot a Domain Model, a slicing szabályok, a core konfiguráció vagy a pipeline sorrendjének módosítására, sem más MeshSource megvalósítás befolyásolására;
* a plugin által előállított eredmény ugyanaz a `Mesh` domainobjektum, mint amit a core MeshSource-ok (pl. STL import) is használnak — a downstream rendszer nem tesz különbséget az eredet alapján;
* a plugin hibája vagy inkompatibilitása a plugin határán belül kezelendő — nem veszélyeztetheti a core működését, és nem akadályozhatja a többi MeshSource használatát;
* a SliceDesignernek képesnek kell lennie a telepített MeshSource pluginok felismerésére úgy, hogy új plugin hozzáadásához ne legyen szükséges a core forráskódjának módosítása; a discovery és a plugin-kompatibilitás konkrét technikai mechanizmusa jelen ADR hatókörén kívül esik, későbbi implementációs döntés tárgya;
* az első konkrét plugin a **Parametric Relief Generator** — ennek saját dokumentációja határozza meg a bemeneti adatokat, paramétereket, geometriai modellt, generálási algoritmust és validációt, ezek nem részei jelen ADR-nek.

## Mérlegelt alternatívák

* **A Relief Generator közvetlen beépítése a SliceDesigner core-ba** — elutasítva: a core feleslegesen függne a generátortól, egy opcionális képesség kötelező core-komponenssé válna.
* **Általános plugin-framework bevezetése** (export pluginok, post-processing pluginok, GUI pluginok stb. is kiszolgálva) — jelenleg elutasítva: nincs rá dokumentált igény, szükségtelen absztrakciót és komplexitást vezetne be, túlmutat a jelenlegi MeshSource-problémán (Engineering Principles, egyszerűség elve).
* **Különálló Relief Generator alkalmazás** (nem SliceDesigner-plugin) — nem választott: technikailag működőképes lenne, de a cél az, hogy a generált Mesh közvetlenül a SliceDesigner modellforrásai között legyen használható, miközben a core opcionális marad.

## Következmények

* Új modellforrások (elsőként a Relief Generator Plugin) hozzáadhatók a SliceDesigner core módosítása nélkül; a plugin önállóan fejleszthető.
* A SliceDesigner core változatlanul, plugin nélkül is teljes értékűen használható.
* A downstream slicing pipeline (Slice Engine-től a DXF Exportig) egyetlen engine-je sem változik.
* Plugin discovery mechanizmust kell majd biztosítani, és a plugin/core közötti `MeshSource` contract kompatibilitását stabilan fenn kell tartani — ezek a többletkomplexitások szükségesek az opcionális bővítéshez. A discovery-mechanizmus konkrét technikai megoldását (entry-point alapú felismerés + `MeshSourceDescriptor` paraméter-séma) az [ADR-0017](0017-plugin-discovery-and-parameter-schema.md) rögzíti; a `MeshSource` contract formális verziózási/kompatibilitási kérdése továbbra is nyitott marad.
* Jelen ADR nem dönt a plugin package könyvtárstruktúrájáról (l. ADR-0016), a plugin GUI megvalósításáról (l. ADR-0017), a Relief Generator algoritmusáról, a HeightField domainmodellről, plugin marketplace-ről, automatikus plugin-letöltésről vagy sandboxolásról, illetve más plugin-típusok támogatásáról — ezeket külön, e döntésre támaszkodó dokumentációs lépések rendezik (ROADMAP Phase 8 további tételei). A konkrét Python entry-point/discovery mechanizmust az ADR-0017 rögzíti.
