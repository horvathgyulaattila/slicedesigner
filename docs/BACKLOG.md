# Backlog

Státusz: Aktív
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-04
Utolsó módosítás: 2026-08-21
Kapcsolódó dokumentumok: [ROADMAP.md](ROADMAP.md)

## Cél

Ez a dokumentum azokat a jövőbeli tételeket (funkciókat, optimalizálásokat) sorolja fel, amelyek felmerültek a fejlesztés során, de nem tartoznak a jelenlegi fázis kilépési feltételei közé. Nem specifikáció és nem ROADMAP — kizárólag nyomon követhetőségi célt szolgál, formális elvárás (pl. SPECIFICATION_STANDARD) nélkül.

## Tételek

1. **Alternatív hullámforma-függvények a Wave Generatorban** (2026-08-19) — a Wave Generator jelenleg kizárólag szinusz alapú (`WaveFunction = Sinusoidal`, [WAVE_DOMAIN_MODEL.md](plugins/relief_generator/WAVE_DOMAIN_MODEL.md) 6.2 szakasz). A domainmodell 6.3 szakasza már előre jelzi további WaveFunctionök (Cosine, Triangle, Sawtooth, egyéb periodikus függvény) bevezetésének lehetőségét, a `WaveFunction` absztrakció újratervezése nélkül. Várhatóan alacsony komplexitású bővítés, mivel az absztrakció már készen áll.

2. **Új, Wave Generatortól független Height Field generátor-típusok** (2026-08-19) — procedurális felülettípusok (például faerezet-, Voronoi-, dűne-, holdkráter-szerű felszínek) mint önálló generátorok, nem a Wave Generator hullámforma-variánsaiként. Illeszkedik a `HeightField` már dokumentált, generátor-független szerződéséhez ([WAVE_FUNCTION_MODEL.md](plugins/relief_generator/WAVE_FUNCTION_MODEL.md) 18–20. szakasz), és a ROADMAP Phase 8 lezáró megjegyzésében is jelzett jövőbeli generátor-típusok (Heightmap, Image, Vector Generator) körébe tartozik.

3. **Amplitude distortion mint AmplitudeEnvelope-bővítés** (2026-08-19) — a hullám magasságát (nem a koordinátáit) moduláló, procedurális torzítás (`z' = z × D(x,y)`) fogalmilag az `AmplitudeEnvelope` (9.2) körébe tartozik, nem a koordináta-alapú `Distortion` (9.6) körébe. A [WAVE_DOMAIN_MODEL.md](plugins/relief_generator/WAVE_DOMAIN_MODEL.md) 16.3 szakasza már előre jelzi jövőbeli envelope-típusok (pl. Image, HeightMap) bevezetésének lehetőségét — egy procedurális/noise-alapú envelope logikusan ide tartozna.

4. **További Distortion-típusok a Wave Generatorban** (2026-08-19) — a 9.6 első köre kizárólag a `SwirlDistortion`-t vezeti be ([PROCEDURAL_DISTORTION.md](drafts/relief_generator_wave_extension/PROCEDURAL_DISTORTION.md) 3. szakasz). További, később hozzáadható típusok: sima, folytonos zajmező-alapú koordináta-warp (pl. Perlin/Simplex-szerű), valamint több lépték kombinálása (multi-scale distortion). Várhatóan alacsony komplexitású bővítés, mivel a `Distortion` absztrakció már készen áll.

5. **A generikus `ParameterSpec`-form vizuális csoportosítása** (2026-08-21) — a `_GeneratorParameterForm`/`_ListParameterWidget` (ADR-0017, ROADMAP Phase 9.7.a) jelenleg egy lapos, soronkénti listaként jeleníti meg az összes paramétert, típustól/relevanciától függetlenül (pl. a relief_generator `sources` listájának minden sorában a `direction` mező is látszik, még `source_type="Radial"` esetén is, amikor irreleváns). Élő teszteléskor (ROADMAP Phase 9.7.f) ez zavarónak bizonyult, különösen a relief_generator plugin Phase 9 paramétereinek (envelope/distortion/sources) számával. Lehetséges megoldás: a core `_CollapsibleSection` (már létező, a Dowel/Gap füleknél használt) mintájára szakaszolt/csoportosított, esetleg feltételesen látható mezőcsoportokat támogató bővítés a `ParameterSpec`/`_GeneratorParameterForm` mechanizmusban.

6. **Irregularity/complexity az explicit hullámforrásokhoz (koncentrikus rétegzés)** (2026-08-21) — jelenleg az explicit `WaveSourceSpec`-ekhez (9.4) nincs `irregularity`/`complexity` paraméter; a [MULTIPLE_WAVE_SOURCES.md](plugins/relief_generator/MULTIPLE_WAVE_SOURCES.md) 3. szakasza kifejezetten azzal indokolta ezt, hogy "nincs értelmes általánosításuk egyetlen, explicit `Radial` forrásra, amelynek nincs mit 'szórni' rajta." Élő használat során felmerült az igény, hogy egy explicit forrás is kaphasson többrétegű, csökkenő amplitúdójú/hullámhosszú komponens-szerkezetet, az automatikus generáláshoz hasonlóan (`PERSISTENCE`/`LACUNARITY` logika). Két lehetséges geometriai interpretáció merült fel: (a) **koncentrikus rétegzés** — ugyanabból a centerből induló, egymásba érő hullámgyűrűk; (b) pozíció-szórás — egymáshoz közeli, eltérő pozíciójú források. A projektgazda az (a) koncentrikus rétegzést preferálja. Megvalósítása nem egyszerű mezőbővítés: a `build_wave(spec) -> Wave` egyetlen hullámot állít elő jelenleg, ez `build_waves(spec) -> tuple[Wave, ...]`-re változna, ami végigfut a `multiple_wave_sources.py`-n, a `WaveGenerator`-on és a hozzájuk tartozó teszteken; a domain-contractot ([WAVE_DOMAIN_MODEL.md](plugins/relief_generator/WAVE_DOMAIN_MODEL.md)/[MULTIPLE_WAVE_SOURCES.md](plugins/relief_generator/MULTIPLE_WAVE_SOURCES.md)) is módosítani kell, mert a 3. szakasz jelenlegi állítása ez esetben tévessé válik. Célszerű a `BACKLOG.md` 5. tétele (mezőcsoportosítás) után/mellett megoldani, mivel két új mező (`irregularity`, `complexity`) soronként tovább zsúfolná a `sources` lista GUI-ját.

(2026-08-13: a korábbi három tétel lezárult — az 1. és 3. a ROADMAP.md Phase 7 hatókörébe került, a 2. véglegesen törölve, a projektgazda döntése alapján nem valósul meg.)
