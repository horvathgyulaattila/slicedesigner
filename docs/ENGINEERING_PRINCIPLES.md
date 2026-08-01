# Mérnöki Alapelvek

Státusz: Elfogadva
Tulajdonos:
Létrehozva: 2026-07-30
Utolsó módosítás: 2026-08-01
Kapcsolódó dokumentumok: [PROJECT_CONSTITUTION.md](PROJECT_CONSTITUTION.md), [PROJECT_VISION.md](PROJECT_VISION.md), [ARCHITECTURE.md](ARCHITECTURE.md), [CODING_STANDARDS.md](CODING_STANDARDS.md)

## Cél

Ez a dokumentum rögzíti azokat a magas szintű mérnöki alapelveket, amelyek a Slice Designer fejlesztése során minden döntést irányítanak.

## 1. Bevezetés és érvényességi kör

Ez a dokumentum a `PROJECT_CONSTITUTION.md`-ben rögzített magas szintű alapelveket bontja le gyakorlatiasabb, de továbbra is technológia- és implementáció-független mérnöki irányelvekké. Az itt felsorolt elvek minden tervezési és architekturális döntést irányítanak, függetlenül a későbbi konkrét megvalósítástól. A dokumentum nem tartalmaz kódrészletet, konkrét technológiai döntést vagy implementációs utasítást — ezeket az `ARCHITECTURE.md` és a `CODING_STANDARDS.md` részletezi majd.

## 2. Alapelvek listája

**Egyszerűség** *(Constitution 3.)*

* A legegyszerűbb, a feladatot ténylegesen megoldó megoldást kell választani.
* Nem építhető be olyan rugalmasság vagy absztrakció, amit a ROADMAP vagy egy jóváhagyott specifikáció nem ír elő.
* Külső függőség bevezetése csak akkor indokolt, ha érdemben egyszerűsíti a megoldást.

**Moduláris felépítés** *(Constitution 4.)*

* Minden modul egyetlen, egy mondatban leírható felelősséggel bír.
* A modulok jól definiált interfészeken keresztül kommunikálnak.
* Egy modul belső változása nem okozhat kaszkádhatást más modulokban.

**A GUI felelőssége** *(Constitution 5.)*

* A GUI kizárólag megjelenítésért és felhasználói interakció fogadásáért felel.
* Minden döntés, számítás és állapotváltás a domain-rétegben történik, a GUI keretrendszertől függetlenül.
* A domain logika GUI nélkül is futtatható és tesztelhető kell, hogy legyen.

**Determinisztikus működés** *(Constitution 6.)*

* A domain logika nem támaszkodhat nem-determinisztikus forrásra (seed nélküli véletlen, rendezetlen iterációs sorrend, valós idejű órától függő kimenet).
* Ha véletlenszerűség szükséges, kizárólag rögzített, dokumentált seed mellett használható.

**Paraméterezhetőség** *(Constitution 7.)*

* Minden méret, tűrés, küszöbérték nevesített, dokumentált, felülírható paraméterként jelenik meg — nincs "magic number".
* A paraméter dokumentációja egyértelműen jelzi a mértékegységet és jelentést.

**Hibakezelés — fail-fast** *(a Constitution 6. és 7. elveiből levezetve)*

* A domain-logika érvénytelen, hiányos vagy ellentmondásos bemenetre nem tesz feltételezést és nem alkalmaz csendes alapértelmezést — explicit, egyértelmű hibát jelez.
* Hibás állapotból a rendszer nem "próbál kihozni valamit" — inkább megáll, és jelzi, mi hiányzik vagy mi érvénytelen.
* A GUI-réteg hibaizolációja (pl. egy nem kritikus megjelenítési hiba ne omlassza össze az alkalmazást) nem tartozik ide — az technikai robusztusság, nem a hibás adat elfogadásának kérdése. Ennek részletei a `CODING_STANDARDS.md` "Hibakezelés" fejezetében kerülnek kidolgozásra.

**Minőség a gyorsaság helyett** *(Constitution 10.)*

* Optimalizálás csak tényleges, dokumentált igény alapján történhet, nem feltételezett jövőbeli szükségletre.
* A kód olvashatósága elsőbbséget élvez a tömörséggel vagy "okos" trükkökkel szemben.

## 3. Az alapelvek viszonya a többi dokumentumhoz

Ez a dokumentum a *"mit"* szintjén rögzíti az elveket. A *"hogyan"* szintjét két dokumentum dolgozza ki: `ARCHITECTURE.md` — hogyan valósulnak meg ezek az elvek a rendszer komponensfelépítésében; `CODING_STANDARDS.md` — hogyan érvényesülnek konkrét kódolási szabályokban. Ellentmondás esetén a `PROJECT_CONSTITUTION.md` az irányadó.
