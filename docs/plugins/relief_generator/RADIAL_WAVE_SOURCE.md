# RADIAL_WAVE_SOURCE.md

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-19
Utolsó módosítás: 2026-08-19
Kapcsolódó dokumentumok: [WAVE_DOMAIN_MODEL.md](WAVE_DOMAIN_MODEL.md)

## 1. Cél

A jelen dokumentum (ROADMAP Phase 9.3 — Radial wave source) a [WAVE_DOMAIN_MODEL.md](WAVE_DOMAIN_MODEL.md) (9.1) 7. szakaszában rögzített `PropagationModel` absztrakciót konkretizálja egy pontszerű forrásból kiinduló hullámmodellel (`Radial`).

## 2. RadialPropagation

A `Radial` propagation egy pontszerű forrásból kiinduló hullámot reprezentál.

Paraméterei: source X; source Y.

A térbeli fázispozíció:

```text
P(x,y) = √( (x − x_s)² + (y − y_s)² )
```

ahol `x_s`, `y_s` a source pozíciója.

A source pozíciója független az AmplitudeEnvelope centerétől ([AMPLITUDE_ENVELOPE.md](AMPLITUDE_ENVELOPE.md)). A két pozíció alapértelmezés szerint lehet azonos, de a domainmodell nem köti őket össze. A source a vizsgált felületen kívül is elhelyezhető.

## 3. RadialPropagation határesetek

Ha `x = x_s` és `y = y_s`, akkor `P(x,y) = 0`. Ez érvényes állapot — a modellben nincs olyan nevező vagy más művelet, amely ebben a pontban szingularitást okozna.
