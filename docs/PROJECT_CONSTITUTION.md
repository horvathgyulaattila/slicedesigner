# Project Constitution

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-07-31
Utolsó módosítás: 2026-07-31
Kapcsolódó dokumentumok: [PROJECT_VISION.md](PROJECT_VISION.md), [ENGINEERING_PRINCIPLES.md](ENGINEERING_PRINCIPLES.md), [ARCHITECTURE.md](ARCHITECTURE.md), [AI_WORKFLOW.md](AI_WORKFLOW.md), [adr/](adr/)

## A dokumentum helye a projektben

Ez a dokumentum a Slice Designer projekt legfelső szintű szabályrendszere. Nem architektúra, nem specifikáció, nem implementáció — hanem a projekt alkotmánya.

Minden más dokumentum ennek van alárendelve:

```
PROJECT_CONSTITUTION
        │
        ▼
PROJECT_VISION
        │
        ▼
ENGINEERING_PRINCIPLES
        │
        ▼
ARCHITECTURE
        │
        ▼
SPECIFICATIONS
        │
        ▼
SOURCE CODE
```

Ha két dokumentum között ellentmondás van, mindig a magasabb szintű dokumentum az érvényes.

A Constitution nem ír le technikai megoldásokat, algoritmusokat vagy implementációt. Kizárólag olyan alapelveket tartalmaz, amelyek az egész projekt működését meghatározzák.

---

## 0. A Constitution módosítása

Ez a dokumentum csak tudatos projektgazdai döntéssel módosítható.

Nem módosítható azért, mert:

* egy AI más megoldást javasol,
* egy új ötlet merül fel,
* egyszerűbbnek tűnik egy másik irány.

Jelentős módosítás előtt Architecture Decision Record (ADR) készül.

## 1. A projekt célja

A Slice Designer nem CAD rendszer.

A Slice Designer célzott gyártás-előkészítő alkalmazás.

## 2. A dokumentáció elsődlegessége

A dokumentáció a projekt egyetlen hivatalos igazságforrása.

A forráskód mindig a dokumentációt követi.

## 3. Egyszerűség

Mindig a legegyszerűbb megfelelő megoldást kell választani.

A szükségtelen bonyolítás kerülendő.

## 4. Moduláris felépítés

Minden modul egyetlen jól meghatározott feladatért felel.

## 5. A GUI felelőssége

A felhasználói felület nem tartalmaz üzleti vagy geometriai logikát.

## 6. Determinisztikus működés

Azonos bemenet mindig azonos eredményt ad.

## 7. Paraméterezhetőség

A működés paraméterekkel szabályozható.

A rendszer nem tartalmazhat rejtett konstansokat vagy "magic number" értékeket.

## 8. Architektúra módosítása

Az architektúra kizárólag tudatos döntéssel módosítható.

A jelentős változtatásokat ADR dokumentumban kell rögzíteni.

## 9. AI szerepe

Az AI nem tervezheti újra a projektet.

Az AI kizárólag a dokumentáció alapján dolgozhat.

Ha a dokumentáció hiányos vagy ellentmondásos, kérdeznie kell.

Nem találhat ki új architektúrát.

## 10. Minőség

Az olvasható, karbantartható és bővíthető kód fontosabb, mint a gyors implementáció.
