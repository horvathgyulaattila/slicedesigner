# Prompt Sztenderd

Státusz: Elfogadva
Tulajdonos:
Létrehozva: 2026-07-30
Utolsó módosítás: 2026-08-01
Kapcsolódó dokumentumok: [PROJECT_CONSTITUTION.md](PROJECT_CONSTITUTION.md), [AI_WORKFLOW.md](AI_WORKFLOW.md)

## Cél

Ez a dokumentum rögzíti a jövőbeni implementációs feladatok prompt-sablonját, hogy azok konzisztens, egyértelmű és ellenőrizhető formában kerüljenek megfogalmazásra.

## 1. Kontextus

Az adott feladat háttere: miért van rá szükség, mely korábbi döntéshez vagy dokumentumhoz kapcsolódik, és — ha releváns — melyik korábban végrehajtott promptra épül vagy melyiket korrigálja. A promptok nem kerülnek archiválásra a repóban (a projektgazda döntése szerint a git history erre elegendő nyomvonal) — ezt a szakaszt ez teszi lehetővé: minden prompt önmagában, a beszélgetési előzmény nélkül is értelmezhető.

## 2. Cél

Pontosan mit kell elérnie a végrehajtásnak. Ha a feladat egy dokumentum tartalmának lecserélése, itt szerepel a végleges, szó szerint beillesztendő szöveg, kódblokkban. Ha fizikai fájlrendszer-műveletek (mappa/fájl létrehozása, törlése) is szükségesek, azok is itt kerülnek felsorolásra, egyértelműen, tétel szerint.

## 3. Kiindulási állapot

A célfájl (vagy célfájlok) jelenlegi, pontos tartalma — szó szerint idézve, kódblokkban —, hogy az Implementációs modell egyértelműen azonosíthassa, mit kell megváltoztatnia, és mit kell változatlanul hagynia.

## 4. Korlátozások

Explicit felsorolás arról, mi nem változhat: mely mezők, szakaszok, fájlok maradnak érintetlenül; hozzáadható-e ADR; létrehozható-e adott fájltípus (pl. `.py`, `pyproject.toml`) ezen a ponton. A korlátozások célja, hogy megakadályozzák a feladat önkényes kibővítését.

## 5. Módosítható fájlok

Pontos, teljes lista azokról a fájlokról (és szükség esetén mappákról), amelyeket a feladat érinthet.

## 6. Nem módosítható fájlok

Explicit felsorolás azokról a fájlokról/mappákról, amelyekhez a feladat nem nyúlhat — jellemzően "minden más fájl a `docs/` alatt", a `README.md`, és a fizikai forráskód-struktúra, ha az adott feladat nem érinti.

## 7. Elfogadási kritériumok

Ellenőrizhető, konkrét feltételek listája, amelyek teljesülése esetén a feladat eredménye elfogadható. Ezek közvetlenül leképezhetők kell legyenek a Cél szakaszban megadott tartalomra — nem szerepelhet köztük olyan elvárás, amit a Cél nem tartalmazott.

## 8. Tesztelési követelmények

Dokumentáció-only feladatoknál jellemzően "nincs automatizált teszt, manuális ellenőrzés a diff alapján". Kódot érintő feladatoknál (Phase 4-től kezdve) itt kerülnek rögzítésre a konkrét tesztelési elvárások, a `CODING_STANDARDS.md` szerint.

## 9. Definition of Done

Egy összefoglaló mondat, amely rögzíti, mikor tekinthető a feladat ténylegesen késznek: a tartalmi/fájlrendszer-változás megtörtént, semmilyen más fájl nem változott, és a módosítás review-ra kész állapotban van.
