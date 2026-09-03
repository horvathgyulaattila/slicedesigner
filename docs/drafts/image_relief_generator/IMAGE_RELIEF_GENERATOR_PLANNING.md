# Image Relief Generator — Tervezési állapot

> **Nem hivatalos repó-fájl.** Ez a dokumentum a `IMAGE_RELIEF_GENERATOR_PLANNING.md` tervezeti, chat-alapú frissítése — az Image Relief Generator előrehozott, előzetes tervezésének aktuális állapotát tartja nyilván. Utolsó frissítés: 2026-09-02, a **9.4** tervezési lépés (`relief_height_up`/`relief_height_down` végleges elnevezése/paraméterezése) **lezárása** alapján (ld. 17.11) — végleges nevek: `relief_height_raised`/`relief_height_recessed`. Korábbi frissítés: 2026-09-01, a 9.1+9.2 tervezési lépés eredményének visszavonása (Origin/frame-mechanizmus, ld. 17.9 átírva) ÉS a 9.3-újra (Depth/Occlusion szemantika) tervezési lépés lezárása (ld. 17.10) alapján.

## 1. Dokumentum célja

Ez a dokumentum az Image Relief Generator előzetes tervezésének aktuális állapotát tartja nyilván.

Az Image Relief Generator a Slice Designer `relief_generator` pluginján belül tervezett, későbbi image-based generátor.

**Fontos:** ez a tervezés a projekt aktuális fejlesztési fázisától független, előrehozott tervezési munka. Ebben a tervezési szakaszban nem cél az implementáció, a végleges specifikáció vagy a végleges projekt-dokumentáció elkészítése.

A dokumentum ezért jelenleg:

- stabil tervezési döntéseket;
- tervezési hipotéziseket;
- nyitott kérdéseket;
- elvetett koncepciókat;
- valamint a további tervezés sorrendjét

tartalmazza.

A dokumentum nem írja felül a Slice Designer aktuális ROADMAP-ját vagy már lezárt architekturális döntéseit.

---

# 2. A generátor célja

Az Image Relief Generator célja, hogy egy képből olyan, szemantikailag értelmezett reliefet hozzon létre, amelyből a Slice Designer downstream engine-jei közvetlenül **raw mesh-t** kapnak.

A generátor nem egyszerű image → heightmap konverter.

A tervezett folyamat:

```text
Image
  ↓
Image Interpretation
  ↓
Region hierarchy
  ↓
Region Resolution
  ↓
EffectSpec[]
  ↓
Relief / Effect Processing
  ↓
Relief Representation
  ↓
Geometry
  ↓
Raw Mesh
  ↓
Slice Designer engines
```

Nincs STL köztes lépés.

```text
Image
  ↓
Image Relief Generator
  ↓
raw mesh
  ↓
Slice Designer engines
```

---

# 3. Alapvető tervezési elv

A kép először **relief-szemantikává**, és csak később **geometriává** alakul.

A rendszer ezért legalább három absztrakciós világot különít el:

```text
SEMANTIC WORLD
    ↓
RELIEF WORLD
    ↓
GEOMETRY WORLD
```

## 3.1 Semantic World

```text
Image
  ↓
Image Interpretation
  ↓
Region hierarchy
  ↓
Region Resolver
  ↓
EffectSpec[]
```

A Semantic World feladata annak meghatározása, hogy a képen milyen relief-szempontból értelmezhető régiók vannak, és ezek hogyan járulnak hozzá a reliefhez.

## 3.2 Relief World

```text
EffectSpec[]
  ↓
Effect Processing
  ↓
Relief Representation
```

A Relief World feladata az egyes resolved relief contributionök együttes relief-értelmezése.

## 3.3 Geometry World

```text
Relief Representation
  ↓
Geometric Surface
  ↓
Raw Mesh
```

A Geometry World feladata a relief geometriai felületté, majd mesh-é alakítása.

---

# 4. Region modell

A jelenleg elfogadott minimális Region modell:

```text
Region
├── Mask
├── Contribution
├── DepthBehavior
└── Children
```

Nem szabad további mezőket bevezetni pusztán elméleti lehetőségek miatt.

A Region modellhez csak akkor nyúlunk vissza, ha egy konkrét új követelmény vagy stresszteszt tényleges hiányosságot mutat.

> **2026-09-01 — visszavonás:** a 9.1+9.2 tervezési lépésben (korábban ld. 17.9) bevezetett `Origin` mező és a hozzá tartozó frame-átvitel/composition-mechanizmus **visszavonásra került** — a 9.3-újra (Depth/Occlusion szemantika) tervezési lépés során derült ki, hogy az eredeti indoklás ("a Mask unresolved/resolved állapot-megkülönböztetésének numerikusan is relevánsnak kell maradnia") körkörös volt: sosem bizonyosodott be, hogy a Masknak valaha "unresolved, parent-relative" állapota kellene legyen. A Mask a Region-fa minden szintjén, kezdettől fogva a kép egyetlen, közös koordinátarendszerében, abszolút módon értelmezett — nincs "másik" tér, amiből fel kellene oldani. A részletes indoklást ld. 17.9 (átírva).

> **2026-09-01 (9.3-újra lezárása):** a szülő-gyermek kapcsolat occlusion-jelentésének kérdése lezárult — ld. 17.10. A `Region.Contribution` és `Region.DepthBehavior` a lineage mentén, additívan felhalmozott `elevation`-né alakul a Resolverben (7.4a); maga a `Children` hierarchia szemantikája (szemantikai/hierarchikus/kontextuális) változatlan marad, occlusion-jelentés nélkül — az occlusion nem magából a hierarchiából, hanem a belőle levezetett `elevation`+`ParentRef` párból adódik.

---

## 4.1 Mask

A `Mask` azt határozza meg:

> Hol érvényes a Region?

A Mask:

- spatial scope;
- nem geometriai objektum;
- nem heightmap;
- nem relief-profil;
- nem mesh.

> **2026-09-01 — lezárva:** a Mask a domain/architektúra szintjén funkcionális kontraktus marad (`member(p) → bool`); nincs domain-szintű materializált reprezentáció. Raszter/vektor/implicit függvény: Image Interpretation belső backend-döntés, nem architekturális kérdés.

> **2026-09-01 — visszavonás** (korábban: "a Mask két állapotot vehet fel a pipeline-ban: unresolved / resolved"): ez a megkülönböztetés megalapozatlannak bizonyult, ld. 4. szakasz és 17.9 (átírva). A Mask a Region-fa minden csomópontján, a kép egyetlen, közös koordinátarendszerében, **mindig abszolút** — nincs külön unresolved/resolved állapot, és nincs Resolver-végezte spatial resolution/composition lépés.

A Mask kontraktusának jelenleg egyetlen, bizonyítottan szükséges alapművelete a **membership query**: egy adott térbeli pontra eldönthető, hogy a Mask ott érvényes-e. A membership **bináris** — ld. 17.1/17.4 STABLE, a 4. tervezési lépésben lezárva. Intersection/union/difference **nem** része a Mask kontraktusának: ezeket a fogyasztó rétegek (pl. Effect Processing) vezetik le ismételt membership query-kből.

---

## 4.2 Contribution

A `Contribution` azt határozza meg:

> Milyen erősséggel járul hozzá a Region a reliefhez?

A jelenlegi értelmezés:

```text
0 = nincs saját hozzájárulás
>0 = egyre hangsúlyosabb hozzájárulás
```

Negatív Contribution nincs.

Fontos:

```text
Contribution ≠ physical height
```

A Contribution tehát nem közvetlen fizikai magasság- vagy mélységérték.

Például:

```text
Contribution = 0.8
```

nem jelenti automatikusan azt, hogy:

```text
0.8 mm
```

A fizikai értelmezés egy későbbi réteg feladata.

> **2026-09-01 (9.3-újra lezárása):** pontosítás — a `Contribution` a **szülő már resolvált `elevation`-jéhez képest relatív**, nem abszolút, globális skálán mért érték. Ez a felismerés a 9.3-újra kulcsmomentuma volt: a `Contribution` nem önmagában értelmezett "hangsúlyosság", hanem egy előjeles eltolás a szülő állapotához képest — ld. 7.4a, 17.10.

---

## 4.3 DepthBehavior

A `DepthBehavior` azt határozza meg:

> Milyen irányban viselkedik a Region a relief szempontjából.

A jelenleg használt példák:

```text
Raised
Recessed
Inherit
```

A DepthBehavior nem fizikai mélységet vagy magasságot jelent.

> **2026-09-01 (9.3-újra lezárása):** a `DepthBehavior` (irány) és az occlusion kérdésének viszonya lezárult: a `DepthBehavior` az `elevation` előjelének forrása (7.4a) — de önmagában továbbra sem old meg occlusiont; ahhoz a lineage-struktúra (`ParentRef`) és az additív felhalmozás is szükséges. Ld. 17.10.

---

## 4.4 Children

A `Children` a Regionök szemantikai hierarchiáját hordozza.

Például:

```text
Scene
└── House
    ├── Wall
    ├── Roof
    ├── Window
    └── Door
```

A parent-child kapcsolat:

- szemantikai;
- hierarchikus;
- kontextuális.

Nem geometriai Boolean-fa.

Egy Child Region kizárólag a **saját Mask-tartalmát** hordozza — nem tartalmazza és nem is kell tartalmaznia a Parent abszolút pozícióját vagy térbeli kiterjedését.

> **2026-09-01 (9.3-újra lezárása):** a parent-child kapcsolat occlusion-szerepének kérdése lezárult — a `Children` szemantikája **változatlanul, kizárólag** szemantikai/hierarchikus/kontextuális marad, occlusion-jelentés nélkül. Az occlusion nem magából a hierarchiából, hanem a belőle és a `Contribution`/`DepthBehavior`-ból számított `elevation`+`ParentRef` párból adódik (7.1a, 7.4a) — ld. 17.10.

---

# 5. Child Region térbeli viszonya a Parenthez

A Child Region Mask-ja — a 4.1-ben rögzítettek szerint — a kép közös, abszolút koordinátarendszerében értelmezett, ugyanúgy, mint bármely más Region Mask-ja; nincs a Parenthez képesti relatív értelmezés.

Ebből következik:

- a Child térbeli kiterjedése nem korlátozódik a Parent tartományára;
- kilóghat a Parent térbeli tartományából;
- nem kerül automatikusan clippingre;
- a parent-child kapcsolat önmagában nem jelent geometriai Boolean műveletet.

Például:

```text
House
└── Roof
```

esetén a Roof túlnyúlhat a House falának térbeli tartományán — ez triviálisan adódik abból, hogy mindkét Mask önmagában, abszolút módon van definiálva, semmilyen külön garancia vagy mechanizmus nem szükséges hozzá.

> **2026-09-01 — visszavonás:** ez a szakasz korábban "Parent-relative spatial definition" címmel, és egy 5.1 "Resolution / Composition" alszakasszal szerepelt, amely a Child Mask-ját a Parenthez képest relatívnak, és a Resolver egy külön, `frame`-alapú átviteli (composition) lépését tekintette szükségesnek. Ez a fogalom — az `Origin` mezővel és a "Mask unresolved/resolved állapota" megkülönböztetéssel együtt — visszavonásra került, ld. 4. szakasz és 17.9 (átírva). Nincs Resolver-végzett spatial composition lépés; a korábbi 5.1 alszakasz emiatt megszűnt.

> **Megjegyzés (2026-09-01):** ez a szakasz **kizárólag térbeli (spatial)** kérdésekről szól — a Mask abszolút voltáról. A **behaviorális** (Contribution/DepthBehavior) relatívság egy másik, önálló fogalom — ld. 4.2, 7.4a, 17.10. A kettő nem tévesztendő össze.

---

# 6. ReliefRole — elvetve

A korábbi stressztesztek alapján a `ReliefRole` nem része a minimális modellnek.

Nem vezetünk be például ilyen kategóriákat:

```text
PrimaryForm
SecondaryForm
Detail
SurfaceDetail
```

Indok:

- nem szükségesek a relief-hozzájárulás kifejezéséhez;
- a hierarchia + Mask + Contribution + DepthBehavior elegendő;
- könnyen redundánssá válhatnának;
- feldolgozási kategóriákat nem akarunk előre beégetni a domainmodellbe.

Ha később konkrét követelmény indokol hasonló fogalmat, azt az adott követelményből kiindulva kell újratervezni.

---

# 7. Region Resolution

*(3. tervezési lépés eredménye, ld. 17.3)*

A Regionök feloldása Resolveren keresztül történik:

```text
Region
   +
ParentContext
   ↓
Resolver
   ↓
EffectSpec
```

## 7.0 Definíció és felelősség

A Region Resolver a Region-fa relatív, hierarchiafüggő állapotát alakítja át EffectSpec[] konkrét, hierarchiafüggetlen állapotává, két, egymásra épülő lépésben:

| Lépés | Forrás | Cél | Mechanizmus |
|---|---|---|---|
| 1. Irány feloldása | `DepthBehavior = Inherit` (4.3) | konkrét `EffectiveDepthBehavior` (belső, tranziens — nem kerül át az EffectSpecbe) | öröklés a szülőláncból (7.4) |
| 2. Elevation felhalmozása | `Contribution` (4.2) + a fenti `EffectiveDepthBehavior` | `elevation` (végleges EffectSpec-mező, 8.) | additív akkumuláció a szülő már resolvált elevation-jéhez képest (7.4a) |

> **2026-09-01 (9.3-újra lezárása):** ez a szakasz korábban (a Mask/Origin-visszavonás után) egyetlen, "Behavioral" dimenziót írt le, `EffectiveDepthBehavior` kimenettel. A 9.3-újra lezárásaként ez bővült: az `EffectiveDepthBehavior` mostantól tisztán belső, tranziens köztes érték — nem kerül át az EffectSpecbe —, helyette a Resolver a felhalmozott `elevation`-t termeli, ld. 7.4a, 8., 17.10.

Minden bejárt Region — nem csak a levelek — pontosan egy EffectSpecet termel; a Region-csomópontok száma megegyezik az EffectSpec-ek számával.

A `Region.Mask` a Resolveren keresztül **változtatás nélkül** kerül át `EffectSpec.Mask`-be — a Masknak nincs `Inherit`-szerű állapota (4.1), ezért ehhez nincs szükség szülői kontextusra. *(2026-09-01: a `Region.Contribution` már nem kerül változtatás nélkül át — bemenete, nem kimenete az `elevation` számításának, ld. 7.4a.)*

A Region-fa bejárása állítja elő az `EffectSpec.ParentRef` mezőt is — ld. 7.1a.

**Nincs szükség köztes, tisztán szervezési célú Region-fogalomra**: a `Contribution = 0` + `DepthBehavior = Inherit` kombináció a meglévő minimális Region-modell (4. szakasz) szabályos, speciális kezelést nem igénylő eleme — a Resolver ezt semmilyen speciális esetkezelés (felismerés vagy eltérő feldolgozás) nélkül, a normál mechanizmussal dolgozza fel.

## 7.1 ParentContext

A `ParentContext` a Resolver által, resolválás közben használt, tranziens kontextus.

A `ParentContext` **nem része az EffectSpecnek** — resolválás után eldobódik.

> **2026-09-01 — visszavonás:** a `ParentContext` korábban egy második mezőt (`frame`) is hordozott, a Mask spatial resolution/composition lépéséhez. Ez megszűnt, ld. 4.1, 5., 17.9 (átírva).

> **2026-09-01 (9.3-újra lezárása):** a `ParentContext` egy — a visszavont `frame`-től független — új mezőt kapott: `elevation`. Ez **nem** spatial adat, hanem a behaviorális felhalmozás alapja, ld. 7.4a, 17.10.

A `ParentContext` pontosan két mezőt hordoz:

```text
ParentContext
├── effectiveDepthBehavior   (a szülő resolvált EffectiveDepthBehaviorja — tranziens, csak az Inherit-lánc feloldásához)
└── elevation                (a szülő resolvált, felhalmozott elevation-je)
```

Nem tartalmaz:

- szemantikai identitást (pl. hogy a szülő „House" volt — ld. 11. szakasz);
- spatial/frame-adatot (nincs rá szükség, ld. 5. szakasz).

A gyerekeknek szánt kimenő `ParentContext`-et minden csomópont a **saját, már feloldott** értékeiből építi fel — sosem a nyers `Region`-mezőkből. Ez adja a többszintű öröklés (7.4, 7.4a) helyes, rekurzív alapját.

**Top-level Region** esetén (ld. 4.4, 17.2 — a Region-fa gyökér nélkül, egy vagy több top-level Regionből is állhat; a „top-level Region" terminológia szándékosan nem „gyökér", hogy ne keveredjen a 17.2 STABLE struktúra-döntésével) nincs szülő, tehát nincs beérkező `ParentContext`:

- `DepthBehavior = Inherit` egy top-level Regionön **kontraktussértés**, nem defaultolt eset;
- **baseline elevation**: top-level Region `elevation`-jének felhalmozási alapja `0` (nincs szülői elevation, amihez képest eltolódna).

## 7.1a ParentRef — az EffectSpec strukturális mutatója

*(9.3-újra tervezési lépés eredménye, ld. 17.10)*

Az `EffectSpec.ParentRef` egy opcionális (top-level Regionnél `None`) mutató a szülő Region már létrehozott EffectSpecjére. Kizárólag azt teszi lehetővé, hogy az Effect Processing réteg (12. szakasz) két aktív EffectSpec-ről eldöntse, van-e köztük ős-utód (lineage) reláció — **nem** szemantikai azonosító (nem hordozza, hogy a szülő "House" vagy "Roof" volt, ld. 11. szakasz), és **nem** `Priority`/`BlendMode`/`MergeRule`/`BooleanOperation` (9. szakasz).

A `ParentRef` a Resolver ugyanazon bejárásában áll elő, mint a többi mező — a konkrét implementációs mechanizmus (pl. index a kimeneti EffectSpec[] tömbben, vagy objektumreferencia) domain-szinten nem rögzített, analóg a Mask konkrét reprezentációjával (4.1).

## 7.2 Traverzálás

A Resolvernek egyetlen kemény függőséget kell tiszteletben tartania:

> Egy csomópont csak azután resolválható, hogy a szülője resolválva van.

Ez egy **parciális rendezés**, nem teljes, lineáris sorrend. Ebből következően:

- testvér Regionök között nincs sorrendi elvárás (összhangban a 17.2 STABLE „nincs elvárás testvérek koordinációjára" döntésével);
- különböző top-level Regionök (erdő) között sincs sorrendi elvárás;
- egy adott ág mélysége mentén szigorú a sorrend, de ágak között nincs — egy mélyebb leszármazott soha nem várja meg egy másik ág resolválását, csak a saját őseiét.

A bejárás emiatt egyetlen áthaladású (single-pass) és per-részfa független: minden csomópontot pontosan egyszer resolválunk, és nincs a modellben olyan adat, ami gyerektől szülő felé áramlana. A konkrét bejárási implementáció (rekurzió, explicit munkalista, párhuzamos feldolgozás) tisztán implementációs kérdés, nem domain-döntés.

## 7.3 [VISSZAVONVA — korábban: Frame-átvitel (composition), funkcionális kontraktus és konkrét mechanika]

> **2026-09-01 — visszavonás:** ez a szakasz a Mask parent-relative → resolved spatial átalakítását írta le (`frame(N) := frame(P) + N.Origin`, `reinterpret(p, frame) := p − frame`). A teljes mechanizmus visszavonásra került, mert a mögöttes feltételezés (a Masknak "unresolved, parent-relative" állapota van) megalapozatlannak bizonyult — a Mask mindig abszolút, ld. 4.1, 5. szakasz, 17.9 (átírva). A szakaszszám megtartva a kereszthivatkozások épsége miatt; tartalom törölve.

## 7.4 `DepthBehavior = Inherit` feloldása

A Resolver egyetlen, minden szinten azonos, egylépéses szabályt alkalmaz:

```text
EffectiveDepthBehavior(node) :=
    ha node.DepthBehavior ≠ Inherit  →  node.DepthBehavior
    egyébként                        →  ParentContext.effectiveDepthBehavior
```

Mivel a `ParentContext.effectiveDepthBehavior` mindig a szülő **már feloldott** értéke (ld. 7.1), ez a szabály — a 7.2-ben rögzített szülő→gyerek parciális rendezésre támaszkodva — tetszőlegesen hosszú `Inherit`-láncot helyesen felold, anélkül hogy a Resolvernek fel kellene „mászni" a láncban: minden szint csak a közvetlenül fölötte lévő, már konkrét értéket látja.

> **2026-09-01 (9.3-újra lezárása):** ez a szabály változatlanul, tranziensen érvényes — az eredménye (`EffectiveDepthBehavior`) mostantól nem kerül közvetlenül az EffectSpecbe, hanem a 7.4a bemenete. Ld. 17.10.

## 7.4a Elevation felhalmozása

*(9.3-újra tervezési lépés eredménye, ld. 17.10)*

Az `EffectiveDepthBehavior` (7.4) feloldása után a Resolver egy második, arra épülő szabályt alkalmaz:

```text
elevation(node) := ParentContext.elevation + signed(node.Contribution, EffectiveDepthBehavior(node))
signed(c, Raised)   := +c
signed(c, Recessed) := -c

Top-level Region: ParentContext.elevation := 0   (baseline)
```

Ez adja az `EffectSpec.elevation` végleges értékét (8. szakasz) — a `Contribution` és az `EffectiveDepthBehavior` innentől **nem** kerül át külön-külön az EffectSpecbe, a jelentésük teljes egészében az `elevation`-ban összegződik.

Példa (a `House`/`Window` occlusion-forgatókönyv):

```text
elevation(House)  = 0 + signed(0.5, Raised)    = 0.5
elevation(Window) = 0.5 + signed(0.3, Recessed) = 0.2
```

## 7.5 Réteghatár (mit nem kell tudnia a Resolvernek)

- **Fizikai relief-jelentés**: a `Contribution` és a `DepthBehavior`/`EffectiveDepthBehavior` fizikai (magasság/mélység) jelentését a Resolver nem ismeri; ezeket opak értékként/címkeként kezeli és adja tovább (4.2, 4.3).
- **Effect Processing**: több EffectSpec együttes relief-hatását, a `combine`-t, falloffot, smoothingot, blendinget, Intersection/Union/Difference műveleteket a Resolver nem végzi el és nem is ismeri (9., 10., 12. szakasz; 17.1 REJECTED). A Resolver csak azt garantálja, hogy az átfedés a resolved Maskok membership query-jével eldönthető legyen.
- **Geometry World**: relief representation, geometric surface, Z-tartomány, base plane, mesh, sampling, watertightness kérdései teljesen kívül esnek a Resolver hatókörén (13–15. szakasz).
- **Eredeti szemantikai identitás kifelé**: a Resolver a bejáráshoz és a `ParentContext`-hez belsőleg használja a hierarchia-információt, de a *szemantikai* identitás (pl. hogy a szülő „House" volt) nem kerül át az EffectSpecbe (11. szakasz).

> **2026-09-01 (9.3-újra lezárása):** ez a réteghatár-tétel felülvizsgálata lezárult — **pontosítva, nem visszavonva**: a *szemantikai* identitás (név/típus) továbbra sem kerül át. Egy szűk, nem-szemantikai `ParentRef` mutató (7.1a) igen átkerül — kizárólag ős-utód-reláció tesztelésére, ld. 17.10.

---

# 8. EffectSpec

*(2026-09-01, 9.3-újra lezárása: a modell módosult, ld. 17.10)*

A minimális EffectSpec modell:

```text
EffectSpec
├── Mask
├── elevation           (előjeles, felhalmozott skalár)
├── ParentRef            (Optional — ős-utód reláció teszteléséhez, ld. 7.1a)
└── TieBreakPriority     (Optional[int] — kizárólag a maradék, nem-rokon ellentétes irányú ütközésre, ld. 12.3)
```

Az EffectSpec jelentése:

> Egy Region már feloldott, önálló, a lineage mentén már felhalmozott relief-hozzájárulása.

> **2026-09-01 — visszavonás** (korábban: `EffectSpec ├── Mask ├── Contribution └── EffectiveDepthBehavior`): ez a modell a 9.3-újra tervezési lépés lezárásaként módosult. A `Contribution` és `EffectiveDepthBehavior` külön-külön már nem kerül át az EffectSpecbe — a jelentésük az `elevation` mezőben, a szülőlánc mentén már felhalmozva jelenik meg (7.4a). Két új, opcionális mező került be: `ParentRef` (occlusion/lineage-teszteléshez, 7.1a) és `TieBreakPriority` (a fennmaradó, nem-rokon ellentétes irányú ütközések explicit, opcionális feloldásához, 12.3).

Például:

```text
Region:
Contribution = 0.3, DepthBehavior = Recessed

Parent (már resolvált):
elevation = 0.5

EffectSpec:
elevation = 0.5 + signed(0.3, Recessed) = 0.2
```

---

# 9. EffectSpec határai

> **2026-09-01 (9.3-újra lezárása):** ez a szakasz felülvizsgálata lezárult. Az EffectSpec továbbra sem geometriai objektum, és a lent felsorolt fogalmakat továbbra sem tartalmazza. Az egyetlen, most bevezetett kiegészítés (`TieBreakPriority`, ld. 8. szakasz) **nem** azonos az itt korábban kizárt, általános `Priority` fogalommal — a különbséget ld. 17.10.

Az EffectSpec nem geometriai objektum.

Nem tartalmaz:

- mesh-t;
- STL-t;
- heightmapet;
- magasságprofilt;
- smoothingot;
- falloffot;
- blending algoritmust;
- geometriai Boolean műveletet.

Nem vezetünk be az EffectSpecbe ilyen fogalmakat:

```text
BlendMode
MergeRule
BooleanOperation
```

> **2026-09-01:** a `Priority` tétel a fenti tiltólistából törölve — helyette ld. `TieBreakPriority` (8. szakasz), ami ennek egy jóval szűkebb, opcionális, kizárólag a 12.3-ban leírt maradék ütközési esetre vonatkozó változata. Az általános, minden EffectSpecre kötelező rangsor-fogalom továbbra is elutasított, ld. 17.10.

Az EffectSpec-ek kombinációja nem az EffectSpec felelőssége.

---

# 10. Több EffectSpec

> **2026-09-01 (9.3-újra lezárása):** a felülvizsgálat lezárult, ld. 18.5/17.10 — az itt leírt alapelvek (EffectSpec = önálló resolved relief contribution; a sorrend nem hordoz szemantikát; az átfedés önmagában nem igényel új domainfogalmat) mind STABLE-ként megerősítve.

Egy Region-hierarchiából több EffectSpec keletkezhet:

```text
Region A → EffectSpec A
Region B → EffectSpec B
Region C → EffectSpec C
```

Az EffectSpec:

> egy önálló resolved relief contribution.

Az EffectSpec-ek sorrendje önmagában nem hordoz szemantikát.

Két EffectSpec Maskja átfedhet:

```text
Mask A ∩ Mask B ≠ ∅
```

Ez önmagában nem igényel új domainfogalmat.

Például:

```text
Scene
├── Tree
└── House
```

esetén a Tree és House lehetnek egymást térben átfedő testvérek. Mindkettő saját Maskkal és `elevation`-nel rendelkezhet.

Az átfedő contributionök együttes értelmezése a későbbi Effect Processing réteg felelőssége.

---

# 11. A Semantic World határa

A jelenlegi modell szerint:

```text
Image
  ↓
Image Interpretation
  ↓
Region hierarchy
  ↓
Region Resolver
  ↓
EffectSpec[]
```

Az `EffectSpec[]` a Semantic World kimenete.

Ezen a ponton a következő rétegnek már nem szükséges ismernie az eredeti szemantikai objektumazonosságot.

Például nem kell tudnia, hogy egy adott EffectSpec:

```text
House
```

vagy:

```text
Roof
```

volt.

A resolved relief contribution számít.

> **2026-09-01 (9.3-újra lezárása):** a hierarchia-információ egy szűk, nem-szemantikai formában (`ParentRef`, 7.1a) mégis átkerül a resolved rétegbe — de a *szemantikai* identitás (a fenti "House"/"Roof" elnevezés) továbbra sem. Ld. 17.10.

---

# 12. Effect Processing

*(4. tervezési lépés eredménye, ld. 17.4)*

A következő tervezési réteg:

```text
EffectSpec[]
       ↓
Effect Processing
       ↓
Relief Representation
```

## 12.1 Definíció és felelősség

*(2026-09-01, 9.3-újra lezárása: a `combine` végleges definíciója, ld. 17.10)*

Az Effect Processing egyetlen felelőssége a `combine` függvény: egy adott térbeli ponton aktív EffectSpec-ek `elevation`-jéből, ős-utód (`ParentRef`) relációjából és — a maradék esetekre — `TieBreakPriority`-jából egyetlen `ReliefValue`-t állít elő.

```text
active(p) := { s ∈ EffectSpec[] : s.Mask.member(p) }
S'(p)      := { s ∈ active(p) : nincs s-nek active(p)-ben lévő leszármazottja (ParentRef-lánc mentén) }

combine(p) :=
    0                                            ha S'(p) = ∅
    elevation(az az egy tag)                     ha |S'(p)| = 1
    envelope(S'(p))                              ha |S'(p)| ≥ 2, egyetlen irányban (mind pozitív vagy mind negatív elevation)
    tiebreak(S'(p))                               ha |S'(p)| ≥ 2, vegyes irányban — ld. 12.3

envelope(specs) := elevation(s), ahol s az a tag, amelyre |elevation(s)| maximális
```

Az `S'(p)` szűrő ("nincs aktív leszármazottja") **automatikusan** megoldja a lineage-menti occlusiont — nincs rá külön, irány-feltételes lépés: mivel az `elevation` már additívan felhalmozott (7.4a), egy leszármazott elevation-je már tartalmazza az ős hatását, ezért az ős kizárása a `combine` bemenetéből nem veszít információt.

## 12.2 Kötelező tulajdonságok

> **2026-09-01 (9.3-újra lezárása):** a kommutativitás-tétel módosult, ld. lent — a korábbi ⚠️ felülvizsgálat lezárult.

- **Determinisztikusság a bemeneti *halmazra* nézve**: a `combine(p)` kimenete kizárólag az `active(p)` halmaztól és a statikus `ParentRef`/`TieBreakPriority` struktúrától függ — nem függ attól, milyen sorrendben dolgozzuk fel a specifikációkat. *(Ez felváltja a korábbi, szigorúbb "kommutativitás" tételt — a `combine` már nem egyszerű, kommutatív aggregáló függvény a teljes bemeneti halmazon, hanem egy strukturált, több lépcsős algoritmus, amely maga is order-independent, de nem "bármely két bemenet felcserélhető" értelemben kommutatív.)*
- **Monotonitás azonos irányú átfedésre**: ha `S'(p)`-ben minden tag azonos irányú, a kombinált hatás (`envelope`) sosem kisebb, mint bármelyik önálló tag `|elevation|`-je — ez triviálisan teljesül, mivel az `envelope` maga a legnagyobb magnitúdójú tag értéke.

## 12.3 A maradék eset — nem-rokon, ellentétes irányú átfedés

*(2026-09-01, 9.3-újra lezárása — korábban: "Overlap Resolution — cserélhető stratégia-kontraktus", OPEN)*

Miután a lineage-menti occlusion (`S'` szűrő) és az azonos irányú, nem-rokon átfedés (`envelope`) kezelve van, egyetlen eset marad, amire a bemenetben (`elevation`, `ParentRef`) strukturálisan nincs elegendő információ: `S'(p)`-ben legalább egy pozitív és legalább egy negatív `elevation`-ű, egymással nem rokon (nincs ős-utód reláció) tag van egyszerre aktív.

```text
tiebreak(S'(p)):
    pos := { s ∈ S'(p) : elevation(s) > 0 }
    neg := { s ∈ S'(p) : elevation(s) < 0 }
    ha pos = ∅ vagy neg = ∅:
        combine(p) := envelope(pos ∪ neg)          # nem valódi ütközés, ld. 12.1
    különben:                                        # valódi, nem-rokon, ellentétes irányú ütközés
        érintettek := pos ∪ neg
        ha ∃ s ∈ érintettek, s.TieBreakPriority definiált, és ez a maximális az érintettek között:
            combine(p) := elevation(s)
        különben:
            KONFLIKTUS — combine(p) nincs definiálva ezen a ponton, ld. lent
```

**Nincs hallgatólagos alapérték** (sem nettósítás, sem magnitúdó-dominancia) erre az esetre — mindkettő bizonyítottan (18.5, és a 9.3-újra "faág az ablak előtt" példája) vagy mesterséges "lépcső"-artefaktumot, vagy tartalomfüggő, véletlenszerű helyes/helytelen eredményt adna. Ehelyett a rendszer **explicit konfliktus-jelzést** ad, és a felhasználó a `TieBreakPriority` mezőn keresztül, utólag, célzottan feloldhatja — pontosan azon EffectSpec-ekre, ahol ez ténylegesen szükséges, nem globálisan minden Regionre.

A konfliktus-jelzés konkrét technikai mechanizmusa (kivétel, figyelmeztetés+preview, mely réteg dobja) implementációs kérdés, nem architekturális döntés — analóg a Mask konkrét reprezentációjával (4.1).

## 12.4 Falloff — opcionális, réteg-utáni transzformáció

A falloff/simítás nem a Mask vagy a membership fogalma — a membership bináris marad (ld. 4.1, 17.4 STABLE). Ha a jövőben konkrét követelmény igazolja a szükségességét, a falloff a `combine` kimenetén (a `ReliefValue`-mezőn) végzett, opcionális, utólagos transzformációként valósul meg, nem a membership-lekérdezés bővítéseként.

Fontos: a bináris membership nem korlátozza a relief lehetséges formáját — a forma-szabadság (pl. lekerekített szélek) a külön, opcionális falloff-réteg meglététől függ, nem a Mask bináris jellegétől.

A konkrét hatókör pontosítását ld. 13.5 (5. tervezési lépés): a transzformáció a teljes Relief Representation függvényen értelmezett, nem pontonkénti.

## 12.5 Réteghatár (mit nem kell tudnia az Effect Processingnek)

- az eredeti szemantikai identitást (pl. hogy egy EffectSpec „House" vagy „Roof" volt — 11. szakasz);
- a teljes Region-hierarchiát és a ParentContextet (Resolver belső ügye — 7. szakasz) — *(2026-09-01: pontosítva — az Effect Processing a `ParentRef`-en keresztül igenis ismeri az ős-utód relációt, de nem a teljes fát, nem a ParentContextet, és nem a szemantikai identitást)*;
- a Geometry World fogalmait (base plane, Z-tartomány, mesh, sampling, watertightness — 14–15. szakasz);
- a Mask konkrét reprezentációját, amíg a `member(p)` kiértékelhető (ld. 17.9, lezárva).

---

# 13. Relief Representation

*(5. tervezési lépés eredménye, ld. 17.5)*

Az Effect Processing eredménye egy köztes relief-reprezentáció.

Ez:

- még nem mesh;
- még nem STL;
- nem feltétlenül azonos egy hagyományos heightmappel.

## 13.1 Definíció és felelősség

A Relief Representation egyetlen felelőssége hidat képezni az Effect Processing (12. szakasz) és a Geometry World (14. szakasz) között: hordozza a downstream fizikai leképezéshez szükséges információt, anélkül hogy maga fizikai jelentést, mértékegységet vagy konkrét materializációt tartalmazna.

## 13.2 Minimális, bizonyítottan szükséges kontraktus — funkcionális forma

A Relief Representation minimális, bizonyítottan szükséges kontraktusa: egy **"pont → ReliefValue" függvény**, reprezentációfüggetlen — analóg a Mask funkcionális kontraktusával (4.1).

Konkrét materializáció (raszter/rács/egyéb) ezen a tervezési lépésen sem bizonyult szükségesnek: a downstream (Geometry World, Mesh Construction) igényei function-kompozícióval kielégíthetők, a mintavételezés (sampling/resolution) explicit, dokumentált módon a Geometry → Raw Mesh lépés (15. szakasz) felelőssége — nem ez a réteg, és nem is a Geometry World általában (14. szakasz).

## 13.3 Üres bemenet — perem-feltétel

Ha egy ponton egyetlen EffectSpec sem ad membershipet, a `combine` bemeneti halmaza üres. Ez kötelezően definiált, és értéke nulla:

```text
combine(∅) := 0
```

Ez minden esetre kötelező perem-feltétel — biztosítja, hogy a maszkolatlan terület jól definiált, a Geometry World számára semleges (base plane-nek megfelelő) bemenet legyen.

## 13.4 `ReliefValue` doménje

A `ReliefValue` minimálisan bizonyítottan szükséges tartalma egy **előjeles skalár**:

```text
pozitív  → Raised irányú nettó hatás
negatív  → Recessed irányú nettó hatás
0        → nincs hatás
```

> **2026-09-01 — a korábbi ⚠️ jegyzet feloldva (9.3-újra lezárása):** a `combine` végleges definíciója (12.1–12.3) is előjeles skalárt ad — a `ReliefValue` doménje változatlan marad.

## 13.5 Falloff/smoothing — pontosítás

A 12.4-ben rögzített, a `combine` kimenetén végzett, opcionális transzformáció a teljes Relief Representation **függvényen** értelmezett (`Relief Representation → Relief Representation`), nem pontonkénti (`ReliefValue → ReliefValue`) transzformáció: egy neighborhood-alapú művelet (pl. élkerekítés) nem vezethető le egyetlen pont értékéből.

Ez nem mond ellent a 12.4 STABLE döntésnek, csak pontosítja a hatókörét.

## 13.6 Fizikai határ a Geometric Surface felé

```text
ReliefValue ≠ physical height
```

— a 4.2 elvének kiterjesztése erre a rétegre. Mértékegység, base plane, Z-tartomány kizárólag a Relief → Geometry lépés (14. szakasz) tárgya; a Relief Representation ezt tudatosan nem tartalmazza.

## 13.7 Réteghatár (mit nem kell tudnia a Relief Representationnek)

- az eredeti szemantikai identitást (11. szakasz);
- a `combine` belső algoritmusát — csak a kimeneti kontraktusát (12.1–12.3);
- a Geometry World fogalmait (base plane, Z-tartomány, mesh, sampling — 14–15. szakasz);
- a Mask konkrét reprezentációját (ld. 17.9, lezárva).

---

# 14. Relief → Geometry

*(6. tervezési lépés eredménye, ld. 17.6)*

A következő lépés:

```text
Relief Representation
        ↓
Geometric Surface
```

Itt történik a relief fizikai geometriai értelmezése — ez a réteg választja el a relatív relief-szemantikát a fizikai geometriától.

## 14.1 Definíció és felelősség

A Geometric Surface egyetlen felelőssége a Relief Representation (13. szakasz, előjeles `ReliefValue`) fizikai geometriává alakítása: fizikai `Z`-koordinátát rendel minden ponthoz, amit a Geometry → Raw Mesh lépés (15. szakasz) mesh-építéshez felhasználhat.

## 14.2 Absztrakciós forma — funkcionális kontraktus

A Geometric Surface — a Relief Representation (13.2) és a meglévő, implementált `HeightField`/`ReliefGeometry` mintázatának analógiájára — **funkcionális kontraktus** marad, materializáció nélkül: a mintavételezés (sampling/resolution) explicit, dokumentáltan a Geometry → Raw Mesh lépés (15. szakasz) felelőssége.

A kontraktus két részre bomlik:

```text
raw_relief: (x,y) -> ReliefValue                       # pass-through a Relief Representationből
physical_z(raw_value, v_min, v_max) -> Z                # tiszta, mintavételezés-mentes leképezési képlet
```

A `v_min`/`v_max` (a ténylegesen realizált `ReliefValue`-szélsőértékek) előállítása **nem** a Geometric Surface felelőssége — ld. 14.8.

## 14.3 Viszony a meglévő Geometry World-höz

A meglévő, implementált `HeightField`/`ReliefGeometry` kontraktus (a Wave/Voronoi/Crater/Dune/WoodGrain generátorok közös rétege, Phase 8–11, lezárva) **változatlan** marad — ez a lépés nem nyúl hozzá.

Az Image Relief Generator Geometric Surface-e egy azzal **párhuzamos, hasonló szerepű, de eltérő alakú, önálló kontraktus**, nem a meglévő típusok újrafelhasználása vagy kiterjesztése. Az eltérés oka: a meglévő `HeightField.query(x,y) -> [0,1]` előjel nélküli, önmagában kész értéket ad, míg a Relief Representation (13.4) tudatosan **előjeles** `ReliefValue`-t definiált — ez a két kontraktus strukturálisan nem azonos (ld. 14.9 is).

## 14.4 `ReliefValue` → fizikai `Z` — nullponthoz rögzített, kétirányú leképezés

A leképezés a ténylegesen realizált `ReliefValue`-szélsőértékekhez adaptívan igazodik, nem előre rögzített tartományhoz:

```text
V(p) := ReliefValue(p)
V_max := max(0, sup_p V(p))        # a Raised oldal realizált terjedelme
V_min := min(0, inf_p V(p))        # a Recessed oldal realizált terjedelme

Z(p) :=
    base_thickness                                             ha V(p) = 0
    base_thickness + (V(p) / V_max) * relief_height_raised      ha V(p) > 0   (V_max > 0 ekkor garantált)
    base_thickness − (V(p) / V_min) * relief_height_recessed    ha V(p) < 0   (V_min < 0 ekkor garantált)
```

A semleges terület (`ReliefValue = 0` — pl. a `combine(∅) := 0` peremfeltétel szerinti maszkolatlan háttér, ld. 13.3) emiatt **mindig pontosan `base_thickness`-en ül**, függetlenül attól, hogy a kép máshol milyen szélsőséges Raised/Recessed értékeket tartalmaz — a felfelé és lefelé irányuló skálázás egymástól **függetlenül** normalizált, nem egyetlen közös, globális stretch.

Ez a leképezés egyúttal **lezárja** a `ReliefValue` numerikus tartományára vonatkozó kérdést: a `ReliefValue` doménje maradhat korlátlan/nem előre vizsgált, mert a fizikai leképezés adaptívan, a realizált szélsőértékekből normalizál, nem egy előre feltételezett skálafaktorból.

## 14.5 Fizikai paraméterek

```text
GeometricSurface
├── width, height             # fizikai XY kiterjedés
├── base_thickness            # a relief "nulla" síkja
├── relief_height_raised      # Raised irány terjedelme
├── relief_height_recessed    # Recessed irány terjedelme
└── raw_relief: (x,y) -> ReliefValue
```

Mind az öt skalár paraméter (`width`, `height`, `base_thickness`, `relief_height_raised`, `relief_height_recessed`) **Orchestration-szintű konfigurációból** érkezik, nem plugin-szintű konstans — konzisztensen a meglévő `ReliefGeometry` mintázatával.

`relief_height_recessed` **explicit, kötelező** paraméter — nem vezethető le automatikusan `base_thickness`-ből (ld. 14.6).

`relief_height_raised`-ra nincs analóg felső korlát ezen a rétegen — nyomtatási/gyártási magasságkorlát downstream réteg felelőssége, nem ez a réteg.

> **9.4 lezárva (2026-09-02):** a két paraméter végleges elnevezése `relief_height_raised`/`relief_height_recessed` — indoklást és a mérlegelt alternatívákat ld. **17.11**. A paraméterezés (kétparaméteres, aszimmetrikus forma) változatlan maradt.

## 14.6 Fail-fast validáció — a nulla-vastagságú régió strukturális kizárása

A rétegnek **egyetlen kötelező fizikai kényszere** van: a relief soha nem kerülhet fizikai `Z < 0` alá. Ezt **nem** futásidejű, a realizált értékektől függő ellenőrzésként, hanem konstrukciókor, tisztán a paraméterekből eldönthető, fail-fast szabályként kell kikényszeríteni:

```text
base_thickness − relief_height_recessed > 0     (szigorú)
```

Mivel a `V(p) = V_min` pontok — a `ReliefValue`-tól, tehát a kép tartalmától teljesen függetlenül — mindig pontosan a `base_thickness − relief_height_recessed` fizikai `Z`-értékre képződnek le (14.4), ez a paraméter-szintű ellenőrzés **strukturálisan, minden lehetséges kép-realizációra** kizárja a nulla vagy negatív vastagságú régiót — nem csak valószínűsíti.

Mellékhatásként a szabály implicit módon `base_thickness > 0`-t is kikényszerít (mivel `relief_height_recessed ≥ 0`), külön "mindkettő egyszerre nulla" ellenőrzés nélkül — analóg a meglévő `ReliefGeometry.__post_init__` degenerált-eset védelmével, de ennek a rétegnek a saját paraméter-készletéből következik.

## 14.7 Geometriai korlátok — hatókör

Nincs bizonyított igény minimum/maximum fizikai magasság-korlátra ezen túlmenően. Nyomtatási/gyártási felső korlát, anyagvastagság-minimum stb. downstream (pl. Slicing/Nesting) réteg felelőssége, nem a Geometric Surface-é.

## 14.8 Réteghatár a Raw Mesh felé

A `v_min`/`v_max` (14.4) előállítása **explicit a Geometry → Raw Mesh lépés (15. szakasz) felelőssége** — a mesh-építéshez amúgy is szükséges mintarácsból számítva, nem egy külön, önálló pásztázással (hatékonysági döntés). A Geometric Surface a `physical_z(raw_value, v_min, v_max)` képletet biztosítja, de a bemeneti `v_min`/`v_max` értékeket nem maga állítja elő.

Ebből következően a `v_min`/`v_max` **empirikus, minta-alapú közelítés**, nem garantált globális szélsőérték — a kontraktusnak ezt dokumentáltan jeleznie kell. A becslés pontossága a mesh-rács felbontásától (`sampling_distance`) függ.

A sampling, resolution, topology, watertightness továbbra is teljes egészében a 15. szakasz felelőssége — ezen a rétegen nem jelenhet meg.

## 14.9 Réteghatár befelé (mit nem kell tudnia a Geometric Surface-nek)

- az eredeti EffectSpec-eket és a Region-hierarchiát (8., 11. szakasz);
- a `combine` belső algoritmusát, csak a Relief Representation kimeneti kontraktusát (12.1–12.3, 13.1/13.2);
- a Mask konkrét reprezentációját (ld. 17.9, lezárva).

## 14.10 Kapcsolódás a jövőbeli generátorokhoz — elnevezési és dokumentációs megjegyzés

A `RELIEF_GENERATOR_DOMAIN.md` 21. és 23. szakasza szerint a projekt tudatosan **nem** hoz létre előzetes, spekulatív közös absztrakciót a jövőbeli generátorok (pl. egy későbbi Vector Relief Generator, vagy a hosszú távú, általános felületgeneráló motor) számára, amíg nincs bizonyított második konkrét igény — ezt ez a lépés is követi.

Ennek megfelelően a Geometric Surface elnevezése és dokumentációja explicit jelzi, hogy ez **Image Relief Generator-specifikus** kontraktus, nem a §23-as jövőbeli általános motor előfutára.

Ugyanakkor rögzítendő egy **felismert, dokumentációs célú** kapcsolódási pont, döntés nélkül: a `BACKLOG.md` 1. tétele (nem téglalap alaprajzú / áttört relief-testek) egy `(x,y) → van-e anyag` footprint/mask-függvényt ír le, ami már ma is jelen van az Image Relief Generator Semantic World-jében (`Region.Mask`, 4.1 szakasz) — és feltehetően egy jövőbeli, vektoralapú generátor is igényelné. Ez a kérdés tudatosan **nyitva marad**, nem ennek a lépésnek (sem az Image Relief Generator jelenlegi tervezésének) a tárgya.

---

# 15. Geometry → Raw Mesh

*(7. tervezési lépés eredménye, ld. 17.7)*

A következő lépés:

```text
Geometric Surface
        ↓
Mesh Construction
        ↓
Raw Mesh
```

Itt történik a Geometric Surface (14. szakasz) tényleges mesh-sé mintavételezése — ez az utolsó lépés a Geometry World-ön belül, mielőtt a Raw Mesh elhagyja az Image Relief Generatort.

## 15.1 Definíció és felelősség

A Raw Mesh réteg egyetlen publikus felelőssége egy tiszta, kontextusfüggetlen leképezés:

```text
(GeometricSurface, sampling_distance) -> GeneratedMesh
```

— közvetlen analógia a meglévő, implementált `MeshGenerator.generate(geometry, sampling_distance)` szignatúrájával (`MESH_GENERATION_MODEL.md` §36–37), csak `ReliefGeometry` helyett `GeometricSurface` bemenettel.

## 15.2 Rács és mintavételezés

A rács definíciója a meglévő `MeshGenerator` mintázatának közvetlen, változtatás nélküli átvétele:

```text
Nx = ceil(width / sampling_distance)
Ny = ceil(height / sampling_distance)
```

A kép natív pixel-felbontása **nem** jelenik meg domainfogalomként ezen a rétegen — a `raw_relief` a 13.2/14.2 szerint funkcionális, materializáció-mentes kontraktus, ugyanolyan opaque a Raw Mesh réteg számára, mint a Wave Generator `z=f(x,y)` matematikai függvénye volt a meglévő `MeshGenerator` számára (`RELIEF_GENERATOR_DOMAIN.md` §19).

## 15.3 `v_min`/`v_max` levezetése — egyetlen mintavételezési kör, két olcsó utófeldolgozási lépés

1. **Egyetlen mintavételezési kör**: `raw_relief(x,y)` kiértékelése a rács minden pontján, **pontosan egyszer** — az eredmény pontonként cache-elve.
2. **Bounds-redukció**: `v_min`/`v_max` tiszta min/max-redukcióval a cache-elt nyers értékekből — nincs második `raw_relief`-hívássorozat.
3. **Z-leképezés**: `physical_z` alkalmazása a cache-elt értékekre.

## 15.4 Topológia

A top+bottom+4 oldalfal, watertight, kifelé mutató normálú séma (`MESH_GENERATION_MODEL.md` §36) változtatás nélkül újrafelhasználható. Bottom-felület `Z = 0` sík marad, a 14.6 fail-fast szabályából strukturálisan következő konzisztenciával. A Raw Mesh réteg nem validálja újra a `base_thickness − relief_height_recessed > 0` feltételt.

## 15.5 Bounds-aliasing kockázat

Tudatosan vállalt közelítés, külön mitigációs mechanizmus nélkül — a kockázat egyetlen levere a meglévő `sampling_distance` paraméter. A bounds-pontatlanság hatása globális (skálázási torzítás), nem csak lokális. A degenerált, teljesen lapos eset aliasing mellett is helyesen viselkedik, nullával osztás nélkül.

## 15.6 Réteghatár az Orchestration felé (8. lépés)

A `(GeometricSurface, sampling_distance) -> GeneratedMesh` kontraktus pontosan kijelöli, mi nem tartozik ide: honnan származik maga a `GeometricSurface` példány, honnan a `sampling_distance`, a teljes pipeline komponens-sorrendje, a `MeshSource`-kontraktusba csomagolás, GUI-integráció, lifecycle, hibaterjesztés — mind a 8. lépés (16. szakasz) tárgya.

## 15.7 Réteghatár befelé

Öröklötten: az eredeti EffectSpec-eket, a Region-hierarchiát, a `combine` belső algoritmusát, a Mask konkrét reprezentációját. Saját nemtudás: a `physical_z` belső levezetését — a `GeometricSurface`-ből ténylegesen csak `width`, `height`, `raw_relief`, `physical_z` lép át a határon.

## 15.8 Reprezentációs kérdések — explicit nem eldöntve

A nyers-érték cache konkrét adatszerkezete, memóriaköltség-kezelés, a Raw Mesh építő pontos elnevezése/modul-elhelyezése — implementációs (Phase 4) vagy Dokumentáció módosítása lépés tárgyai.

---

# 16. Orchestration

*(8. tervezési lépés eredménye, ld. 17.8)*

Itt történik a Semantic World, a Relief World és a Geometry World komponenseinek tényleges összefűzése, valamint az eredmény becsomagolása a meglévő `MeshSource` kontraktusba (`MESH_SOURCE.md`, ADR-0014).

## 16.1 Definíció és felelősség

Az Orchestration egyetlen felelőssége, hogy előállítsa a Raw Mesh réteg (15. szakasz) bemenetét, majd az eredményt a `MeshSource` kontraktusba csomagolja.

## 16.2 Komponens-modell — MeshSource-adapter

Nincs külön, önálló "Orchestrator" domainfogalom. A felelősséget egy MeshSource-adapter osztály viseli, a meglévő `ReliefGeneratorMeshSource` precedens mintájára:

```text
ImageReliefGeneratorParameters (carrier dataclass)
        ↓
ImageReliefGeneratorMeshSource.get_mesh()
        │
        ├─ Image Interpretation   → Region-fa
        ├─ Region Resolver        → EffectSpec[]
        ├─ Effect Processing      → combine-zárvány (ReliefValue forrás)
        ├─ GeometricSurface összeállítása (raw_relief + öt fizikai paraméter)
        └─ Raw Mesh generálás     → GeneratedMesh → core Mesh (source_path=None)
```

## 16.3 Adatátadási határ — a `raw_relief` closure

```text
effect_specs = region_resolver.resolve(region_tree)          # Semantic World
def raw_relief(x, y):
    return effect_processing.combine(effect_specs, x, y)      # Relief World, elrejtve
surface = GeometricSurface(width, height, base_thickness,
                            relief_height_raised, relief_height_recessed,
                            raw_relief=raw_relief)             # Geometry World bemenete
```

> **Megjegyzés (2026-09-03, ADR-0020):** a fenti closure elavult — a bemutatott `raw_relief(x, y)` pass-through nem old fel egy időközben azonosított ellentmondást (a `Mask` abszolút kép-pixel-koordinátái vs. a Raw Mesh réteg deklarált pixel-agnosztikussága, 15.2/17.7). A helyes closure normalizált `(x,y) ∈ [0,1]²` bemenetet vár, és belsejében végzi el a kép-pixel-koordinátákra való leképezést — ld. `ADR-0020`. A tényleges, végleges closure-kód a Phase 13.8 (Orchestration) implementációjának tárgya; a fenti kód történeti, ez a jegyzet nem írja át, csak elavultnak jelöli.

> **Megjegyzés (2026-09-03, 13.8 lezárása):** a fenti nyitott kérdés
> lezárult — a végleges `raw_relief` closure és a normalizált→pixel
> leképezés (`px = x_norm · (image_width − 1)`, `py = y_norm ·
> (image_height − 1)`) a `docs/plugins/relief_generator/
> IMAGE_RELIEF_ORCHESTRATION.md`-ben (Phase 13.8) és az `ADR-0020`
> kiegészítésében található.

## 16.4 Paraméterátadás

Az öt fizikai paraméter és a `sampling_distance` egy `ImageReliefGeneratorParameters`-szerű carrier dataclass-on keresztül érkezik, a meglévő `ParameterSpec`/`MeshSourceDescriptor` mechanizmuson (ADR-0017) keresztül.

## 16.5 Lifecycle

A meglévő discovery-mechanizmus, a generikus form-builder és a háttérszálas generálás (Phase 8 precedens) közvetlenül újrafelhasználható.

## 16.6 Hibaterjesztés

A downstream rétegek saját kivételei nem kerülnek újracsomagolásra — változatlanul propagálnak a `get_mesh()`-ből.

> **Megjegyzés (nyitott, implementáció-közeli kérdés):** a 12.3-ban bevezetett explicit konfliktus-jelzés (nem-rokon, ellentétes irányú, prioritás nélküli ütközés) konkrét hibaterjesztési mechanizmusa itt dől majd el. *(2026-09-02: a korábbi "9.4 és későbbi" hivatkozás pontosítva — a 9.4 lezárva, ld. 17.11, de ezt a kérdést nem érintette; ez továbbra is önálló, nyitott tétel marad.)*

## 16.7 Paraméter-reprezentáció — kép-fájl bemenet

Új `"file"` `ParameterType` bevezetése a core GUI paraméter-sémában (ADR-0017 kiegészítés) — additív bővítés.

## 16.8 Réteghatár — mit NEM dönt el ez a lépés

Mask konkrét reprezentációja (ld. 17.9, lezárva), a `combine` belső algoritmusa (ld. 17.10, lezárva), footprint/mask kérdés, kép betöltés/fájlformátum, `sampling_distance` alapérték.

## 16.9 Plugin output

```text
Image Relief Generator
        ↓
Raw Mesh
        ↓
Slice Designer engines
```

---

# 17. Lezárt tervezési lépések

## 17.1 1. lépés — Mask + Spatial Representation (Lezárva; 2026-09-01: a spatial-vonatkozású tételek visszavonva, ld. 17.9 átírva)

### STABLE

- Az egyetlen bizonyítottan szükséges Mask-művelet: **membership query**.
- **A membership bináris.**
- Intersection/union/difference **nem** része a Mask kontraktusának.
- A Mask konkrét reprezentációja (raszter/vektor/implicit) Image Interpretation belső backend-döntés — ld. 17.9.

### VISSZAVONT (2026-09-01, ld. 17.9 átírva)

- ~~A Mask két állapotot hordoz a pipeline-ban: unresolved (Region, parent-relative) és resolved (EffectSpec, önállóan összevethető).~~ A Mask mindig abszolút, nincs ilyen állapot-megkülönböztetés.
- ~~A resolution / composition a Resolver felelőssége; frame-átvitel, nem clipping, nem geometriai Boolean metszet.~~ Nincs spatial resolution/composition lépés.
- ~~A Child Region csak a saját, parent-relative Mask-tartalmát hordozza; a Parent abszolút pozícióját nem.~~ A Child Mask már eleve abszolút.

### REJECTED

- **Intersection/union/difference mint elsőrangú Mask-művelet.** Indok: levezethető ismételt membership query-kből.
- **Külön, a Mask jelentését duplikáló spatial/frame fogalom bevezetése a Region-be.** *(2026-09-01: a korábbi, `Origin` mezőre vonatkozó "pontosítás, nem törlés" jegyzet visszavonva — ez a tétel ismét kiegészítés nélkül, teljes egészében érvényes.)*

---

## 17.2 2. lépés — Image Interpretation (Lezárva)

### STABLE

- **Definíció**: Az Image Interpretation felelőssége, hogy egy input képi forrásból előállítson egy, a Region-kontraktusnak (4. szakasz) megfelelő Region-fát (vagy -erdőt).
- **Bemenet**: domain-szinten nincs rögzítve konkrét reprezentáció.
- **Kimenet**: Region-fa vagy -erdő, csomópontonként a 4. szakasz kontraktusa szerint.
- **Region-hood kritérium**: egy terület akkor válik saját Regionná, ha hozzá megkülönböztethető (Contribution, DepthBehavior) pár tartozik.
- **Hierarchia (parent-child) kritérium — "coordinate coupling"**: Region B akkor és csak akkor gyermeke Region A-nak, ha (a) B térbeli kiterjedése természetes módon A-hoz van kötve, vagy (b) B DepthBehavior-ja vagy Contributionje A-tól függ. Térbeli átfedés vagy közelség önmagában nem indokolja a parent-child kapcsolatot.
- **Gyökér/erdő**: a Region-fa alakja nincs megkötve a pipeline szintjén.
- **Mélységi sorrend**: nincs önálló, a `Contribution`/`DepthBehavior`-tól elkülönült Region-mező arra, hogy egy Region a testvéreihez képest "elöl" vagy "hátul" áll.
- **Mask létrehozás**: régiónként független folyamat; nincs elvárás a testvér Regionök közti diszjunktságra vagy koordinációra.
- **Interpretation stratégia**: konkrét szegmentálási/interpretation stratégia nem kerül rögzítésre.

> **2026-09-01 (9.3-újra lezárása):** a "Mélységi sorrend" STABLE tétel felülvizsgálata lezárult — **módosítva**: nincs explicit, önálló "z-order" mező, de az `elevation` (a Contribution/DepthBehavior lineage menti felhalmozása, 7.4a) és az opcionális `TieBreakPriority` (12.3) együttesen igenis explicit adatot adnak a mélységi viszonyhoz — nem tisztán emergens hatás. Ld. 17.10.

> **2026-09-01 — kiegészítés (a 9.3-újra felülvizsgálat mellékterméke, ld. 17.9 átírva):** a "coordinate coupling" teszt kizárólag **fastruktúra-eldöntési kritérium** — azt dönti el, hogy B egyáltalán A gyereke legyen-e a `Children` hierarchiában. Nem vonható le belőle semmilyen következtetés a Mask *adatreprezentációjára* nézve (pl. hogy a Mask-nak a Parenthez képest relatívnak kellene lennie) — ennek összemosása volt az `Origin`/frame-mechanizmus (most visszavont) bevezetésének gyökér-oka.

### OPEN

- A Region-hood kritérium konkrét küszöbe/mértéke — stratégia-szintű kérdés.

### REJECTED

- **Szemantikai tartalmazás mint önálló hierarchia-kritérium.**
- **Strukturális szükségesség mint önálló Region-hood kritérium.**
- **Általános, minden Regionre kötelező explicit mélységi sorrend / z-order mező bevezetése a Region modellbe.**

> **2026-09-01 (9.3-újra lezárása):** ez a REJECTED tétel **megerősítve, pontosítva**: egy általános, minden Regionre kötelező z-order/rangsor mező továbbra is elutasított — de egy szűk, opcionális `TieBreakPriority` bevezetésre került, kizárólag a 12.3-ban leírt maradék, nem-rokon ellentétes irányú ütközésre. Ld. 8., 12.3, 17.10.

---

## 17.3 3. lépés — Region Resolution (Lezárva; 2026-09-01: spatial-vonatkozású tételek visszavonva, ld. 17.9 átírva; behaviorális dimenzió bővült, ld. 17.10)

### STABLE

- **Definíció és felelősség**: a Region Resolver a Region-fa relatív, hierarchiafüggő állapotát alakítja át EffectSpec[] konkrét, hierarchiafüggetlen állapotává — irány (`EffectiveDepthBehavior`, tranziens) és felhalmozott `elevation` feloldásával.
- **1:1 leképezés**: minden bejárt Region pontosan egy EffectSpecet termel.
- **Mask**: resolválás nélkül, változtatás nélkül kerül át `EffectSpec.Mask`-be.
- **`elevation`**: a `Contribution` és az `EffectiveDepthBehavior` szülőlánc menti, additív felhalmozásából származik (7.4a) — nem változtatás nélküli átvétel.
- **`ParentRef`**: a Region-fa bejárásából származó, opcionális strukturális mutató (7.1a).
- **ParentContext tartalma**: pontosan két mező (`effectiveDepthBehavior`, `elevation`).
- **ParentContext építése**: mindig a már feloldott szülő-értékekből.
- **Top-level Region**: `DepthBehavior = Inherit` top-level Regionön kontraktussértés; baseline `elevation = 0`.
- **Traverzálási szabály**: egyetlen kényszer — egy csomópont csak a szülője után resolválható.
- **DepthBehavior öröklés**: egylépéses szabály minden szinten (7.4).
- **Nincs szükség köztes, szervezési célú Region-fogalomra.**
- **Réteghatár**: a Resolver nem ismeri a Contribution/DepthBehavior fizikai jelentését, nem végez Effect Processing feladatot, nem ismeri a Geometry World fogalmait, nem viszi át az eredeti *szemantikai* identitást az EffectSpecbe (de a `ParentRef`-en keresztül igen egy szűk strukturális jelet, ld. lent).

> **2026-09-01 (9.3-újra lezárása):** a "nem viszi át az eredeti szemantikai identitást" réteghatár-tétel felülvizsgálata lezárult — **pontosítva, nem visszavonva**: a *szemantikai* identitás (név/típus) STABLE marad; egy szűk, nem-szemantikai `ParentRef` mutató (7.1a) igen átkerül. Ld. 17.10.

### VISSZAVONT (2026-09-01, ld. 17.9 átírva)

- ~~Frame-átvitel funkcionális kontraktusa és konkrét mechanikája.~~ Nincs frame-átvitel, nincs spatial resolution.
- ~~Top-level Region: Mask triviálisan resolved.~~ Tárgytalan — a Mask sosem "resolválódik", mindig abszolút.

### REJECTED

- **Többmenetes (multi-pass) vagy bottom-up resolválási lépés.**
- **Explicit „lánc-felfelé keresés" mechanizmus.**
- **Dedikált „OrganizationalRegion" típus vagy `IsOrganizational`-jellegű flag.**

### TÁRGYTALANNÁ VÁLT (2026-09-01)

- ~~A frame = a szülő resolved Maskja.~~ A `frame` fogalom megszűnt, ld. 17.9 átírva.

---

## 17.4 4. lépés — Effect Processing (Lezárva; 2026-09-01: a 9.3-újra végleges eredményével frissítve, ld. 17.10)

### STABLE

- **Definíció és felelősség**: a `combine` végleges algoritmusa — ld. 12.1–12.3, 17.10.
- **`S'` szűrő (lineage-occlusion) + `envelope` (azonos irányú, nem-rokon átfedés) + `tiebreak` (a maradék eset)** — a háromlépcsős kombinálási logika.
- **Determinisztikusság a bemeneti halmazra nézve** — a `combine` order-independent, de nem a régi, egyszerű "kommutativitás" fogalom szerint kommutatív.
- **Monotonitás azonos irányú átfedésre kötelező** — `envelope`-on keresztül triviálisan teljesül.
- **Relief Representation minimális tartalma**: „pont → ReliefValue” függvény-kontraktus.
- **Membership marad bináris.**
- **Falloff nem a Mask/membership fogalma.**
- **A bináris membership nem korlátozza a relief lehetséges formáját.**
- **Réteghatár**: az Effect Processing nem ismeri az eredeti szemantikai identitást, a teljes Region-hierarchiát/ParentContextet, a Geometry World fogalmait, és a Mask konkrét reprezentációját — de a `ParentRef`-en keresztül igen ismeri az ős-utód relációt.

### OPEN

*(nincs — a 9.3 teljes egészében lezárva. A `TieBreakPriority` konkrét GUI/UX-kezelése és a konfliktus-jelzés implementációs mechanizmusa nyitva marad, de ez implementációs, nem architekturális kérdés — ld. 16.6.)*

### REJECTED

- **Mask membership fokozatossá (fuzzy) tétele ezen a ponton.**
- **„Egyedi EffectSpec hatása” mint önálló alfolyamat/fogalom.**
- **Nettósítás (Σ) mint univerzális, minden azonos irányú átfedésre alkalmazott alapérték.** *(2026-09-01: véglegesen elvetve — lépcső-artefaktumot okoz lineage-menti, illetve nem-rokon ellentétes irányú átfedésnél; a lineage-esetben az additív `elevation`-felhalmozás formailag hasonló, de más szemantikájú, más rétegben (Resolver) történő művelet, ld. 17.10.)*
- **Dominancia (magnitúdó-alapú) mint univerzális kombinátor.** *(2026-09-01: véglegesen elvetve — bizonyítottan félrevezető, ld. 18.5, 17.10.)*
- **Általános, minden EffectSpec-re kötelező `Priority`/z-order mező.** *(2026-09-01: REJECTED megerősítve — a bevezetett `TieBreakPriority` ennél jóval szűkebb, opcionális, csak a maradék esetre vonatkozik, ld. 12.3, 17.10.)*
- **Sorrendfüggő (a feldolgozási sorrendtől ténylegesen függő) kombinálási stratégia bármilyen formája.**

---

## 17.5 5. lépés — Relief Representation (Lezárva)

### STABLE

- **Definíció és felelősség**: a Relief Representation egyetlen felelőssége hidat képezni az Effect Processing és a Geometry World között.
- **Absztrakciós forma**: funkcionális, "pont → ReliefValue" kontraktus.
- **Üres bemenet perem-feltétele**: `combine(∅) := 0`.
- **`ReliefValue` doménje**: előjeles skalár.
- **Falloff/smoothing pontosítás.**
- **Fizikai határ**: `ReliefValue ≠ physical height`.
- **Réteghatár**: nem ismeri az eredeti szemantikai identitást, a `combine` belső algoritmusát, a Geometry World fogalmait, és nem igényli a Mask konkrét reprezentációjának eldöntését.

### OPEN

*(nincs — a 9.3 lezárva, ld. 17.10)*

### REJECTED

- **Materializált (rács/raszter alapú) Relief Representation bevezetése ezen a lépésen.**
- **Strukturált (nem skalár) `ReliefValue` típus.**

---

## 17.6 6. lépés — Relief → Geometry (Lezárva)

### STABLE

- **Definíció és felelősség**: a Geometric Surface egyetlen felelőssége a Relief Representation fizikai geometriává alakítása.
- **Funkcionális absztrakció marad.**
- **Új, önálló, testvér-kontraktus** a meglévő `HeightField`/`ReliefGeometry` mellett.
- **Kétrészes kontraktus**: `raw_relief` + `physical_z`.
- **`v_min`/`v_max` előállítása a 7. lépés felelőssége.**
- **Nullponthoz rögzített, kétirányú skálázás.**
- **`ReliefValue` numerikus tartománya lezárva**: adaptív normalizálás.
- **Degenerált/teljesen lapos eset helyesen viselkedik.**
- **Fail-fast validáció konstrukciókor.**
- **`relief_height_recessed` explicit, kötelező paraméter.**
- **Nincs felső korlát `relief_height_raised`-ra.**
- **Fizikai paraméterek Orchestration-szintű konfigurációból érkeznek.**
- **Réteghatár a Raw Mesh felé és befelé.**
- **`relief_height_up`/`relief_height_down` végleges elnevezése: `relief_height_raised`/`relief_height_recessed`; paraméterezés (kétparaméteres, aszimmetrikus) megerősítve, változatlan.** (9.4, ld. 17.11)

### OPEN

- **Footprint/mask kérdés** (`BACKLOG.md` 1. tétele) — tudatosan nyitva.

### REJECTED

- **Meglévő `HeightField`/`ReliefGeometry` közvetlen, változtatás nélküli újrafelhasználása.**
- **Egyetlen globális min–max stretch.**
- **`relief_height_recessed` automatikus levezetése `base_thickness`-ből.**
- **Nyomtatási/gyártási magasságkorlát bevezetése ezen a rétegen.**
- **"Csak arra figyelni, hogy Z=0 alá ne menjünk" mint informális, futásidejű szabály.**
- **A Geometric Surface saját, önálló bounds-felfedező pásztázása.**
- **Előzetes, spekulatív közös absztrakció bevezetése** a jövőbeli generátorok számára.

---

## 17.7 7. lépés — Geometry → Raw Mesh (Lezárva)

### STABLE

- **Definíció és felelősség**: `(GeometricSurface, sampling_distance) -> GeneratedMesh`.
- **Rácsdefiníció**: `Nx = ceil(width/sampling_distance)`, `Ny = ceil(height/sampling_distance)`.
- **A kép natív pixel-felbontása nem jelenik meg domainfogalomként.**
- **`v_min`/`v_max` levezetése**: egyetlen mintavételezési kör + két olcsó utófeldolgozási lépés.
- **A nyers-érték cache** az egyetlen ténylegesen új absztrakciós elem.
- **Topológia**: változtatás nélkül újrafelhasználható.
- **Bottom-felület `Z = 0` sík marad.**
- **A Raw Mesh réteg nem validálja újra** a fail-fast feltételt.
- **Bounds-aliasing kockázat dokumentált, tudatosan vállalt közelítés.**
- **A bounds-pontatlanság hatása globális.**
- **Degenerált, teljesen lapos eset helyesen viselkedik.**
- **Réteghatár az Orchestration felé és befelé.**

### OPEN

- **A resolved Mask konkrét reprezentációja** — lezárva, ld. 17.9. *(történeti — a lezáráskor még OPEN volt)*
- **Bounds-pontosság `sampling_distance`-függősége.**
- **Footprint/mask kérdés** — tudatosan nyitva.

*(A `relief_height_up`/`relief_height_down` végleges elnevezése — lezárva, ld. 17.11. Az itt szereplő formula-hivatkozás `relief_height_recessed`-re frissítve.)*

### REJECTED

- **Kép natív pixel-felbontásának figyelembevétele vagy korlátként beépítése a Raw Mesh rétegbe.**
- **Külön, finomabb rácson végzett bounds-becslés.**
- **Biztonsági margó/epsilon bevezetése a `relief_height_raised`/`relief_height_recessed` skálázásában.**

---

## 17.8 8. lépés — Orchestration (Lezárva)

### STABLE

- **Nincs külön "Orchestrator" domainfogalom.**
- **Az adapter futtatja végig belsőleg a teljes láncot.**
- **Az adatátadási határ maga a `raw_relief` closure-építés ténye.**
- **Az öt fizikai paraméter + `sampling_distance`** a meglévő mechanizmuson keresztül érkezik.
- **Lifecycle és hibaterjesztés** a Phase 8 precedens újrafelhasználása.
- **`MeshSource`/`MeshSourceDescriptor` e lépés által nem módosul.**
- **Új `"file"` `ParameterType` bevezetése.**

### OPEN

- **A resolved Mask konkrét reprezentációja** — lezárva, ld. 17.9. *(történeti)*
- **A parent → child frame-átvitel konkrét mechanikája** — visszavonva, ld. 17.9 átírva. *(történeti)*
- **`sampling_distance` ajánlott alapértékének kép natív felbontásából való származtatása.** ← **következő aktív lépés (9.5)**
- **Falloff konkrét mechanizmusa** — csak ha konkrét igény igazolja.
- **Footprint/mask kérdés** — tudatosan nem kerül be a 9. lépésbe.
- **A kép betöltésének/fájlformátumának konkrét kérdése** — tudatosan nem architekturális kérdés.
- **Reprezentációs implementációs döntések.**
- **Dokumentációs kereszthivatkozási teendő** (`MESH_GENERATION_MODEL.md` §21 frissítése).
- **A 12.3 konfliktus-jelzés konkrét hibaterjesztési mechanizmusa** — ld. 16.6.

### REJECTED

- **Külön, önálló Orchestrator-objektum bevezetése az adapter-osztály mellett.**
- **`str` `ParameterType` + kézi útvonal-begépelés a kép-fájl paraméterhez.**

---

## 17.9 9. lépés (9.1+9.2 alszakasz) — Mask reprezentáció + Frame-átvitel — VISSZAVONVA, ÚJRATÁRGYALVA (2026-09-01)

> **2026-09-01 — visszavonás:** ez a szakasz eredetileg a 9.1 (Mask konkrét reprezentációja) és 9.2 (frame-átvitel mechanikája) alszakaszok lezárt eredményét rögzítette, beleértve az `Origin` mező és a `frame`/`reinterpret` mechanizmus bevezetését. A 9.3-újra (Depth/Occlusion szemantika) tervezési lépés során derült ki, hogy ennek indoklása körkörös volt: a "Mask unresolved/resolved állapot-megkülönböztetésének numerikusan is relevánsnak kell maradnia" premissza sosem lett önmagában bizonyítva. A projektgazda kérésére elvégzett, dedikált felülvizsgálat nem talált egyetlen bizonyított esetet sem, ahol a Masknak "unresolved, parent-relative" állapotra szüksége lenne — a Mask a Region-fa minden szintjén, a kép egyetlen, közös koordinátarendszerében, kezdettől fogva abszolút.

### Eredeti módszertan és döntés (történeti, visszavonva)

A kérdés eredetileg "raszter / vektor / implicit függvény" alternatívaként volt felvetve — ez materializációt feltételezett. A bizonyítottan szükséges igény (membership query kiértékelhetősége) nem indokolta a materializációt.

A `frame` tartalmának kérdésénél egy — utólag tévesnek bizonyult — architekturális ellentmondást láttunk: a `frame` funkcionális kontraktusa csomópontonkénti eltolás-adatot igényelt volna, mert a Mask unresolved/resolved állapot-megkülönböztetését numerikusan is relevánsnak tekintettük. A projektgazda a felkínált három megoldás közül (A: új, szűk hatókörű Region-mező / B: párhuzamos Image Interpretation kísérőstruktúra / C: `frame` mindenhol identitás) az A) változatot (az `Origin` mező) hagyta jóvá — ez volt az eredeti, most visszavont döntés.

### Felülvizsgálat (2026-09-01, 9.3-újra tervezési lépés)

A projektgazda konkrét kérésére elvégzett, tételes felülvizsgálat minden elképzelhető indokot megvizsgált, ami a relatív Mask-reprezentációt igényelhetné (Image Interpretation belső kényelme; a Child túllógásának kezelése; a "coordinate coupling" teszt, 17.2; jövőbeli template-alapú régió-definíció) — egyik sem bizonyult ténylegesen szükségesnek. A "coordinate coupling" teszt kifejezetten **fastruktúra-eldöntési kritérium** (dönti el, hogy B egyáltalán A gyereke legyen-e a `Children` hierarchiában), nem adatreprezentációs előírás — ennek összemosása volt a hiba gyökere. A korábbi C) opció ("frame mindenhol identitás") elutasítása ("elvetve, mert trivializálná a megkülönböztetést") éppen ezt a hibás premisszát feltételezte — ha a megkülönböztetés maga hibás volt, a "trivializálás" nem hiba, hanem helyes eredmény.

### ÚJ, ÉRVÉNYES DÖNTÉS — STABLE

- **A Mask mindig abszolút**: nincs unresolved/resolved állapot-megkülönböztetés. A Region-fa minden csomópontján a Mask a kép közös koordinátarendszerében, önállóan, közvetlenül összevethető formában létezik, a detektálás pillanatától kezdve.
- **Nincs Resolver-végzett spatial resolution/composition lépés.** A Resolver egyetlen megmaradt felelőssége a behaviorális dimenzió — ld. 17.10.
- **`EffectSpec.Mask := Region.Mask`**, változtatás nélküli átvétel.
- **Raszter/vektor/implicit függvény**: továbbra is Image Interpretation belső backend-döntés, nem architekturális kérdés — ez a tétel a visszavonás után is érvényes marad.
- **A Child térbeli túllógása a Parenten**: triviálisan adódik abból, hogy mindkét Mask önmagában, abszolút módon definiált — nem igényel külön garanciát vagy mechanizmust (ld. 5. szakasz, átírva).

### VISSZAVONT tételek

- **`Origin: (x, y)` Region-mező** — visszavonva. Nem szerepel többé a Region modellben (4. szakasz).
- **`frame(N) = frame(P) + N.Origin`; `reinterpret(p, frame) = p − frame`** — visszavonva, a teljes frame-átviteli mechanizmussal együtt (korábbi 7.3 szakasz törölve).
- **Transzformáció-család (tiszta eltolás)** — tárgytalanná vált, nincs mit transzformálni.
- **REJECTED tételek (elforgatás bevezetése a frame-be; `frame` = szülő resolved Maskja)** — tárgytalanná váltak, mivel maga a `frame`-fogalom megszűnt.
- **„`frame` mindenhol identitás, `Origin` mező nélkül — elvetve, mert trivializálná a megkülönböztetést”** — ez a korábbi REJECTED tétel **felülbírálva**: éppen ez (a `frame`/`Origin` teljes elhagyása) bizonyult a helyes megoldásnak, ld. fent.

---

## 17.10 9.3-újra — Depth/Occlusion szemantika (Lezárva, 2026-09-01)

*(A 18.5-ben felvetett architekturális kérdés dedikált tervezési lépésének eredménye.)*

### Módszertan

A kérdés a 9.3 (Overlap Resolution) tervezése közben merült fel: sem a nettósítás, sem a dominancia nem adta vissza a kívánt, occlusion-szerű vizuális hatást (18.5). A projektgazda hipotézise szerint a szülő-gyermek hierarchia hordozhatja a mélységi viszonyt — ezt a lépés tételesen megvizsgálta, beleértve egy közbeeső, önálló hibát is (a Mask/Origin/frame-mechanizmus megalapozatlansága, ld. 17.9), amely a vizsgálat közben derült ki és külön lezárásra került.

### A kulcsfelismerés — relatív, nem abszolút Contribution

A hierarchia-hipotézis első, hibás megfogalmazása abszolútnak tekintette a `Contribution`-t (pl. "House Raised 0.5 + gyermek Ornament Raised 0.3" — mintha a kettő független skálán lenne). A projektgazda pontosítása szerint a gyermek `Contribution`-je a **szülő már resolvált értékéhez képest relatív** — ugyanaz a mintázat, mint amit a (később visszavont) Origin/frame a térbeli dimenzióra alkalmazott, csak itt a behaviorális dimenzióra érvényes és megalapozott.

### Végleges döntés — STABLE

- **`elevation`**: a Region Resolver a `Contribution`+`EffectiveDepthBehavior` párost a szülőlánc mentén additívan felhalmozott, előjeles skalárrá (`elevation`) alakítja — ld. 7.4a.
  ```text
  elevation(node) := ParentContext.elevation + signed(node.Contribution, EffectiveDepthBehavior(node))
  ```
- **Lineage-menti occlusion — nem külön mechanizmus**: mivel az `elevation` additív, egy leszármazott értéke már tartalmazza az ősei hatását — az occlusion "ingyen" adódik abból, hogy egy ponton csak a legmélyebb, aktív leszármazottat (`S'(p)` szűrő) kell figyelembe venni, a sekélyebb ősöket ki kell zárni. Ld. 12.1.
- **Azonos irányú, nem-rokon (testvér/cross-branch) átfedés**: **envelope** (a nullától legtávolabbi elevation nyer) — **nem** összeadás. Az összeadás (nettósítás) itt mesterséges "lépcső"-artefaktumot hozna létre. Ld. 12.1.
- **Nem-rokon, ellentétes irányú átfedés**: strukturálisan nem oldható meg emergens jelből (sem hierarchia, sem magnitúdó, sem Mask-méret nem megbízható, ld. lent) — opcionális, szűk hatókörű `TieBreakPriority` mező (8., 12.3) old fel, alapértelmezésként **explicit konfliktus-jelzéssel**, hallgatólagos fallback nélkül.
- **`ParentRef`**: az EffectSpec egyetlen, strukturális (nem-szemantikai) mezője, ami az ős-utód reláció teszteléséhez szükséges — ld. 7.1a.
- **EffectSpec modell egyszerűsödik**: `Contribution`+`EffectiveDepthBehavior` helyett `elevation`+`ParentRef`+`TieBreakPriority` (utóbbi kettő opcionális) — ld. 8.

### Megcáfolt alternatívák (bizonyítással, nem csak érveléssel)

- **Globális, hierarchia-vak magnitúdó-dominancia** — megcáfolva a House/Window példán: a nagyobb `|elevation|` (House=0.5) "nyerne" a bemetszés (Window=0.2) felett, ami vizuálisan hibás.
- **Mask-terület mint occlusion-jel** — elvetve: megbízhatatlan, a kép véletlenszerű tulajdonsága, nem a szerzői szándék kifejeződése.
- **Nettósítás mint univerzális alapérték a maradék (nem-rokon, ellentétes irányú) esetre** — elvetve: mindenképp mesterséges "lépcsőt" hozna létre az érintett objektumban (a projektgazda eredeti gyanújának forrása, a "faág az ablak előtt" példával illusztrálva).

### A 18.5 táblázatának végleges feloldása

| Érintett tétel | Végállapot |
|---|---|
| 10–11. szakasz: „az EffectSpec-ek sorrendje nem hordoz szemantikát” | **Megerősítve.** A `ParentRef`/`TieBreakPriority` strukturális reláció, nem sorrend. |
| 17.2 REJECTED: explicit z-order mező elutasítva | **Megerősítve, pontosítva.** Az általános z-order továbbra is elutasított; a bevezetett `TieBreakPriority` ennél lényegesen szűkebb, opcionális, csak a maradék esetre vonatkozik. |
| 9. szakasz: `Priority`/`BlendMode`/`MergeRule`/`BooleanOperation` kizárva | **`Priority` finomítva.** `BlendMode`/`MergeRule`/`BooleanOperation` továbbra is kizárva. A `TieBreakPriority` nem azonos a kizárt, általános `Priority`-val. |
| 17.3 STABLE: eredeti szemantikai identitás nem kerül át | **Pontosítva, nem visszavonva.** A *szemantikai* identitás (név/típus) továbbra sem kerül át; egy szűk, nem-szemantikai `ParentRef` igen. |
| 17.4 STABLE/REJECTED: `combine` kötelezően kommutatív | **Módosítva.** A `combine` determinisztikus és order-independent marad a bemeneti *halmazra* nézve, de már nem egyszerű, kommutatív aggregáció — strukturált, több lépcsős algoritmus (12.1–12.3). |

### Nettósítás / dominancia végleges sorsa

- **Nettósítás**: **véglegesen elvetve** mint univerzális alapérték bármely, korábban mérlegelt szerepben — az azonos irányú, nem-rokon esetre az `envelope` helyettesíti, a lineage-esetre pedig maga az additív `elevation`-felhalmozás (ami formailag összeadás, de nem az Overlap Resolution szintjén, hanem a Resolverben, más szemantikával).
- **Dominancia**: **véglegesen elvetve** — bizonyítottan félrevezető minden vizsgált esetben.

### Definition of Done — teljesítve

(a) `combine` végleges szemantikája: ld. 12.1–12.3. (b) Minimális adat: `elevation`, `ParentRef`, opcionális `TieBreakPriority` (7.1a, 7.4a, 8.). (c) A 18.5 táblázat minden tétele feloldva (fent). (d) Nettósítás/dominancia sorsa: mindkettő véglegesen elvetve (fent).

---

## 17.11 9.4 — `relief_height_up`/`relief_height_down` végleges elnevezése/paraméterezése (Lezárva, 2026-09-02)

### Módszertan

Kis, alacsony kockázatú tétel — a szokásos négy lépés (követelmény → felelősség → absztrakció → reprezentáció) egy körben, stresszteszt-forduló nélkül, a 14., 16. és 4./13. szakaszok meglévő tartalmának keresztellenőrzésével.

### A kulcsfelismerés — a projekt már rendelkezik kanonikus kétirányú szókinccsel

A `relief_height_up`/`relief_height_down` munkanevek a `DepthBehavior` (4.3 STABLE: `Raised`/`Recessed`) és a `ReliefValue` előjel-konvenció (13.4 STABLE: pozitív → Raised, negatív → Recessed) által már lezárt fogalompár **1:1 fizikai realizációi** (14.4: `V(p) > 0` → `relief_height_up`, `V(p) < 0` → `relief_height_down`). Az „up”/„down” szókincs emiatt indokolatlan terminológiai törés volt a már STABLE Raised/Recessed fogalompárhoz képest — nem szándékos réteghatár-elválasztás, mert a 14.9 réteghatár a `combine` *algoritmusára* vonatkozik, nem a szókincsre.

### Végleges döntés — STABLE

- **Elnevezés**: `relief_height_up` → **`relief_height_raised`**, `relief_height_down` → **`relief_height_recessed`**. A `relief_height_` előtag megmarad (konzisztencia a többi négy fizikai paraméterrel, 14.5).
- **Paraméterezés**: **változatlan** — kétparaméteres, aszimmetrikus forma megerősítve. Nincs bizonyított igény egyetlen szimmetrikus `relief_height` paraméterre.

### Megcáfolt/elvetett alternatívák

- **`relief_height_up`/`relief_height_down` megtartása** — elvetve: indokolatlanul inkonzisztens a 4.3/13.4 fogalompárral.
- **`relief_height`/`relief_depth`** — elvetve: a `depth` szó ütközne a `DepthBehavior` fogalommal, amelyről 4.3 explicit kimondja, hogy *„nem fizikai mélységet vagy magasságot jelent”* — pontosan az a fogalmi keveredés, amit a dokumentum eddig tudatosan elkerült.
- **Egyetlen szimmetrikus `relief_height` paraméter** — elvetve, két bizonyított evidencia alapján: (1) 14.4 STABLE — a Raised/Recessed skálázás tudatosan **függetlenül** normalizált, nem közös stretch (az „Egyetlen globális min–max stretch” a 17.6 REJECTED listáján szerepel); (2) 14.6 fail-fast szabálya strukturálisan **aszimmetrikus** — csak a Recessed irányhoz kötődik kemény kényszer, a Raised irányhoz nincs analóg korlát (14.5). Bizonyított igény hiányában a 4. szakasz elve („nem vezetünk be mezőt elméleti lehetőség miatt”) alapján elvetve.

### Definition of Done — teljesítve

(a) Végleges elnevezés: `relief_height_raised`/`relief_height_recessed`, indoklással (fent). (b) Paraméterezés megerősítve, változatlan. (c) A 14.4/14.5/14.6, 15.4, 16.3, 17.6/17.7/17.8 érintett hivatkozásai frissítve. (d) Nem sérti a 17.10 (9.3-újra) eredményét — a `ReliefValue` doménje és a `combine` algoritmusa érintetlen, a réteghatár (14.9) nem sérült.

---

# 18. Jelenleg nyitott fő tervezési területek

### 18.1 Relief → Geometry — ✅ Lezárva

A 6. tervezési lépés eredménye — ld. 14. szakasz, 17.6.

### 18.2 Geometry → Raw Mesh — ✅ Lezárva

A 7. tervezési lépés eredménye — ld. 15. szakasz, 17.7.

### 18.3 Orchestration — ✅ Lezárva

A 8. tervezési lépés eredménye — ld. 16. szakasz, 17.8.

### 18.4 9. lépés — Nyitott kérdések feldolgozása

- **9.1 A resolved Mask konkrét reprezentációja** — ✅ **Lezárva** (2026-09-01, ld. 17.9 — átírva, az Origin/frame-mechanizmus visszavonva, a "Mask mindig abszolút" eredménnyel).
- **9.2 A parent → child frame-átvitel (composition) konkrét mechanikája** — ❌ **VISSZAVONVA** (2026-09-01) — nincs frame-átvitel, ld. 17.9 átírva.
- **9.3 Overlap Resolution konkrét politikája** — ✅ **Lezárva** (2026-09-01, ld. 17.10) — a "9.3-újra: Depth/Occlusion szemantika" dedikált tervezési lépés eredménye: `elevation` (additív, lineage menti felhalmozás) + `S'` szűrő (lineage-occlusion) + `envelope` (azonos irányú, nem-rokon átfedés) + opcionális `TieBreakPriority` (a maradék, nem-rokon ellentétes irányú ütközésre, explicit konfliktus-jelzéssel alapértelmezésként).
- **9.4 `relief_height_up`/`relief_height_down` végleges elnevezése/paraméterezése** — ✅ **Lezárva** (2026-09-02, ld. 17.11) — végleges nevek: `relief_height_raised`/`relief_height_recessed`; paraméterezés változatlan.
- **9.5 `sampling_distance` ajánlott alapértékének kép natív felbontásából való származtatása** — nyitva, csak ha bizonyítottá válik. **← következő aktív lépés.**
- **9.6 Falloff konkrét mechanizmusa** — továbbra is nyitva, csak ha igazolt igény.

### 18.5 Felfedezett architekturális kérdés — Depth/Occlusion szemantika (9.3 vizsgálatból, 2026-09-01) — ✅ LEZÁRVA (ld. 17.10)

> **Lezárás (2026-09-01):** a lent leírt kérdés a "9.3-újra: Depth/Occlusion szemantika" dedikált tervezési lépésben lezárult — a végleges eredményt, a táblázat tételes feloldását és a Definition of Done teljesülését ld. **17.10**. Ez a szakasz történeti indoklásként, változatlanul megmarad.

A 9.3 (Overlap Resolution) tervezése során két konkrét kombinátor-javaslat kapott alapos mérlegelést:

- **Nettósítás (signed sum)**: `combine(S) := Σ signed(c, d)`, `signed(c, Raised) = +c`, `signed(c, Recessed) = -c`. Minden kötelező invariánst (kommutativitás, monotonitás, `combine(∅)=0`) kielégít, nulla extra paraméterrel, és pontosan illeszkedik a már lezárt `ReliefValue` előjeles-skalár doménjéhez (13.4/17.5 STABLE).
- **Dominancia (magnitúdó-alapú)**: a nagyobb `|Contribution|`-jú irány felülír, önkényes tie-break szükséges egyenlő magnitúdóra.

**A projektgazda felismerése**: egyik módszer sem adja vissza azt a vizuális benyomást, mintha az átfedő objektumok közül valamelyik *közelebb* lenne a nézőhöz (occlusion-szerű hatás) — mindkettő az átfedésben egy harmadik, mesterséges relief-formát (lépcsőt/dudort) hoz létre, ahelyett hogy az egyik test egyszerűen eltakarná/felváltaná a másikat, miközben mindkettő változatlanul folytatódik az átfedésen kívül.

**A hiányzó bemenet oka**: sem a nettósítás, sem a dominancia bemenete (`Contribution`, `EffectiveDepthBehavior`) nem hordoz "melyik van elöl" információt — ez strukturálisan nem is származtatható belőlük, mert a `Contribution` hangsúlyosságot, a `DepthBehavior` irányt fejez ki, egyik sem mélységi sorrendet.

**A projektgazda hipotézise**: a szülő-gyermek hierarchia hordozhatná ezt a jelentést (egy gyermek Region strukturálisan "elöl van" a szülőjéhez képest) — ez a felvetés **explicit ellentmond** több, korábban lezárt döntésnek:

| Érintett tétel | Jelenlegi tartalom | Miért kérdőjeleződik meg |
|---|---|---|
| 10–11. szakasz | "Az EffectSpec-ek sorrendje önmagában nem hordoz szemantikát" | Ha a mélység a hierarchiából ered, a sorrend (implicit) mégis szemantikát hordozna |
| 17.2 REJECTED (2. lépés) | "Explicit mélységi sorrend/z-order mező... elutasítva, indok: emergens hatás" | Az indoklás valószínűleg téves volt: explicit adat nélkül nem áll elő a kívánt hatás |
| 9. szakasz | `Priority`/`BlendMode`/`MergeRule`/`BooleanOperation` kizárva az EffectSpecből | Egy occlusion-jellegű kombinátornak szüksége lenne valamilyen "ki van elöl" jelzésre |
| 17.3 STABLE (réteghatár) | "Az eredeti szemantikai identitás/hierarchia-infó... resolválás után eldobódik" | Ha a mélység a hierarchiából származna, ennek ellentmondana |
| 17.4 STABLE/REJECTED (4. lépés) | `combine` kötelezően kommutatív; sorrendfüggő stratégia kizárva | Egy occlusion-alapú `combine` definíció szerint **nem** kommutatív |

**A táblázat végleges feloldását ld. 17.10.**

**A 9.3-ban mérlegelt "nettósítás" és "dominancia" javaslatok végleges státusza**: mindkettő **véglegesen elvetve** mint a probléma bármilyen szerepű univerzális megoldása — ld. 17.10.

---

# 19. Tervezési sorrend

```text
0. Scope + Pipeline Contract        ✅ Lezárva
          ↓
1. Mask + Spatial Representation    ✅ Lezárva (ld. 17.1) — 2026-09-01: spatial-vonatkozású tételek visszavonva, ld. 17.9
          ↓
2. Image Interpretation             ✅ Lezárva (ld. 17.2)
          ↓
3. Region Resolution                ✅ Lezárva (ld. 17.3) — spatial-vonatkozású tételek visszavonva; behaviorális dimenzió bővült (elevation, ParentRef), ld. 17.10
          ↓
4. Effect Processing                ✅ Lezárva (ld. 17.4) — `combine` végleges algoritmusa, ld. 17.10
          ↓
5. Relief Representation            ✅ Lezárva (ld. 17.5)
          ↓
6. Relief → Geometry                ✅ Lezárva (ld. 17.6)
          ↓
7. Geometry → Raw Mesh              ✅ Lezárva (ld. 17.7)
          ↓
8. Orchestration                    ✅ Lezárva (ld. 17.8)
          ↓
9. Nyitott kérdések feldolgozása
     ├─ 9.1 Mask konkrét reprezentációja           ✅ Lezárva (ld. 17.9 átírva) — Origin/frame visszavonva
     ├─ 9.2 Frame-átvitel (composition) mechanikája ❌ VISSZAVONVA (2026-09-01) — nincs frame-átvitel
     ├─ 9.3 Overlap Resolution politikája           ✅ Lezárva (ld. 17.10) — Depth/Occlusion szemantika
     ├─ 9.4 relief_height_raised/recessed elnevezés  ✅ Lezárva (ld. 17.11)
     ├─ 9.5 sampling_distance alapérték kép-felbontásból  ⏳ Nyitva ← következő aktív lépés
     └─ 9.6 Falloff mechanizmusa (csak ha igazolt igény)   ⏳ Nyitva
```

A következő tényleges tervezési lépés:

> **9.5: `sampling_distance` ajánlott alapértékének kép natív felbontásából való származtatása** (csak akkor önálló tervezési lépés, ha a igény ténylegesen bizonyítottá válik — ld. 17.7 STABLE/OPEN és 16.8)

---

# 20. Tervezési munkamódszer

Az Image Relief Generator minden nagyobb tervezési lépését külön beszélgetésben dolgozzuk fel.

Egy-egy chat kizárólag az adott tervezési lépésre koncentrál — ettől a projektgazda kifejezett kérésére, esetenként, eltérhetünk (pl. 2026-09-01: a 9.1+9.2, a Mask/Origin-visszavonás és a teljes 9.3-újra egyetlen, hosszú chatben történt).

A beszélgetés végén:

1. összefoglaljuk az adott lépés eredményét;
2. elkülönítjük a stabil döntéseket, nyitott kérdéseket és elvetett megoldásokat;
3. frissítjük a központi tervezési állapotot;
4. elkészítjük a következő chat számára szükséges frissítő promptot.

A következő chat az aktuális `IMAGE_RELIEF_GENERATOR_PLANNING_updated.md` állapotból indul.

---

# 21. Tervezési állapotjelölések

A tervezés során három állapotot használunk:

### STABLE

Jelenleg elfogadott, érvényes tervezési döntés.

### OPEN

Még megválaszolatlan vagy további tervezést igénylő kérdés.

### REJECTED

Tudatosan elvetett fogalom vagy megoldás.

Egy korábban `REJECTED` elem nem kerül vissza a modellbe pusztán azért, mert egy későbbi beszélgetésben ismét felmerül, kivéve ha konkrét új követelmény vagy stresszteszt indokolja annak újravizsgálását.

> **Kiegészítés (2026-09-01):** egy negyedik, nem formális jelölés is használatban van: **⚠️ felülvizsgálat alatt** — egy STABLE vagy REJECTED tétel mellett jelzi, hogy egy másik, még nyitott tervezési kérdés eredményétől függően a tétel megváltozhat. Ez **nem** módosítja a tétel formális STABLE/REJECTED státuszát — kizárólag figyelmeztetés, amíg a függő kérdés le nem zárul. *(2026-09-01: a dokumentumban korábban szereplő, 18.5-re mutató ⚠️ jegyzetek a 9.3-újra lezárásával feloldásra kerültek — a lezárt tartalmat ld. 17.10.)*

> **Kiegészítés (2026-09-01):** egy ötödik, szintén nem formális jelölés: **visszavonás** — egy korábban STABLE-nek jelölt, ténylegesen lezárt döntés érvénytelenítése, amikor a projektgazda kérésére végzett felülvizsgálat az eredeti indoklást hibásnak találja. Ez különbözik a "⚠️ felülvizsgálat alatt" jelöléstől: az utóbbi egy *függő*, még el nem dőlt kérdésre mutat, míg a "visszavonás" egy *lezárt, végleges* eredmény — a régi tartalom nem törlődik nyomtalanul, hanem a visszavonás ténye és indoka a helyén dokumentálva marad (ld. pl. 17.9).

---

# 22. Fontos tervezési korlát

Ez az előzetes tervezés nem jelent implementációs engedélyt.

Ebben a munkafolyamatban:

```text
gondolkodás
    ↓
stresszteszt
    ↓
koncepció
    ↓
tervezet
```

a cél.

Nem cél:

```text
végleges specifikáció
    ↓
implementáció
    ↓
tesztelés
    ↓
review
```

A tényleges projektfázisban a megfelelő dokumentációs és architekturális jóváhagyási folyamatot külön kell végrehajtani.
