# ADR-0019: Image Relief Generator — Depth/Occlusion szemantika

Dátum: 2026-09-02
Státusz: Tervezet (fenntartott sorszám, tartalom a Phase 13.2 alfázis tárgya)
Döntéshozó: Horváth Gyula Attila (projektgazda) — a végleges döntés még nem született meg

## Kontextus

A ROADMAP Phase 13 (Image Relief Generator) megnyitásakor a Szoftverarchitekt azonosította, hogy a tervezési dokumentum (`docs/drafts/image_relief_generator/IMAGE_RELIEF_GENERATOR_PLANNING.md`, 17.10 szakasz) egy `elevation` + `ParentRef` + `TieBreakPriority` alapú Region Resolution (Depth/Occlusion) mechanizmust vezet be — jelentős, nem triviális algoritmus, amely korábbi feltételezéseket (kommutativitás, sorrend-függetlenség) von vissza, ezért erős ADR-jelölt (l. `RELIEF_GENERATOR_DOMAIN.md` 29. szakasza: "új domainobjektum").

Ez az ADR jelenleg kizárólag a sorszámot és a témát foglalja le, hogy a 13.2 alfázis tervezési munkája ne ütközzön sorszám-kiosztási kérdésbe.

## Döntés

Nyitott — a tényleges döntés tartalma a ROADMAP Phase 13.2 alfázisának saját Döntési javaslat → Hatásvizsgálat → Projektgazdai jóváhagyás lépéseinek eredményeként kerül majd ide.

## Mérlegelt alternatívák

Nyitott — a Phase 13.2 alfázis tárgya.

## Következmények

Nyitott — a Phase 13.2 alfázis tárgya.
