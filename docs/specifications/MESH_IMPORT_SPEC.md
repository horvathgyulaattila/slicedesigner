# Mesh Import — Specifikáció

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-01
Utolsó módosítás: 2026-08-01
Kapcsolódó dokumentumok: [PROJECT_CONSTITUTION.md](../PROJECT_CONSTITUTION.md), [ARCHITECTURE.md](../ARCHITECTURE.md), [DOMAIN_MODEL.md](../DOMAIN_MODEL.md), [SPECIFICATION_STANDARD.md](../SPECIFICATION_STANDARD.md), [ENGINEERING_PRINCIPLES.md](../ENGINEERING_PRINCIPLES.md)

## 1. Kontextus

A Mesh Import a pipeline első lépése (ARCHITECTURE.md 3. szakasz), ezért nem épül korábbi Phase 2 specifikációra. A rá épülő Slice Engine specifikáció ennek Kimenet szakaszára fog támaszkodni. A DOMAIN_MODEL.md már rögzíti a Mesh fogalmát, a koordinátarendszert (jobbsodrású, origó a forrásfájl szerint) és a mértékegységet (mm) — ez a spec ezeket pontosítja engine-szinten.

## 2. Felelősség

ARCHITECTURE.md-ből átvéve, nem bővítve: STL formátumú modell betöltése, validálása, Mesh domain objektum előállítása. Pontosítás: kizárólag STL formátum (ASCII és bináris egyaránt); a betöltés felelőssége kiterjed a nem-blokkoló figyelmeztetések (geometriai és egység-plauzibilitási) jelzésére is.

## 3. Bemenet

| Attribútum | Típus | Kötelező |
|---|---|---|
| STL fájl elérési útja | fájlrendszer-hivatkozás (string) | igen |
| origin_alignment | paraméter (lásd 5. szakasz) | nem (alapértelmezés: `none`) |

Elfogadott STL-változat: ASCII és bináris egyaránt, automatikus felismeréssel.

## 4. Kimenet

Mesh domain objektum:

| Attribútum | Típus | Mértékegység |
|---|---|---|
| geometriai reprezentáció | háromszögháló (csúcslista + háromszög-indexlista) | mm |
| forrásfájl-hivatkozás | string (fájlútvonal) | — |
| bounding box | min/max koordináta-hármas, 3 tengelyen | mm |
| validáltsági állapot | érvényes/érvénytelen jelző + figyelmeztetések listája (nem-manifold/nem-vízzáró geometria, egység-plauzibilitási probléma) | — |

## 5. Paraméterek

| Név | Alapérték | Érvényességi tartomány | Jelentés |
|---|---|---|---|
| `origin_alignment` | `none` | `{none}` (egyelőre egyetlen érvényes érték) | Origó kezelése betöltéskor — a forrásfájl koordinátái változatlanok maradnak. |
| `min_plausible_size_mm` | `1.0` | `> 0`, `< max_plausible_size_mm` | A bounding box legkisebb elfogadott mérete (mm) az egység-plauzibilitási figyelmeztetéshez. |
| `max_plausible_size_mm` | `3000.0` | `> min_plausible_size_mm` | A bounding box legnagyobb elfogadott mérete (mm) az egység-plauzibilitási figyelmeztetéshez. |

## 6. Viselkedés

1. STL fájl beolvasása (ASCII vagy bináris, automatikus felismeréssel).
2. Háromszögháló felépítése egyetlen Mesh objektumként — akkor is, ha a geometria több, egymással nem összefüggő testből áll.
3. Bounding box számítása mm-ben.
4. Geometriai validálás: nem-manifold/nem-vízzáró geometria észlelése esetén figyelmeztetés rögzítése — nem blokkolja a betöltést.
5. Egység-plauzibilitás ellenőrzése: ha a bounding box bármely mérete a `[min_plausible_size_mm, max_plausible_size_mm]` tartományon kívül esik, figyelmeztetés rögzítése — szintén nem blokkoló.
6. `origin_alignment` paraméter alkalmazása (jelenleg: nincs koordináta-módosítás).
7. Mesh objektum előállítása és visszaadása a Project felé.

## 7. Hibakezelés

Fail-fast elven:

* Fájl nem található / nem olvasható → **hiba**.
* Fájl sem ASCII, sem bináris STL szerkezetként nem ismerhető fel → **hiba**.
* Üres vagy nulla méretű geometria → **hiba**.
* Nem-manifold / nem-vízzáró geometria → **figyelmeztetés** (nem hiba; a tényleges geometriai hibakezelés a Slice Engine spec feladata).
* Egység-plauzibilitási probléma → **figyelmeztetés** (nem hiba; GUI felé továbbítva).

## 8. Kapcsolódó engine-ek és Domain Model fogalmak

* **Slice Engine** — bemenetként fogadja a Mesh Import kimenetét; a nem-manifold/nem-vízzáró figyelmeztetésből eredő tényleges hibakezelés (pl. nyitott kontúr egy adott szeleten) az ő specifikációjának feladata lesz.
* Domain Model: **Mesh**, **Project**.

## 9. Nyitott kérdések

Nincs megválaszolatlan pont — mind a hat, a specifikáció kidolgozása során felmerült kérdés lezárásra került a projektgazdával.

## 10. Elfogadási kritériumok

* A specifikáció mind a 10 szakaszt hiánytalanul tartalmazza.
* A Bemenet/Kimenet a DOMAIN_MODEL.md Mesh fogalmát típus- és mértékegység-szinten pontosítja, bővítés/szűkítés nélkül.
* Minden, a Viselkedésben hivatkozott küszöbérték és mód nevesített, dokumentált paraméter (Constitution 7. elv).
* A Hibakezelés egyértelműen elkülöníti a blokkoló hibákat a figyelmeztetésektől.
