# Specifikáció Sztenderd

Státusz: Elfogadva
Tulajdonos:
Létrehozva: 2026-08-01
Utolsó módosítás: 2026-08-01
Kapcsolódó dokumentumok: [PROJECT_CONSTITUTION.md](PROJECT_CONSTITUTION.md), [ROADMAP.md](ROADMAP.md), [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md), [DOMAIN_MODEL.md](DOMAIN_MODEL.md), [ARCHITECTURE.md](ARCHITECTURE.md), [ENGINEERING_PRINCIPLES.md](ENGINEERING_PRINCIPLES.md), [PROMPT_STANDARD.md](PROMPT_STANDARD.md)

## Cél

Ez a dokumentum rögzíti a ROADMAP Phase 2 (Functional Specifications) alatt készülő, egy-egy domain engine-hez tartozó funkcionális specifikációk kötelező tartalmi sablonját, hogy azok konzisztens, egyértelmű és egymással összevethető szerkezetben készüljenek — a PROMPT_STANDARD.md mintájára.

A sablon minden, a `docs/specifications/` alatt készülő specifikációra vonatkozik (Mesh Import, Slice Engine, Gap System, Dowel System, Backplate, Numbering, Nesting, DXF Export — PROJECT_STRUCTURE.md 4. szakasza).

## 1. Kontextus

Az adott engine háttere: miért van rá szükség, hol helyezkedik el a pipeline-ban (ARCHITECTURE.md 3. szakasza), mely korábbi specifikációra vagy döntésre épül, ha van ilyen.

## 2. Felelősség

Az engine pontos, egy-két mondatos felelősség-megfogalmazása. Kiindulásként az ARCHITECTURE.md 2. szakaszában már rögzített Felelősség-mezőt kell használni, szükség esetén pontosítva — a specifikáció az ott rögzített felelősségi kört nem bővítheti és nem szűkítheti, kizárólag részletezheti (Constitution 8. elv).

## 3. Bemenet

Az engine bemeneteként szolgáló Domain Model fogalmak és azok attribútumai, típus- és érték-szinten (a DOMAIN_MODEL.md-ben rögzített attribútum-nevek pontosítása: típus, mértékegység — a Mértékegységek szakasz szerint —, érvényességi tartomány, kötelező vagy opcionális jelleg).

## 4. Kimenet

Az engine kimeneteként előálló Domain Model fogalmak és azok attribútumai, ugyanolyan részletességgel, mint a Bemenet szakaszban.

## 5. Paraméterek

Az engine működését szabályozó, kívülről állítható paraméterek listája: név, mértékegység, alapérték, érvényességi tartomány, jelentés. Rejtett konstans vagy "magic number" nem megengedett (Constitution 7. elv, Engineering Principles paraméterezhetőség).

## 6. Viselkedés

Az engine funkcionális logikájának szöveges, algoritmustól független leírása: milyen szabályok, döntési pontok és szélsőértékek jellemzik. Nem tartalmaz kódot, konkrét adatstruktúrát vagy implementációs döntést — ezek a Phase 4 feladatai.

## 7. Hibakezelés

Milyen érvénytelen, hiányos vagy ellentmondásos bemenet esetén milyen jellegű hibát kell jeleznie az engine-nek, fail-fast elven (Engineering Principles; CODING_STANDARDS.md 5. szakasza, egyedi kivétel-hierarchia). A konkrét kivétel-osztály neve itt még nem kötelező, a hibaeset és annak jellege igen.

## 8. Kapcsolódó engine-ek és Domain Model fogalmak

Explicit hivatkozás azokra az engine-ekre, amelyekkel az adott engine a Project-en keresztül adatot cserél (ARCHITECTURE.md 3. szakasza), és azokra a Domain Model fogalmakra, amelyekhez a specifikáció kapcsolódik.

## 9. Nyitott kérdések

Minden olyan pont, ami a specifikáció elkészítése során felmerült, de projektgazdai döntést igényel, mielőtt a specifikáció Elfogadott státuszba kerülhetne. Elfogadás előtt ez a szakasz nem maradhat megválaszolatlan tétellel.

## 10. Elfogadási kritériumok

Ellenőrizhető, konkrét feltételek listája, amelyek teljesülése esetén a specifikáció késznek és a Phase 4 implementációs promptjainak alapjául alkalmasnak tekinthető. Nem tartalmazhat olyan elvárást, amit a Bemenet/Kimenet/Paraméterek/Viselkedés szakaszok nem támasztanak alá.
