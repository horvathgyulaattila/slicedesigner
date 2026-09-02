# ADR-0019: Image Relief Generator — Depth/Occlusion szemantika

Dátum: 2026-09-02
Státusz: Elfogadva
Döntéshozó: Horváth Gyula Attila (projektgazda)

## Kontextus

Az Image Relief Generator Semantic World rétegében a Regionök hierarchikus szerkezetet alkotnak (`Children`, l. `IMAGE_RELIEF_REGION_MODEL.md`), ahol egy gyermek Region (pl. egy ablak egy házon) vizuálisan "belevésődik" a szülőjébe — occlusion-szerű hatást várunk. A kérdés: hogyan fejeződjön ki ez a mélységi viszony a domain modellben, amikor a Region-fa hierarchiafüggetlen `EffectSpec[]`-szé oldódik fel?

Két, korábban mérlegelt, de megcáfolt megközelítés:

- **Globális, hierarchia-vak magnitúdó-dominancia** (a nagyobb `|elevation|` nyer): a House (Raised, 0.5) / Window (Recessed, 0.2 abszolút mélységben) példán megcáfolva — a nagyobb magnitúdójú House "nyerne" a Window bemetszés fölött, ami vizuálisan hibás (az ablak eltűnne).
- **Mask-terület mint occlusion-jel**: elvetve — a Mask mérete a kép véletlenszerű tulajdonsága, nem a szerzői szándék kifejeződése, megbízhatatlan jel.

A projektgazda hipotézise szerint maga a szülő-gyermek hierarchia hordozhatja a mélységi viszonyt — ez a hipotézis bizonyítottnak bizonyult, egy fontos pontosítással: a gyermek `Contribution`-je nem abszolút, hanem **a szülő már resolvált értékéhez képest relatív**.

## Döntés

A Region Resolver a `Contribution` + `EffectiveDepthBehavior` párost a szülőlánc mentén **additívan felhalmozott, előjeles skalárrá** (`elevation`) alakítja:

```text
elevation(node) := ParentContext.elevation + signed(node.Contribution, EffectiveDepthBehavior(node))
signed(c, Raised)   := +c
signed(c, Recessed) := -c
Top-level Region: ParentContext.elevation := 0   (baseline)
```

Ebből következik, hogy a **lineage-menti occlusion nem külön mechanizmus** — mivel egy leszármazott `elevation`-je már additívan tartalmazza az ősei hatását, az ősök kizárása a kombinálás bemenetéből (a Phase 13.4 Effect Processing `S'` szűrője) nem veszít információt, "ingyen" adja vissza a kívánt occlusion-hatást.

Az `EffectSpec` modell ennek megfelelően egyszerűsödik: a korábban tervezett `Contribution`+`EffectiveDepthBehavior` pár helyett `elevation` + egy opcionális, strukturális (nem szemantikai) `ParentRef` mutató (az ős-utód reláció teszteléséhez) + egy opcionális `TieBreakPriority` (kizárólag a fennmaradó, nem-rokon, ellentétes irányú ütközés explicit feloldásához, l. Phase 13.4).

## Mérlegelt alternatívák

- **Globális, hierarchia-vak magnitúdó-dominancia** — megcáfolva a House/Window példán (fent).
- **Mask-terület mint occlusion-jel** — elvetve, megbízhatatlan (fent).
- **Nettósítás (összeadás) mint univerzális alapérték a maradék, nem-rokon ellentétes irányú esetre** — elvetve: mesterséges "lépcső"-artefaktumot hozna létre az érintett objektumban (a projektgazda eredeti gyanújának forrása, a "faág az ablak előtt" példával illusztrálva). Erre az esetre a döntés explicit konfliktus-jelzés, amit a felhasználó a `TieBreakPriority` mezőn keresztül oldhat fel — de ennek a mezőnek a tényleges beállítási mechanizmusa jelenleg (13.3-ban) még nincs megoldva, l. Következmények.
- **Explicit, minden Regionre kötelező z-order/rangsor mező** — elutasítva; a bevezetett `TieBreakPriority` ennél lényegesen szűkebb, opcionális, csak a maradék esetre vonatkozik.

## Következmények

- Az `EffectSpec` modell (`Mask`, `elevation`, `ParentRef`, `TieBreakPriority`) a Region Resolver (Phase 13.3) kimenete; a `combine` algoritmus (Phase 13.4) ezt a modellt fogyasztja.
- A `combine` a bemeneti *halmazra* nézve determinisztikus és order-independent marad, de már nem egyszerű, kommutatív aggregáció — strukturált, több lépcsős algoritmus (Phase 13.4 tárgya).
- **Nyitott, jövőre halasztott kérdés**: a `TieBreakPriority` mezőt jelenleg semmi nem tölti ki — sem a Region modell (13.1), sem az Image Interpretation (13.2), sem a Resolver (13.3) nem szolgáltat hozzá értéket, ezért a Resolver kimenetén mindig `None`. Emiatt egy tényleges, nem-rokon, ellentétes irányú ütközés esetén a Phase 13.4 `combine`-ja jelenleg mindig explicit konfliktus-hibát fog jelezni — a felhasználónak egyelőre nincs módja ezt megelőzni. A tényleges beállítási mechanizmus (Region-modell bővítés, Image Interpretation hozzárendelési fájl bővítése, vagy GUI-elem) külön, jövőbeli döntés tárgya.
