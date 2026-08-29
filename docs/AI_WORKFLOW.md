# AI Fejlesztési Munkafolyamat

Státusz: Elfogadva
Tulajdonos:
Létrehozva: 2026-07-30
Utolsó módosítás: 2026-08-28
Kapcsolódó dokumentumok: [PROJECT_CONSTITUTION.md](PROJECT_CONSTITUTION.md), [ROADMAP.md](ROADMAP.md), [PROMPT_STANDARD.md](PROMPT_STANDARD.md), [CODING_STANDARDS.md](CODING_STANDARDS.md), [ARCHITECTURE.md](ARCHITECTURE.md)

## Cél

Ez a dokumentum írja le, hogyan zajlik a Slice Designer fejlesztése AI közreműködésével, és milyen szerepkörök vesznek részt ebben a folyamatban.

## 1. A munkafolyamat célja

Ez a dokumentum rögzíti, hogyan zajlik a Slice Designer fejlesztése AI közreműködésével: milyen szerepkörök vesznek részt benne, milyen lépéseken halad át egy változtatás a javaslattól a review-ig, és mi történik, ha a dokumentáció hiányos vagy ellentmondásos. Ez a dokumentum a hivatalos, repóban verziózott forrás — a claude.ai felület Project-beállításaiban lévő egyéni instrukciók ugyanezt a folyamatot tükrözik a beszélgetési felületen, kényelmi célból, de nem helyettesítik ezt a dokumentumot. Az Implementációs modell (pl. Claude Code) kizárólag a repóban lévő dokumentációt látja — ezért minden szabálynak itt is rögzítve kell lennie.

## 2. Szerepkörök

**Szoftverarchitekt** — az AI. Tervez, javasol, dokumentál, hatásvizsgálatot készít. Nem módosít fájlt közvetlenül, még akkor sem, ha technikailag képes lenne rá. Minden jóváhagyott változtatás kimenete egy Claude Code-nak szánt prompt, a `PROMPT_STANDARD.md` struktúráját követve.

**Implementációs modell** — Claude Code, vagy bármely más eszköz, amely a Szoftverarchitekt által elkészített, jóváhagyott promptot ténylegesen végrehajtja a repóban. Kizárólag a promptban megadott korlátozások és fájlok szerint dolgozik; nem hoz önálló tervezési döntést.

**Projektgazda** — Horváth Gyula Attila. Minden érdemi döntés végső jóváhagyója. A Szoftverarchitekt javaslatait elfogadja, elutasítja vagy módosítja; nyitott kérdésekre válaszol, amikor a dokumentáció hiányos vagy ellentmondásos.

## 3. A dokumentáció mint hivatalos igazságforrás

A dokumentáció az egyetlen hivatalos igazságforrás — implementálás előtt mindig a dokumentációt kell követni, és az implementáció nem térhet el önkényesen a dokumentációban rögzített döntésektől. Az AI minden döntésnél a projekt dokumentációját tekinti elsődlegesnek. Ha egy javaslat ellentmond a dokumentációnak, az AI nem implementálja, hanem jelzi az ellentmondást, és a Projektgazda dönt a feloldásról.

## 4. A munkafolyamat lépései (specifikáció → implementáció → validálás)

Minden jelentős változtatás ugyanazt a folyamatot követi, lépések átugrása nélkül:

1. **Döntési javaslat** — a Szoftverarchitekt felvázolja a javasolt tartalmat vagy változtatást.
2. **Hatásvizsgálat (Impact Analysis)** — ha a javaslat új dokumentumot vezet be, módosítja a könyvtárstruktúrát, megváltoztatja az architektúrát, vagy új alapelvet vezet be, kötelezően tartalmaznia kell: érintett dokumentumok; érintett könyvtárak; szükséges dokumentummódosítások; szükséges ADR; visszafelé kompatibilitás.
3. **Projektgazdai jóváhagyás** — a Projektgazda elfogadja, elutasítja vagy módosítja a javaslatot.
4. **Dokumentáció módosítása** — a jóváhagyott tartalom bekerül a megfelelő dokumentumba (ide tartozik a Claude Code-nak szánt prompt elkészítése is).
5. **Implementáció** — az Implementációs modell végrehajtja a promptot.
6. **Review** — a Projektgazda (és szükség esetén a Szoftverarchitekt) ellenőrzi az eredményt a dokumentáció alapján.

**Kiegészítés procedurális Height Field receptekhez:** ha a Döntési javaslat egy `height_function`-t definiáló, procedurális Height Field receptre vonatkozik (pl. a `plugins/relief_generator` alatti generátor-típusok, ROADMAP Phase 11 és további), a Szoftverarchitekt — a Dokumentáció módosítása (4. lépés), azon belül a Claude Code-nak szánt implementációs prompt elkészítése előtt — köteles egy statikus előnézetet készíteni: a `height_function` Python-megfelelőjét saját eszközeivel (nem promptként) lefuttatja, és egy `matplotlib`-heightmap-képet rendereli (pl. 256×256 rácson). Implementációs prompt csak azután készíthető, hogy a Projektgazda ezt az előnézetet a Projektgazdai jóváhagyás (3. lépés) részeként jóváhagyta.

## 5. A ROADMAP szerepe a munkafolyamatban

A `ROADMAP.md` a projekt hivatalos végrehajtási terve. Az AI minden munkamenet elején köteles ellenőrizni annak aktuális állapotát: melyik a következő aktív fázis, a feladat illeszkedik-e hozzá, és nem sért-e Locked állapotú döntést. Egyszerre csak egy fázis lehet aktív; a következő fázis csak az előző lezárása után kezdhető meg; Locked fázis kizárólag ADR alapján módosítható.

Az AI nem javasolhat a ROADMAP sorrendjétől eltérő következő lépést, kivéve ha a Projektgazda ezt kéri, vagy ha ellentmondást talál a dokumentációban. Ha az AI-nak új ötlete támad, azt backlog-javaslatként kell kezelnie, nem a következő végrehajtandó feladatként — az AI alapértelmezett működési módja a végrehajtás, nem az optimalizálás.

Az aktuális sprintben elfogadott döntések nem módosíthatók ugyanabban a sprintben, kivéve, ha hibásak, egymásnak ellentmondanak, vagy a Projektgazda kifejezetten ezt kéri.

## 6. Eltérések kezelése a dokumentációtól

Ha az AI jobb megoldást lát egy korábbi döntésnél, nem változtatja meg önkényesen — először javaslatot tesz, megindokolja, elkészíti a hatásvizsgálatot, és megvárja a Projektgazda döntését. Sem dokumentáció, sem implementáció nem tekinthető véglegesnek review nélkül.

A projekt célja nem a lehető leggyorsabb fejlesztés, hanem egy hosszú távon fenntartható, következetes, jól dokumentált rendszer létrehozása. Az egyszerű, tiszta és stabil megoldás mindig előnyt élvez a bonyolultabb, de "okosabb" megoldással szemben.


Execution Rule

A ROADMAP a projekt hivatalos végrehajtási terve. Az AI minden munkamenet elején köteles annak aktuális állapotát figyelembe venni. A következő feladatot a ROADMAP határozza meg, nem az AI.
