# MULTIPLE_WAVE_SOURCES.md

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-19
Utolsó módosítás: 2026-08-21
Kapcsolódó dokumentumok: [WAVE_DOMAIN_MODEL.md](WAVE_DOMAIN_MODEL.md), [RADIAL_WAVE_SOURCE.md](RADIAL_WAVE_SOURCE.md)

## 1. Cél

A jelen dokumentum (ROADMAP Phase 9.4 — Multiple wave sources) azt határozza meg, hogyan válik a [WAVE_DOMAIN_MODEL.md](WAVE_DOMAIN_MODEL.md) (9.1) `WaveSet`/`Wave` modellje — amely strukturálisan már eddig is lehetővé tette több, egymástól független forrású `Wave` komponens kombinálását — felhasználói szinten ténylegesen konfigurálhatóvá.

## 2. Kontextus

A [WAVE_FUNCTION_MODEL.md](WAVE_FUNCTION_MODEL.md) (Phase 8) 16. szakasza már előre jelezte több hullámforrás kombinálásának lehetőségét. A domain modell (`Wave`, `WaveSet`) ezt már 9.1 óta strukturálisan támogatja. A hiányzó láncszem a magasabb szintű, felhasználó által megadható generátor-konfiguráció volt — enélkül semmi nem határozná meg egy radiális hullám forráspozícióját a gyakorlatban.

## 3. Kettős mechanizmus: automatikus generálás és explicit forráslista

A meglévő, `WaveParameters`-alapú automatikus generálás (`direction`, `direction_spread`, `irregularity`, `complexity`) egy **hullámcsalád-generátor**: egyetlen domináns irányból determinisztikusan szórt `Directional` komponenseket állít elő. Az `irregularity` és a `complexity` fogalmilag ehhez a családhoz tartozik — nincs értelmes általánosításuk egyetlen, explicit `Radial` forrásra, amelynek nincs mit "szórni" rajta.

A 9.4 ezért **nem váltja fel** az automatikus generálást, hanem egy azzal párhuzamos, kiegészítő mechanizmust vezet be:

* **Automatikus generálás** (változatlan, Phase 8 óta): `WaveParameters` → N darab jitterelt `Directional` `Wave`.
* **Explicit forráslista** (új, 9.4): felhasználó által egyenként megadott, teljesen paraméterezett `Wave` komponensek listája — elsősorban `Radial`, de elvileg `Directional` forrás is lehet.

A kettő ugyanabba a `WaveSet`-be táplál (lásd 5. szakasz).

## 4. WaveSourceSpec

Egy explicit forrás specifikációja (`WaveSourceSpec`) a következő mezőkből áll:

* **source_type**: `Directional` vagy `Radial`;
* típus-specifikus pozíció: `Directional` esetén `direction`; `Radial` esetén `source_x` és `source_y`;
* **amplitude**, **wavelength**, **phase**;
* **weight** (opcionális, alapértelmezett érték `1`).

A `WaveSourceSpec` a [WAVE_DOMAIN_MODEL.md](WAVE_DOMAIN_MODEL.md) invariánsai szerint validálódik (pl. `amplitude > 0`, `wavelength > 0` — 5.1–5.2 szakasz), a típusnak megfelelő `PropagationModel` saját szabályai szerint (`DirectionalPropagation` — 7.2 szakasz; `RadialPropagation` — [RADIAL_WAVE_SOURCE.md](RADIAL_WAVE_SOURCE.md) 2–3. szakasz).

Minden `WaveSourceSpec`-ből előálló `Wave`:

* `WaveFunction` = a `WaveSourceSpec.function` mező szerint (Sinusoidal/Triangle/Sawtooth/Square, `WAVE_DOMAIN_MODEL.md` 6.2–6.3 szakasz), forrásonként egyedileg választható — ROADMAP Phase 10.2 kiegészítés (korábban rögzítetten Sinusoidal volt);
* `AmplitudeEnvelope`/`Distortion` = a `WaveParameters.envelope`/`distortion` — ugyanaz a megosztott, opcionális komponens, amit az automatikusan generált komponensek is kapnak (2026-08-21-i kiegészítés, ld. 9. szakasz). Forrásonkénti, egymástól eltérő envelope-/distortion-testreszabás továbbra sem lehetséges — ez marad hatókörön kívül (ld. 7. szakasz).

## 5. WaveSet felépítése

A végső `WaveSet` az automatikus generálás és az explicit forráslista determinisztikus összefűzéséből áll, ebben a sorrendben:

```text
WaveParameters
      ↓
automatikus, jitterelt Directional Wave-lista (N darab)
      │
      │         WaveSourceSpec lista (0..N elem, alapértelmezetten üres)
      │                 ↓
      │         egy Wave / spec
      │
      ▼                 ▼
      └──────── összefűzés ────────┘
                    ↓
                 WaveSet
```

Az összefűzés sorrendje: az automatikusan generált komponensek előbb, az explicit forráslista elemei a megadott sorrendjükben utánuk — ez biztosítja a `WaveSet` determinisztikus komponens-sorrendjére vonatkozó követelményt (`WAVE_DOMAIN_MODEL.md` 9.1 szakasz).

## 6. Validáció és határesetek

Nincs a több forrásra vonatkozó, önálló validációs szabály. Minden `WaveSourceSpec` kizárólag a saját típusának már meglévő szabályai szerint validálódik; a `WaveSet` szintjén nincs többlet-megkötés.

Ebből következik, hogy két, egymással azonos centerű `Radial` forrás **érvényes konfiguráció** — a domainmodell következetesen elutasítja a mesterséges korlátozásokat ott, ahol a matematika nem indokolja őket (`WAVE_DOMAIN_MODEL.md` több helyen, pl. 5.2, 9. szakasz). Az azonos centerű források egyszerűen összeadódnak a `WaveSet` összegzésében, akár szándékos, akár véletlen a konfiguráció.

## 7. Hatókörön kívül

Nem része a 9.4-nek:

* forrásonkénti, egymástól eltérő `AmplitudeEnvelope`-testreszabás (minden komponens — automatikus és explicit egyaránt — ugyanazt a megosztott envelope-ot kapja, ld. 4. és 9. szakasz);
* forrásonkénti, egymástól eltérő `Distortion`-testreszabás (ugyanaz az elv, ld. 4. és 9. szakasz);
* GUI-implementáció — a `WaveSourceSpec` lista felhasználói szerkesztése a meglévő, deklaratív paraméter-séma mechanizmuson (`MeshSourceDescriptor`/`ParameterSpec`, ADR-0017) keresztül valósul majd meg, ami nem igényel a 9.4 hatókörében saját tervezést.

Az automatikus generálás kikapcsolhatósága ("kizárólag explicit" mód) a 9. szakaszban rögzített, 2026-08-21-i kiegészítés tárgya — ez már RÉSZE a domain-contractnak.

## 8. Phase 8 / 9.1 backward compatibility

Ha az explicit forráslista üres (ez az alapértelmezett állapot), a viselkedés pontosan megegyezik a Phase 8 / 9.1 viselkedésével — kizárólag az automatikus, `WaveParameters`-alapú generálás fut. Ez a 9.4 validációjának kötelező része.

## 9. Kiegészítés (2026-08-21): megosztott envelope/distortion és `include_automatic`

Élő teszteléskor (ROADMAP Phase 9.7.f) kiderült, hogy a 4. és 7. szakaszban eredetileg rögzített két korlátozás — (a) az explicit forrásokból épülő `Wave`-ek mindig `Uniform` envelope-ot és semmilyen `Distortion`-t nem kapnak, (b) az automatikus generálás nem kapcsolható ki — együttesen olyan konfigurációt eredményeztek, ahol a felhasználó nem tudott kizárólag az explicit forrásokból álló reliefet létrehozni, és nem tudta ezekre alkalmazni a globálisan beállított envelope-ot/torzítást sem. A projektgazda ezt a két korlátozást felülbírálta:

**Megosztott envelope/distortion.** A `WaveParameters.envelope`/`distortion` (9.7.b/c) mostantól **minden** `Wave`-re — az automatikusan generáltakra ÉS az explicit `WaveSourceSpec`-ekből épülőkre egyaránt — alkalmazódik, ugyanazzal a megosztott példánnyal. Ez a 4. szakasz korábbi "AmplitudeEnvelope = Uniform (rögzített)" kikötését hatálytalanítja. Forrásonkénti (egymástól eltérő) envelope-/distortion-testreszabás továbbra sem lehetséges — ez a korlátozás változatlan (ld. 7. szakasz).

**`include_automatic`.** A `WaveParameters` egy új, opcionális `include_automatic: bool = True` mezőt kap. Ha `False`, a `WaveGenerator` **nem** épít automatikus komponenseket — a végső `WaveSet` kizárólag az explicit forráslistából áll. Ha `include_automatic=False` ÉS `sources` üres, a `WaveSet.__post_init__` már meglévő fail-fast hibáját (`WaveSetValueError`) dobja — ez szándékos, nem igényel külön kezelést.

**Backward compatibility.** `include_automatic` alapértéke `True` — minden meglévő, ezt a mezőt nem megadó konstrukció (a teljes 9.1–9.7 tesztkészlet) változatlan viselkedést kap.
