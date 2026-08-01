# ADR-0001: Implementációs technológia — Python + PySide

Dátum: 2026-08-01
Státusz: Elfogadva
Döntéshozó: Horváth Gyula Attila (projektgazda)

## Kontextus

Az ARCHITECTURE.md rögzítette a rendszer réteges felépítését (Domain / Koordinációs / Prezentációs), szándékosan technológiafüggetlenül. A PROJECT_STRUCTURE.md kidolgozásához, és minden további fejlesztéshez szükség van a konkrét implementációs nyelv és technológia rögzítésére.

## Döntés

A Slice Designer implementációja Python nyelven történik. A Prezentációs réteg (GUI) PySide (Qt for Python) segítségével valósul meg.

## Mérlegelt alternatívák

* **C# / .NET** (WPF vagy Avalonia) — natív desktop teljesítmény, de a projektgazda számára kevésbé ismerős environment.
* **Rust** — kiváló teljesítmény és determinizmus, de jelentősen nagyobb fejlesztési overhead egy egyszemélyes, saját használatra készülő eszköznél (PROJECT_VISION.md célfelhasználók szakasza).
* **Python + PySide** — *választott*: gyors fejlesztési ciklus, érett geometriai/numerikus ökoszisztéma (pl. numpy, trimesh-szerű mesh-kezelés, DXF-írás), és összhangban van az Engineering Principles "legegyszerűbb megfelelő megoldás" elvével egy egyszemélyes, saját célú eszköznél.

## Következmények

* A `PROJECT_STRUCTURE.md` Python csomagelrendezést fog követni.
* A `CODING_STANDARDS.md` Python-specifikus elvárásokat rögzít majd (típusannotáció, formázó, tesztelési keretrendszer), amikor sorra kerül.
* A determinizmus elvének (Engineering Principles) betartásához külön figyelmet kell fordítani a Python néhány nem-determinisztikus alapértelmezésére (pl. hash randomization, lebegőpontos pontosság) — ezt a `CODING_STANDARDS.md` fogja részletezni.
