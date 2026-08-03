"""GUI-teszt-specifikus pytest-konfiguráció: VTK/offscreen tesztstabilitás.

`QT_QPA_PLATFORM=offscreen` alatt Windows-on a `pyvistaqt`/VTK render-
kontextusa időszakosan natív összeomlást (access violation) produkált — a
gyökérok a `QtInteractor` beépített, kb. 200ms-enként lefutó
`render_timer`-je volt (`pyvistaqt.plotting.QtInteractor.__init__`,
`auto_update` paraméter): ez a widget aktuális állapotától/láthatóságától
függetlenül újra lefuttatja a `render()`-t a Qt eseményhurok bármelyik
feldolgozásakor, és a `pytest-qt` minden teszt köré `app.processEvents()`
hívásokat illeszt (lásd `pytestqt/plugin.py` `_process_events()`) — a
still-futó `render_timer` így egy már törlés/lezárás alatt álló
render-kontextusba futott bele.

Két, egymásra épülő intézkedés oldja meg:

1. A Qt saját szoftveres OpenGL-implementációjának (Mesa/llvmpipe)
   kikényszerítése (`AA_UseSoftwareOpenGL`), ami nem igényel natív GPU-/
   ablakkezelő-kontextust — ezt kell a `QApplication` létrehozása előtt,
   a legkorábbi ponton beállítani.
2. A `render_timer` explicit kikapcsolása offscreen platform alatt
   (`src/slicedesigner/gui/preview_panel.py`, `QtInteractor(...,
   auto_update=False)`) — offscreen, semmit nem megjelenítő környezetben
   nincs értelme az élő újrarajzolásnak, így nincs mit a still-futó
   timernek egy már törölt kontextusba renderelnie.

E két intézkedés után a 3. szakasz szerinti ellenőrzés (a
`test_main_window.py` önmagában és a teljes tesztsorozattal együtt,
egyenként háromszori futtatása) natív összeomlás nélkül, stabilan zölden
fut — ezért a natív összeomlásra tervezett alprocesszes izoláció
(`pytest-forked`-fallback, ROADMAP prompt 2.2 szakasz) bevezetése nem
indokolt (Constitution 3. elv: ne vezess be plusz komplexitást, ha nincs
rá szükség).

Kizárólag a teszt-futtatásra vonatkozik — a valós, interaktív
alkalmazásindítás (`app.py`) nem használja.
"""

from __future__ import annotations

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """A Qt szoftveres OpenGL-kikényszerítése, a `QApplication` létrehozása
    előtt (lásd a modul-docstringet, 1. intézkedés)."""
    from PySide6.QtCore import QCoreApplication, Qt

    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_UseSoftwareOpenGL)
