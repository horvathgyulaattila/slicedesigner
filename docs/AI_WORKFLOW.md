# AI Fejlesztési Munkafolyamat

Státusz: Piszkozat
Tulajdonos:
Létrehozva: 2026-07-30
Utolsó módosítás: 2026-07-31
Kapcsolódó dokumentumok: [PROJECT_CONSTITUTION.md](PROJECT_CONSTITUTION.md), [ROADMAP.md](ROADMAP.md), [PROMPT_STANDARD.md](PROMPT_STANDARD.md), [CODING_STANDARDS.md](CODING_STANDARDS.md), [ARCHITECTURE.md](ARCHITECTURE.md)

## Cél

Ez a dokumentum írja le, hogyan zajlik a Slice Designer fejlesztése AI közreműködésével, és milyen szerepkörök vesznek részt ebben a folyamatban.

## Leírás

A dokumentum rögzíti a fejlesztésben részt vevő szerepköröket (Szoftverarchitekt, Implementációs modell, Projektgazda), valamint azt az alapelvet, hogy a dokumentáció az egyetlen hivatalos igazságforrás: implementálás előtt mindig a dokumentációt kell követni, és az implementáció nem térhet el önkényesen a dokumentációban rögzített döntésektől.

A `docs/ROADMAP.md` határozza meg a projekt fejlesztési sorrendjét és aktuális állapotát. Minden új munkamenet elején ellenőrizni kell a ROADMAP aktuális állapotát. Kizárólag a következő aktív fázison szabad dolgozni. Lezárt (Locked) állapotú fázis kizárólag Architecture Decision Record (ADR) alapján módosítható.

## Javasolt tartalomjegyzék

1. A munkafolyamat célja
2. Szerepkörök
   - Szoftverarchitekt
   - Implementációs modell
   - Projektgazda
3. A dokumentáció mint hivatalos igazságforrás
4. A munkafolyamat lépései (specifikáció → implementáció → validálás)
5. A ROADMAP szerepe a munkafolyamatban
6. Eltérések kezelése a dokumentációtól


Execution Rule

A ROADMAP a projekt hivatalos végrehajtási terve. Az AI minden munkamenet elején köteles annak aktuális állapotát figyelembe venni. A következő feladatot a ROADMAP határozza meg, nem az AI.
