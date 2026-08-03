# ADR-0008: Nesting Engine — befoglaló-téglalap alapú csomagolás a "valódi alak" helyett

Dátum: 2026-08-03
Státusz: Elfogadva
Döntéshozó: Horváth Gyula Attila (projektgazda)

## Kontextus

A `NESTING_SPEC.md` 6. szakasza (Viselkedés, 6. lépés) "valódi alak (true-shape) szerinti elrendezést" ír elő. A ténylegesen ipari színvonalú true-shape nesting (no-fit-polygon alapú algoritmusok) a projekt méretéhez és céljához (Engineering Principles, Egyszerűség: "a legegyszerűbb, a feladatot ténylegesen megoldó megoldást kell választani") képest aránytalanul nagy implementációs terhet jelentett volna egy egyszemélyes, hobbi-célú eszközben.

## Döntés

A Nesting Engine ténylegesen **tengelyfüggő befoglaló téglalap (axis-aligned bounding box, illetve `FREE` forgatási módban a Shapely beépített minimális-területű befoglaló téglalapja) alapú, polc-alapú (shelf) csomagolási heurisztikát** valósít meg — nem a specifikáció szó szerinti "valódi alak" szerinti elrendezését.

Ez egy tudatos, dokumentált **eltérés** a `NESTING_SPEC.md` szó szerinti szövegétől, nem implementációs részlet — a `NESTING_SPEC.md` maga változatlan marad (a specifikáció a kívánt, hosszú távú célállapotot rögzíti), ezt az ADR-t kell a tényleges implementáció forrásaként figyelembe venni, amíg egy jövőbeli, finomabb algoritmus be nem váltja.

## Mérlegelt alternatívák

* **Teljes no-fit-polygon alapú true-shape nesting implementálása** — elvetve: aránytalanul nagy komplexitás/kockázat egy hobbi-célú eszközhöz képest (Engineering Principles, Egyszerűség).
* **Külső nesting-könyvtár bevonása** — elvetve: nem ismert, aktívan karbantartott, a projekt függőségi listájához illeszkedő, kellően egyszerű Python-könyvtár erre a célra a döntés idején; új, jelentős függőség bevezetése csak akkor indokolt, ha érdemben egyszerűsíti a megoldást (Engineering Principles).

## Következmények

* A tényleges lap-kihasználtság rosszabb lehet, mint egy valódi true-shape algoritmusé — különösen erősen konkáv vagy egyenetlen alakú alkatrészeknél.
* A `NESTING_SPEC.md` Kimenet-táblája ("elrendezett elemek... pozíció, forgatás") és Hibakezelése továbbra is teljes egészében teljesül — csak az elrendezés *minősége*, nem a *helyessége* egyszerűsödött.
* Backlog-tétel: ha a gyakorlati használat során a kihasználtság elégtelennek bizonyul, egy finomabb (pl. no-fit-polygon alapú) algoritmus bevezetése külön Döntési javaslat és Hatásvizsgálat tárgya lesz.
