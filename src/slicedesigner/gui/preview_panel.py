"""3D előnézet-widget: `pyvistaqt.QtInteractor` beágyazása, az eredeti Mesh
és a szeletelt összeállítás megjelenítésével (ADR-0002, prompt 2.3 szakasz;
ROADMAP Phase 5 "teljes workflow" 1. rész — 3D előnézet feltöltése).
"""

from __future__ import annotations

import logging

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QHBoxLayout, QRadioButton, QVBoxLayout, QWidget
from pyvistaqt import QtInteractor

from slicedesigner.engines.dowel_engine import DowelPosition
from slicedesigner.engines.gap_engine import Spacer
from slicedesigner.engines.mesh_import import Mesh
from slicedesigner.engines.slice_engine import SliceSet
from slicedesigner.gui.render_geometry import (
    dowel_hole_contours_to_polydata,
    dowel_positions_to_polydata,
    mesh_to_polydata,
    slice_set_to_polydata,
    spacers_to_polydata,
)

logger = logging.getLogger(__name__)


class PreviewPanel(QWidget):
    """A középső 3D előnézet-terület.

    Kezdetben üres `QtInteractor`-jelenettel indul, a nézet-váltó
    rádiógombok rejtve maradnak (nincs még megjelenítendő adat). Egy
    sikeres pipeline-futtatás után a `show_mesh()`/`show_sliced_assembly()`
    hívásokkal tölthető fel, ezt követően a rádiógombok aktiválódnak, és a
    váltás a legutóbb kapott `Mesh`/`SliceSet` referenciákat jeleníti meg
    újra — pipeline-újrafuttatás nélkül.

    `QT_QPA_PLATFORM=offscreen` alatt (pl. a smoke tesztben, ablakkezelő
    nélküli CI-környezetben) natív ablak-handle nélkül a VTK
    render-window inicializálása elszáll — ilyenkor a `QtInteractor`
    `off_screen=True` móddal jön létre, ami nem igényel natív ablakot.

    Offscreen alatt az alapértelmezett `auto_update` (a `QtInteractor`
    beépített, kb. 200ms-enként lefutó `render_timer`-je, ami a
    `render()`-t a widget aktuális állapotától/láthatóságától
    függetlenül, a Qt eseményhurok bármelyik feldolgozásakor újra
    lefuttatja) is kikapcsolásra kerül — offscreen, semmit nem
    megjelenítő környezetben nincs értelme az élő újrarajzolásnak, és ez
    volt a natív összeomlás (access violation) forrása: a Qt-teszt-
    keretrendszer (`pytest-qt`) minden teszt köré `app.processEvents()`
    hívásokat illeszt, ami a still-futó `render_timer`-t egy már
    törlés/lezárás alatt álló render-kontextusba futtatta bele.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._mesh: Mesh | None = None
        self._slice_set: SliceSet | None = None
        self._dowel_positions: tuple[DowelPosition, ...] = ()
        self._spacers: tuple[Spacer, ...] = ()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        switch_widget = QWidget(self)
        switch_layout = QHBoxLayout(switch_widget)
        switch_layout.setContentsMargins(0, 0, 0, 0)
        self.show_mesh_radio = QRadioButton("Eredeti Mesh", switch_widget)
        self.show_sliced_assembly_radio = QRadioButton(
            "Szeletelt összeállítás", switch_widget
        )
        self.show_sliced_assembly_radio.setChecked(True)
        switch_layout.addWidget(self.show_mesh_radio)
        switch_layout.addWidget(self.show_sliced_assembly_radio)
        switch_widget.setVisible(False)
        self._switch_widget = switch_widget
        self.show_mesh_radio.toggled.connect(self._on_view_switch_toggled)
        layout.addWidget(switch_widget)

        is_offscreen_platform = QGuiApplication.platformName() == "offscreen"
        self.plotter = QtInteractor(
            self,
            off_screen=is_offscreen_platform,
            auto_update=False if is_offscreen_platform else 5.0,
        )
        layout.addWidget(self.plotter)
        logger.debug("PreviewPanel felépítve, üres jelenettel.")

    def _on_view_switch_toggled(self, mesh_checked: bool) -> None:
        if mesh_checked:
            if self._mesh is not None:
                self._render_mesh(self._mesh)
        else:
            if self._slice_set is not None:
                self._render_sliced_assembly(
                    self._slice_set, self._dowel_positions, self._spacers
                )

    def show_mesh(self, mesh: Mesh) -> None:
        """Az eredeti Mesh megjelenítése, és eltárolása a nézet-váltóhoz."""
        self._mesh = mesh
        self._switch_widget.setVisible(True)
        self._render_mesh(mesh)

    def show_sliced_assembly(
        self,
        slice_set: SliceSet,
        dowel_positions: tuple[DowelPosition, ...] = (),
        spacers: tuple[Spacer, ...] = (),
    ) -> None:
        """A szeletelt összeállítás megjelenítése, és eltárolása a
        nézet-váltóhoz.

        A `slice_set.source_mesh` a nézet-váltó "Eredeti Mesh" oldalához is
        eltárolásra kerül — a hívónak (`MainWindow`) nem kell külön
        `show_mesh()`-t hívnia, a `PipelineResult`-ban már elérhető Mesh
        ehhez elegendő.

        A `dowel_positions`/`spacers` (alapértelmezetten üres) a szolid
        extrudálás mellett Dowel-hengerekként/Spacer-korongokként, a
        lyukas kontúrok pedig Dowel Hole-körvonalként jelennek meg — lásd
        `render_geometry.py`."""
        self._slice_set = slice_set
        self._mesh = slice_set.source_mesh
        self._dowel_positions = dowel_positions
        self._spacers = spacers
        self._switch_widget.setVisible(True)
        self._render_sliced_assembly(slice_set, dowel_positions, spacers)

    def _render_mesh(self, mesh: Mesh) -> None:
        self.plotter.clear()
        self.plotter.add_mesh(mesh_to_polydata(mesh))
        # pyvista `Plotter.reset_camera` is `@wraps`-decorated from
        # `Renderer.reset_camera`, which confuses mypy into requiring an
        # explicit `self` argument on the already-bound call — a pyvista
        # typing quirk, not a real argument-count error.
        self.plotter.reset_camera()  # type: ignore[call-arg]

    def _render_sliced_assembly(
        self,
        slice_set: SliceSet,
        dowel_positions: tuple[DowelPosition, ...] = (),
        spacers: tuple[Spacer, ...] = (),
    ) -> None:
        self.plotter.clear()
        self.plotter.add_mesh(slice_set_to_polydata(slice_set))

        dowel_polydata = dowel_positions_to_polydata(dowel_positions, slice_set)
        if dowel_polydata.n_points > 0:
            self.plotter.add_mesh(dowel_polydata, color="red")

        hole_polydata = dowel_hole_contours_to_polydata(slice_set)
        if hole_polydata.n_points > 0:
            self.plotter.add_mesh(hole_polydata, color="black")

        spacer_polydata = spacers_to_polydata(spacers, slice_set)
        if spacer_polydata.n_points > 0:
            self.plotter.add_mesh(spacer_polydata, color="blue")

        self.plotter.reset_camera()  # type: ignore[call-arg]
