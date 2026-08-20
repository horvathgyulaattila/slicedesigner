# MULTIPLE_WAVE_SOURCES.md

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-19
Utolsó módosítás: 2026-08-19
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

* `WaveFunction` = Sinusoidal (rögzített, a 9.1 hatókörének megfelelően — ld. `WAVE_DOMAIN_MODEL.md` 6.3 szakasz, illetve a `BACKLOG.md` 1. tétele a jövőbeli alternatívákról);
* `AmplitudeEnvelope` = Uniform (rögzített — a forrásonkénti envelope-testreszabás jelenleg nem része a 9.4 hatókörének, ld. 7. szakasz).

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

* forrásonkénti `AmplitudeEnvelope`-testreszabás (minden explicit forrás Uniform envelope-ot kap);
* forrásonkénti `Distortion` (9.6)-testreszabás;
* az automatikus generálás kikapcsolása vagy "kizárólag explicit" mód bevezetése;
* GUI-implementáció — a `WaveSourceSpec` lista felhasználói szerkesztése a meglévő, deklaratív paraméter-séma mechanizmuson (`MeshSourceDescriptor`/`ParameterSpec`, ADR-0017) keresztül valósul majd meg, ami nem igényel a 9.4 hatókörében saját tervezést.

## 8. Phase 8 / 9.1 backward compatibility

Ha az explicit forráslista üres (ez az alapértelmezett állapot), a viselkedés pontosan megegyezik a Phase 8 / 9.1 viselkedésével — kizárólag az automatikus, `WaveParameters`-alapú generálás fut. Ez a 9.4 validációjának kötelező része.
