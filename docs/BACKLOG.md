# Backlog

Státusz: Aktív
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-04
Utolsó módosítás: 2026-09-02
Kapcsolódó dokumentumok: [ROADMAP.md](ROADMAP.md)

## Cél

Ez a dokumentum azokat a jövőbeli tételeket (funkciókat, optimalizálásokat) sorolja fel, amelyek felmerültek a fejlesztés során, de nem tartoznak a jelenlegi fázis kilépési feltételei közé. Nem specifikáció és nem ROADMAP — kizárólag nyomon követhetőségi célt szolgál, formális elvárás (pl. SPECIFICATION_STANDARD) nélkül.

## Tételek

1. **Nem téglalap alaprajzú / áttört (lyukacsos) relief-testek** (2026-08-25) — a jelenlegi geometria-modell (`ReliefGeometry`) mindig egy folytonos, téglalap alaprajzú, `base_thickness` vastagságú alaplemezre épít, amire a `HeightField` egy `relief_height`-tel skálázott buckót helyez — a `HeightField.query(x,y) -> float` szerződése kizárólag magasságot fejez ki, azt nem, hogy van-e egyáltalán anyag egy adott `(x,y)` ponton. Két, egymással rokon jövőbeli igény merült fel (a projektgazdától, a Voronoi-mesh élő tesztelése közben): (a) nem téglalap alakú alaptest (pl. kör, ellipszis, vagy egy hullám kontúrját követő szabálytalan alaprajz); (b) áttört/lyukacsos relief, ahol egyes belső régiókban sincs anyag (sem relief, sem alaplemez). Mindkettő architekturálisan ugyanarra az alapmechanizmusra vezethető vissza — egy, a `HeightField`-től független, `(x,y) → van-e anyag` footprint/maszk-függvényre —, de ez egy jóval nagyobb, önálló geometria-modell-döntés lenne, nem a jelenlegi Phase 11 Height Field receptjeinek (11.1–11.4) hatóköre. Explicit módon nem aktuális, nincs sürgetve — pusztán jelzett jövőbeli irány. **Kereszthivatkozás (2026-09-02):** a `docs/ROADMAP.md` Phase 13 (Image Relief Generator) `Region.Mask` fogalma fogalmilag rokon ezzel a tétellel, de nem oldja meg — a Mask az Image Relief Generator saját, belső, image-specifikus fogalma marad; ez a tétel önálló, jövőbeli döntés marad.
2. **Wave Generator anizotróp/aszimmetrikus profil-kiegészítés** (2026-08-28) — a Phase 11.3 (Dűne-felszín) tervezése és négy egymást követő élő-tesztelési köre közben felmerült, hogy egy irányított, szélirány mentén lankás/hosszú, arra merőlegesen éles/keskeny, ÉS aszimmetrikus (lankás elöl, meredek hátul) periodikus gerinc-profil hasznos, önálló kiegészítés lenne a Wave Generatorhoz — feltehetően egy új `WaveFunction`-ként vagy ahhoz hasonló mechanizmusként. Ez kifejezetten NEM a Dune Generator domb-alapjaként valósítandó meg: az ott próbaként beépített, ugyanerre az elvre épülő periodikus profil élő tesztelésen elutasításra került, mivel elnyomta a projektgazda által kifejezetten dicsért, szerves, izotróp domborzatjelleget (l. `docs/plugins/relief_generator/DUNE_RELIEF_GENERATOR.md` 2–3. szakasza). Explicit módon nem aktuális, nincs sürgetve — pusztán jelzett jövőbeli irány.

(2026-08-13: a korábbi három tétel lezárult — az 1. és 3. a ROADMAP.md Phase 7 hatókörébe került, a 2. véglegesen törölve, a projektgazda döntése alapján nem valósul meg.)

(2026-08-23: az 1., 3., 4., 5. és 6. tétel a ROADMAP.md Phase 10 (Hullámforma-variánsok és eljárásos zajmoduláció) hatókörébe került és törlésre került a Backlogból; a fent megmaradt egyetlen tétel emiatt 1. sorszámra került át.)

(2026-08-24: a megmaradt 1. tétel a ROADMAP.md Phase 11 (Procedurális Height Field receptek) hatókörébe került és törlésre került a Backlogból.)
