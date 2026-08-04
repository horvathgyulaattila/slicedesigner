# Backlog

Státusz: Aktív
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-04
Utolsó módosítás: 2026-08-04
Kapcsolódó dokumentumok: [ROADMAP.md](ROADMAP.md)

## Cél

Ez a dokumentum azokat a jövőbeli tételeket (funkciókat, optimalizálásokat) sorolja fel, amelyek felmerültek a fejlesztés során, de nem tartoznak a jelenlegi fázis kilépési feltételei közé. Nem specifikáció és nem ROADMAP — kizárólag nyomon követhetőségi célt szolgál, formális elvárás (pl. SPECIFICATION_STANDARD) nélkül.

## Tételek

### 1. 2D export-előnézet

A Nesting Engine kimenetének (exportra kerülő vektorok) 2D megjelenítése ellenőrzés céljából, futtatás/export előtt.

**Eredet / indoklás:** Új funkció, nincs jelenleg dokumentációs alapja — önálló specifikáció és jóváhagyás szükséges bevezetése előtt.

### 2. Dowel automatikus pozíciókeresés — további teljesítmény-optimalizálás

A jelenlegi rácsos keresés (`_PLACEMENT_GRID_STEP_MM` finomságú, teljes bejárás) bonyolultabb formáknál továbbra is lassú (a korábbi teljesítmény-javítás után is kb. 29 mp egy 200 mm-es kockán). Durvább kezdő-rács + finomítás, vagy térbeli indexelés csökkenthetné a futásidőt.

**Eredet / indoklás:** Élő tesztelés során feltárt teljesítményprobléma. A megoldás megváltoztathatja, mely pozíciókat találja meg az algoritmus, ezért önálló, alapos vizsgálatot és jóváhagyást igényel — nem végezhető el mellékesen.
