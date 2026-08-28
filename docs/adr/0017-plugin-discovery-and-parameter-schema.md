# ADR-0017: Plugin discovery mechanizmus és GUI paraméter-séma

Dátum: 2026-08-16
Státusz: Elfogadva
Döntéshozó: Horváth Gyula Attila (projektgazda)

## Kontextus

Az ADR-0015 és az ADR-0016 egyaránt explicit módon későbbi döntésre halasztotta a MeshSource pluginok discovery-mechanizmusának konkrét technikai megvalósítását ("a discovery és a plugin-kompatibilitás konkrét technikai mechanizmusa jelen ADR hatókörén kívül esik, későbbi implementációs döntés tárgya" — ADR-0015; "a plugin discovery... konkrét technikai mechanizmusa jelen ADR hatókörén kívül esik" — ADR-0016).

A Relief Generator Plugin implementációja (`docs/plugins/relief_generator/IMPLEMENTATION_PLAN.md` §21) az 1-6. tételig elkészült; a 7. tétel ("Minimális GUI-integráció") tervezésekor kiderült, hogy egy valódi Qt-panel a SliceDesigner saját GUI-jában (`src/slicedesigner/gui/parameter_panel.py`) a jelenlegi állapotban csak úgy valósítható meg, ha a core közvetlenül importálja a `plugins.relief_generator`-t — ez sértené az ADR-0016 feltétel nélküli egyirányú függőségi szabályát (Plugin → Core).

A projektgazda kifejezett döntése: a GUI-integráció valódi, élő Qt-panel legyen, szabálysértés nélkül — ehhez a korábban elhalasztott discovery-mechanizmust kell most, ezzel az ADR-rel véglegesíteni, mielőtt a GUI-panel implementációja elkezdődhet.

## Döntés

Két, egymásra épülő, de egymástól elkülönülő mechanizmus kerül bevezetésre, kizárólag a `MeshSource` bővítési pontra szűkítve:

```text
Plugin
   ↓ (entry point regisztráció)
MeshSourceDescriptor  ← ÚJ, core-oldali, generikus contract
   ↓ (ParameterSpec lista)
Core GUI — generikus form-builder
   ↓ (felhasználói kitöltés)
MeshSourceDescriptor.build(values) → MeshSource
   ↓
Mesh
   ↓
meglévő SliceDesigner pipeline
```

**1. Discovery.** A core Python `importlib.metadata.entry_points()` segítségével, egy dedikált entry-point csoporton (`slicedesigner.mesh_sources`) keresztül ismeri fel a telepített MeshSource pluginokat. Minden entry point egy hívható objektumra mutat, amely meghívva egy `MeshSourceDescriptor`-t ad vissza. Nincs telepített plugin esetén a lista üres — ez nem hiba, a core enélkül is teljes értékű marad (ADR-0015 elve).

**2. Parameter Schema — `MeshSourceDescriptor`.** Egy új, core-oldali, domain-semleges adatstruktúra:

* `display_name: str` — a generátor neve a GUI-választóban;
* `parameters: tuple[ParameterSpec, ...]` — minden `ParameterSpec` név, típus (`float`/`int`/`str`/`enum`+választható értékek), alapérték, opcionális min/max, mértékegység és felirat;
* `build(values: dict[str, Any]) -> MeshSource` — factory, amely a kitöltött értékekből egy `MeshSource` példányt állít elő.

**Explicit rögzítendő, ellentmondás-elkerülés céljából:** a `MeshSourceDescriptor` **nem** módosítja és nem bővíti a `MeshSource` contractot (ADR-0014). A `MeshSource` interfész (`get_mesh() -> Mesh`) változatlan marad; ADR-0014 azon kikötése is érvényben marad, hogy "a core `MeshSource` contract [paraméterobjektumot] nem tartalmaz". A `MeshSourceDescriptor` egy különálló, kizárólag discovery-időben és GUI-építéskor használt regisztrációs csomagolás — a plugin mellett létezik, nem a `MeshSource`-on.

**3. Generikus form-builder.** A core GUI oldalán egy `ParameterSpec`-listából Qt widgeteket (spinbox/combobox/lineedit, típus szerint) építő komponens jön létre. A core sosem szembesül relief-specifikus fogalommal (Wave, Width, Base thickness stb.) — kizárólag generikus `ParameterSpec`-ekkel dolgozik.

A döntés további részletei:

* a mechanizmus **kizárólag** a MeshSource bővítési pontra vonatkozik — nem általánosított plugin-SDK export-, post-processing- vagy GUI-pluginokhoz; ez explicit hatókör-korlátozás, hogy a döntés ne kerüljön ellentmondásba az ADR-0014/ADR-0015 "Általános plugin-framework bevezetése... elutasítva" pontjával;
* a `MeshSourceDescriptor` és a `ParameterSpec` a SliceDesigner core-jába kerül (a pontos modul-elhelyezés az implementációs prompt feladata, l. Következmények);
* a plugin oldalán (`plugins/relief_generator/source/`) egy regisztrációs függvény szükséges, amely a meglévő `ReliefGeneratorMeshSource`/`ReliefGeneratorParameters`-t egy `MeshSourceDescriptor` mögé csomagolja;
* mindkét oldal (`pyproject.toml`, core és plugin) entry-point deklarációt igényel;
* a `MeshSource` contract formális verziózási/kompatibilitási kérdését (ADR-0014, "verziózott interfész") jelen ADR sem oldja meg részletesen — a jelenlegi, egyetlen plugint (relief_generator) tartalmazó hatókörben ez továbbra is nyitott, későbbi kérdés marad, explicit jelezve.

## Mérlegelt alternatívák

* **Statikus, kódba égetett import a core GUI-ban** (a korábban felvázolt "2. opció", tudatos, átmeneti ADR-0016 kivétellel) — elutasítva: a projektgazda kifejezetten azt kérte, hogy szabálysértés nélküli megoldás szülessen.
* **Konfigurációs fájl alapú discovery** (pl. egy kézzel szerkesztett `plugins.json` a core mellett) — elutasítva: felesleges kézi lépést vezetne be a felhasználó számára, miközben a Python csomagolási ökoszisztéma (`entry_points`) natívan, telepítéskor megoldja ugyanezt.
* **A paraméter-séma közvetlenül a `MeshSource` interfészen** (nem külön `MeshSourceDescriptor`-on) — elutasítva: ez ténylegesen módosítaná/bővítené az ADR-0014-ben elfogadott core contractot, amely kifejezetten kizárja a paraméterobjektumot onnan; a különálló Descriptor-mintázat elkerüli ezt az ellentmondást.
* **Teljes, több plugin-típusra általánosított plugin-SDK bevezetése már most** (export-, post-processing-, GUI-pluginok is) — elutasítva, az ADR-0014/ADR-0015 korábbi elutasítását megerősítve: nincs rá dokumentált igény; jelen ADR szigorúan a MeshSource bővítési pontra szűkíti a hatókört (Engineering Principles, egyszerűség elve).

## Következmények

* Az ADR-0015 "Következmények" szakaszának nyitott pontja ("Plugin discovery mechanizmust kell majd biztosítani... technikai megvalósításuk külön, későbbi döntés tárgya") ezzel lezárul, hivatkozással erre az ADR-re — az ADR-0015 külön prompttal frissül.
* Az `IMPLEMENTATION_PLAN.md` §21 7. tétele ("Minimális GUI-integráció") átértelmeződik: valódi, a core `ParameterPanel`-ban generikusan felépülő Qt-panelt jelent, nem szkriptet vagy STL-exportos kerülőutat; a discovery + `MeshSourceDescriptor` bevezetése önálló, a GUI-panel elé eső implementációs lépésként kerül be a tervbe — ezt az `IMPLEMENTATION_PLAN.md` külön prompttal veszi át.
* Új core-oldali kód szükséges (discovery loader + `MeshSourceDescriptor`/`ParameterSpec` típusok + generikus form-builder); a pontos modulhely (`src/slicedesigner/gui/` vagy egy új, dedikált modul) az implementációs promptban dől el.
* A plugin oldalán (`plugins/relief_generator/source/`) regisztrációs kód és `pyproject.toml`-bővítés szükséges mindkét oldalon.
* A `PROJECT_STRUCTURE.md` 11. szakasza kiegészül az entry-point konvenció rövid leírásával, erre az ADR-re hivatkozva.
* Az `ARCHITECTURE.md` a meglévő ADR-0014/ADR-0015/ADR-0016 hivatkozások mellé egy új bekezdést kap.
* A `ROADMAP.md` Phase 8 hatóköre bővül a discovery-mechanizmussal — ezt a projektgazda kifejezett kérése indokolja (Projekt végrehajtási szabály), nem AI-kezdeményezésű optimalizáció.
* Jelen ADR nem dönt a `ParameterSpec` pontos mezőlistájáról, a Qt widget-típus-leképezésről, a `MeshSourceDescriptor` pontos Python-modulhelyéről, sem a `pyproject.toml` entry-point csoport pontos szintaxisáról — ezeket a rá épülő implementációs promptok rendezik.

## Kiegészítés (2026-08-21): `list` típus

A ROADMAP Phase 9.7.a a `ParameterSpec`-et egy ötödik típussal, `"list"`-tel bővítette
— ezt a jelen ADR "Következmények" szakasza kifejezetten előre jelezte ("a
`ParameterSpec` pontos mezőlistájáról... a rá épülő implementációs promptok
rendezik"), ezért ez kiegészítés, nem új ADR.

Az igényt a Phase 9 (Wave Extension) 9.4 tétele (`WaveSourceSpec` explicit,
felhasználó által megadható hullámforrás-lista,
`docs/plugins/relief_generator/MULTIPLE_WAVE_SOURCES.md`) vetette fel: egy változó
hosszúságú, strukturált rekordokból álló lista, amire az eredeti négy skalár típus
nem elegendő.

A `list` típusú `ParameterSpec` egy új `item_schema: tuple[ParameterSpec, ...]` mezőt
kap, amely egyetlen listaelem mezőit írja le — kizárólag skalár (nem `list` típusú)
`ParameterSpec`-ekből. **Nincs beágyazott lista** — ugyanaz az elv, mint a
`WaveSet`/`WaveSourceSpec` domain rétegben (`WAVE_DOMAIN_MODEL.md` 17. szakasz, "nincs
nested `WaveSet` struktúra").

A core GUI generikus form-builderje (`src/slicedesigner/gui/parameter_panel.py`) egy új
`_ListParameterWidget` osztályt kapott: soronként egy, az `item_schema` alapján
generikusan épített mini-form (a meglévő `_GeneratorParameterForm` újrafelhasználásával,
rekurzívan), "Hozzáadás"/"Eltávolítás" gombokkal. A `values()` a sorok
`item_schema`-kulcsú dict-jeinek listáját adja vissza.

A meglévő négy típus (`float`/`int`/`str`/`enum`) és minden meglévő `_PARAMETERS`
tuple (jelenleg: relief_generator) változatlan — a `list` tisztán additív bővítés.

## Kiegészítés (2026-08-23): mezőcsoportosítás (`group`)

A ROADMAP Phase 10 10.1 tétele a `ParameterSpec`-et egy hatodik mezővel,
`group: str | None = None`-nal bővítette — ezt a jelen ADR "Következmények"
szakasza nem jelezte előre explicit módon, de a `list` típus kiegészítés
mintáját követi: additív dataclass-mező, nem érinti a `build()`-szemantikát,
ezért kiegészítés, nem új ADR.

Az igényt a `BACKLOG.md` (korábbi) 5. tétele vetette fel: a relief_generator
plugin 24 elemű `_PARAMETERS`-e (ROADMAP Phase 9.7.d) egyetlen, tagolatlan
formként jelent meg, típustól/relevanciától függetlenül.

Azonos `group`-ú `ParameterSpec`-ek a core GUI generikus form-builderjében
(`src/slicedesigner/gui/parameter_panel.py::_GeneratorParameterForm`) egy
közös, a meglévő `_CollapsibleSection` osztállyal épített, alapból csukott
szakaszba kerülnek, a csoport első előfordulásának helyén — nem szükséges,
hogy a `parameters` tuple-ben szomszédosak legyenek. `group=None` mezők
(minden meglévő `ParameterSpec`, a relief_generator alapgeometriai mezői és
a `sources` `item_schema`-ja is) csoportosítás nélkül, a fő formban jelennek
meg — ez a `list` típushoz hasonlóan tisztán additív bővítés, minden meglévő
`_PARAMETERS` tuple és a `_GeneratorParameterForm.values()` visszatérési
alakja változatlan marad.

**Explicit hatókörön kívül:** feltételes (dinamikus, egy másik mező
értékétől függő) mezőláthatóság — a csoportosítás statikus, a `parameters`
tuple összeállításakor rögzített, nem futásidőben, widget-eseményekre
változó.

## Kiegészítés (2026-08-24): feltételes mezőláthatóság (`visible_when`)

A ROADMAP Phase 11 11.0 tétele feloldja a jelen ADR korábbi, explicit
"hatókörön kívül" kikötését: a `ParameterSpec` egy hetedik mezővel,
`visible_when: tuple[str, str] | None = None`-nal bővült — additív
dataclass-mező, nem érinti a `build()`-szemantikát vagy a `values()`
visszatérési alakját, ezért ez kiegészítés, nem új ADR (a `group`
kiegészítés mintáját követve).

Az igényt a projektgazda vetette fel: a meglévő `envelope_type`/
`distortion_type` enum-mezőknél minden almező mindig látható volt a
GUI-n, típustól függetlenül — ez a `folytatás 41` bejegyzésben
dokumentált, elfogadott korlátként szerepelt, és a program jelenlegi
legzavaróbb tulajdonságává vált.

Egy mező csak akkor jelenik meg, ha a `visible_when`-ben megnevezett
vezérlő mező jelenlegi értéke megegyezik az elvárt értékkel, ÉS a
vezérlő mező maga is effektíven látható — ez a rekurzív kiértékelés
(`_GeneratorParameterForm._effective_visible()`) kétszintű vagy mélyebb
láncokat is helyesen kezel (pl. `envelope_sharpness` csak akkor látható,
ha `envelope_falloff == "Gaussian"` ÉS `envelope_type == "Radial"`),
külön, összetett feltétel-szintaxis bevezetése nélkül — minden mezőn
elég egyetlen, közvetlen szülőre mutató `visible_when`.

A core GUI generikus form-builderje
(`src/slicedesigner/gui/parameter_panel.py::_GeneratorParameterForm`) a
vezérlő enum-widgetek (`QComboBox`) értékváltozására (`currentIndexChanged`)
minden érintett sor (felirat + beviteli widget) láthatóságát újraszámolja.
A `_ListParameterWidget` soronkénti, beágyazott `_GeneratorParameterForm`-
jai a mechanizmust automatikusan, önállóan érvényesítik a saját
`item_schema`-jukon belül — nincs szükség a `_ListParameterWidget` saját
módosítására.

Visszamenőlegesen alkalmazva (`plugins/relief_generator/source/registration.py`):
az "Envelope" csoport `envelope_type`/`envelope_falloff`/
`envelope_noise_type` almezői, a "Torzítás" csoport `distortion_type`
almezői, és a `sources` `item_schema`-ban a `source_type` almezői
(`direction` vs. `source_x`/`source_y`) — a pontos hozzárendelést l. a
végrehajtó prompt `_PARAMETERS` tuple-jében.

A meglévő négy mező (`group`-ig) és minden meglévő `_PARAMETERS` tuple
`visible_when` nélkül (`None` alapértelmezéssel) változatlan viselkedésű
marad — teljes backward compatibility.
