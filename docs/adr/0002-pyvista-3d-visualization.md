# ADR-0002: 3D vizualizációs technológia — PyVista + pyvistaqt

Dátum: 2026-08-01
Státusz: Elfogadva
Döntéshozó: Horváth Gyula Attila (projektgazda)

## Kontextus

Az ARCHITECTURE.md GUI komponense kiegészült azzal a felelősséggel, hogy interaktív, forgatható és zoomolható 3D nézetben jelenítse meg az Assembly-t és az egyes Slice-okat a modellen belül (PROJECT_VISION.md 3. szakasz, hatókör-kiegészítés). Az ADR-0001 a Python + PySide technológiai alapot rögzítette, de nem tárgyalta a 3D renderelés konkrét megvalósítását.

## Döntés

A 3D vizualizáció a **PyVista** könyvtárral valósul meg, a **pyvistaqt** csomag `QtInteractor` widgetjén keresztül beágyazva a PySide felületbe.

## Mérlegelt alternatívák

* **Qt3D (PySide6 natív modul)** — natív Qt-integráció, nincs extra nagy függőség, de bonyolultabb és kevésbé dokumentált API, ingadozó karbantartottság.
* **Nyers OpenGL (QOpenGLWidget)** — maximális kontroll, de jelentős fejlesztési overhead, ami ellentétes az Engineering Principles "legegyszerűbb megfelelő megoldás" elvével egy egyszemélyes, saját célú eszköznél.
* **Web-alapú megoldás (three.js, QWebEngineView-ban beágyazva)** — gazdag ökoszisztéma, de a beágyazott böngészőmotor extra függőséget és komplexitást jelent, ami nem illik a natív desktop-fókuszhoz.
* **PyVista + pyvistaqt** — *választott*: numpy-alapú, jól illeszkedik a projekt mesh-feldolgozó ökoszisztémájához (ADR-0001 is "trimesh-szerű mesh-kezelést" említ mint indokot a Python választására); kész, dokumentált Qt-integráció; széles körben elterjedt mérnöki/tudományos 3D vizualizációhoz.

## Következmények

* Új függőségek kerülnek a `pyproject.toml`-ba a Phase 4/5 megkezdésekor: `pyvista`, `pyvistaqt` (és ezek tranzitív függősége, a VTK).
* A `PROJECT_STRUCTURE.md` 5. szakasza szerint a GUI belső felbontása (ablakok, widgetek) Phase 5-ben kerül kidolgozásra — ott a 3D nézet konkrét elhelyezése és interakciója ezen ADR alapján történik.
* A `CODING_STANDARDS.md`-t nem érinti közvetlenül, de jövőbeli GUI-specifikációk hivatkozhatnak erre az ADR-re.
