# WAVE_WEIGHTING.md

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-19
Utolsó módosítás: 2026-08-19
Kapcsolódó dokumentumok: [WAVE_DOMAIN_MODEL.md](WAVE_DOMAIN_MODEL.md)

## 1. Cél

A jelen dokumentum (ROADMAP Phase 9.5 — Wave combination / weighting) a [WAVE_DOMAIN_MODEL.md](WAVE_DOMAIN_MODEL.md) (9.1) 5.4 és 9. szakaszában bevezetett `weight` paraméter és `WaveSet` összegzés szemantikáját fejti ki részletesen.

## 2. Weight szemantika

A `weight` azt határozza meg, hogy az adott hullámkomponens milyen mértékben járul hozzá a `WaveSet` eredményéhez. Alapértelmezett érték: `w_i = 1`.

A `weight` és az `amplitude` külön fogalmak:

* `amplitude` → a hullám saját amplitúdója;
* `weight` → a komponens hozzájárulása a kompozícióhoz.

A weight bármely véges valós érték lehet.

## 3. Weight = 0

`weight = 0` érvényes konfiguráció — a komponens ekkor nem járul hozzá a `WaveSet` eredményéhez, de a `Wave` maga továbbra is érvényes, létező komponens marad a gyűjteményben (pl. ideiglenes kikapcsolásra alkalmas, a komponens eltávolítása nélkül).

## 4. Negatív weight

Negatív weight szintén megengedett. A negatív weight a komponens előjelét fordítja meg, ami matematikailag egy fáziseltolással ekvivalens lehet.

## 5. WaveSet összegzés

A `WaveSet` nyers eredménye a súlyozott komponensek összege:

```text
F(x,y) = Σ f_i(x,y) = Σ w_i · A_i · M_i(x,y) · W_i(P_i(x,y), λ_i, φ_i)
```

A weight a normalizálás ([WAVE_DOMAIN_MODEL.md](WAVE_DOMAIN_MODEL.md) 12. szakasz) *előtt* érvényesül — a normalizálás a súlyozott összegre vonatkozik, nem az egyedi komponensekre.
