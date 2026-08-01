# Projekt Vízió

Státusz: Elfogadva
Tulajdonos:
Létrehozva: 2026-07-30
Utolsó módosítás: 2026-08-01
Kapcsolódó dokumentumok: [PROJECT_CONSTITUTION.md](PROJECT_CONSTITUTION.md), [README.md](../README.md), [ENGINEERING_PRINCIPLES.md](ENGINEERING_PRINCIPLES.md), [ARCHITECTURE.md](ARCHITECTURE.md)

## Cél

Ez a dokumentum rögzíti a Slice Designer projekt célját, célfelhasználóit, hatókörét és tervezési filozófiáját, hogy minden későbbi döntés ehhez a közös alaphoz igazodjon.

## 1. A projekt célja

A Slice Designer egy desktop alkalmazás, amely 3D modellekből (első körben STL formátumból) gyártásra előkészített, szeletelt alkatrészeket állít elő. A program nem általános célú CAD rendszer, hanem egy célzott, a gyártás-előkészítési munkafolyamatra fókuszáló eszköz.

## 2. Célfelhasználók

A Slice Designer elsődlegesen egyszemélyes, saját használatra készülő eszköz — a fejlesztő saját gyártás-előkészítési igényeit szolgálja ki. Másodlagos, jövőbeni célközönség a hobbi/maker alkotói kör, amennyiben a projekt nyilvánosan használhatóvá válik. A projekt jelenleg nem professzionális, vállalati vagy csapatkörnyezetre tervezett.

## 3. Amit a projekt magában foglal (hatókör)

* STL formátumú 3D modell (Mesh) betöltése és feldolgozása egy Project keretében. Egy Project egyszerre egy Mesh-t tartalmaz.
* A Mesh szeletelése konfigurálható Gap (távolság) mentén, Slice Set létrehozása.
* Pozicionálást segítő elemek kezelése: Spacer, Backplate, Dowel / Dowel Hole.
* Technológia-független működés: a kimenet lapos alapanyagból (Material) történő kivágásra készül, technológiától (pl. lézervágás, CNC routing, plazmavágás) függetlenül.
* Anyagfüggetlen tervezés: nincs kitüntetett anyagtípus (fa, akril, fém stb.), a működés paraméterezhető, anyagspecifikus hardcode-olt logika nélkül.
* Nesting: az alkatrészek optimális elrendezése a Material-on.
* DXF Export: gyártásra kész kimenet előállítása.

## 4. Amit a projekt nem céloz meg (nem-cél)

* Nem CAD rendszer: nem tartalmaz általános célú mesh-szerkesztést, mesh-javítást (repair) vagy szabad geometriai modellezést.
* Nem konkrét gyártástechnológiára vagy anyagra optimalizált/korlátozott megoldás.
* Nem többfelhasználós / csapategyüttműködési eszköz.
* Nem foglalkozik gépvezérléssel (pl. G-code generálás): a gyártás-előkészítés az Export (DXF) előállításával lezárul, a tényleges gépvezérlés a felhasználó által használt külön szoftver/gép feladata.

## 5. Tervezési filozófia

A projekt a Constitution alapelveire épül: a legegyszerűbb megfelelő megoldás előnyben részesítése a bonyolultabb, de "okosabb" megoldással szemben; determinisztikus, paraméterezhető működés rejtett konstansok nélkül; moduláris felépítés. Mivel a projekt elsődlegesen saját használatra készül, a fejlesztés pragmatikus: a funkciók köre a tényleges gyártás-előkészítési igényekhez igazodik, nem elméleti általánosításhoz. Nyilvános használhatóvá válás esetén ez az alapfilozófia nem változik.
