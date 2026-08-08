"""3D előnézet-widget: `pyvistaqt.QtInteractor` beágyazása, az eredeti Mesh
és a szeletelt összeállítás megjelenítésével (ADR-0002, prompt 2.3 szakasz;
ROADMAP Phase 5 "teljes workflow" 1. rész — 3D előnézet feltöltése).
"""

from __future__ import annotations

import logging

import pyvista as pv
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from pyvistaqt import QtInteractor

from slicedesigner.engines.backplate_engine import Backplate, BackplateNormalAxis
from slicedesigner.engines.dowel_engine import DowelPosition
from slicedesigner.engines.gap_engine import Spacer
from slicedesigner.engines.mesh_import import BoundingBox, Mesh
from slicedesigner.engines.slice_engine import SliceSet
from slicedesigner.gui.render_geometry import (
    backplate_to_polydata,
    dowel_hole_contours_to_polydata,
    dowel_positions_to_polydata,
    mesh_to_polydata,
    single_slice_to_polydata,
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
        self._backplate: Backplate | None = None
        self._backplate_normal_axis: BackplateNormalAxis | None = None

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

        # Szeletenkénti kiemelés — kizárólag a "Szeletelt összeállítás"
        # nézetben releváns (lásd `_update_highlight_widget_visibility()`);
        # nincs VTK-picking, a szelet-sorszám kézzel választott (prompt
        # 1. szakasz: a `QtInteractor` korábban instabilnak bizonyult).
        highlight_widget = QWidget(self)
        highlight_layout = QHBoxLayout(highlight_widget)
        highlight_layout.setContentsMargins(0, 0, 0, 0)
        self.highlight_checkbox = QCheckBox("Szelet kiemelése", highlight_widget)
        self.highlight_spinbox = QSpinBox(highlight_widget)
        self.highlight_spinbox.setRange(1, 1)
        self.highlight_spinbox.setEnabled(False)
        highlight_layout.addWidget(self.highlight_checkbox)
        highlight_layout.addWidget(self.highlight_spinbox)
        highlight_widget.setVisible(False)
        self._highlight_widget = highlight_widget
        self.highlight_checkbox.toggled.connect(self.highlight_spinbox.setEnabled)
        self.highlight_checkbox.toggled.connect(self._on_highlight_changed)
        self.highlight_spinbox.valueChanged.connect(self._on_highlight_changed)
        layout.addWidget(highlight_widget)

        is_offscreen_platform = QGuiApplication.platformName() == "offscreen"
        self.plotter = QtInteractor(
            self,
            off_screen=is_offscreen_platform,
            auto_update=False if is_offscreen_platform else 5.0,
        )
        layout.addWidget(self.plotter)

        # Mélység-rendezés (depth peeling) — több áttetsző réteg egyidejű
        # jelenlétekor (kiemeléskor) a helyes vizuális rétegződéshez
        # (enélkül a VTK alapértelmezett, "nincs depth peeling"
        # átlátszóság-renderelése miatt a teljesen átlátszatlan kiemelt
        # szelet is halványabbnak látszódhat). A `number_of_peels=0` a
        # PyVista/VTK-ban "nincs felső korlát"-ot jelent (a megállást az
        # `occlusion_ratio` alapértelmezett `0.0`, azaz pontos eredmény,
        # dönti el) — a PyVista alapértelmezett `number_of_peels=4` élő
        # teszteléskor nem bizonyult elégnek 4-nél több szeletet
        # tartalmazó összeállításoknál, a nem-kiemelt szeletek szinte
        # teljes eltűnését okozva kiemeléskor. Ez VTK-natív hívás — a
        # korábbi, dokumentált VTK/offscreen instabilitás miatt védetten,
        # hogy egy nem támogatott renderelési háttéren (pl. szoftveres
        # OpenGL, offscreen) se akassza meg a `PreviewPanel` felépülését,
        # csak naplózásra kerüljön.
        try:
            # A `# type: ignore` ugyanaz a pyvista `@wraps`-dekorálási
            # typing-fura miatt kell, mint a `reset_camera()`-nál lentebb.
            self.plotter.enable_depth_peeling(  # type: ignore[call-arg]
                number_of_peels=0
            )
        except Exception as error:  # a fenti indoklás szerint szándékosan tág.
            logger.warning(
                "A mélység-rendezés (enable_depth_peeling) nem engedélyezhető "
                "ezen a renderelési háttéren — a 3D előnézet enélkül folytatódik.",
                exc_info=error,
            )

        logger.debug("PreviewPanel felépítve, üres jelenettel.")

    def _on_view_switch_toggled(self, mesh_checked: bool) -> None:
        self._update_highlight_widget_visibility()
        if mesh_checked:
            if self._mesh is not None:
                self._render_mesh(self._mesh)
        else:
            if self._slice_set is not None:
                self._render_sliced_assembly(
                    self._slice_set,
                    self._dowel_positions,
                    self._spacers,
                    self._backplate,
                    self._backplate_normal_axis,
                )

    def _on_highlight_changed(self) -> None:
        """A kiemelés-checkbox/spinbox változásra kötött slot — csak akkor
        renderel újra, ha van már betöltött Slice Set és a "Szeletelt
        összeállítás" nézet aktív (a nézet-váltás ugyanígy ezt hívja meg,
        lásd `_on_view_switch_toggled()`)."""
        if self._slice_set is not None and not self.show_mesh_radio.isChecked():
            self._render_sliced_assembly(
                self._slice_set,
                self._dowel_positions,
                self._spacers,
                self._backplate,
                self._backplate_normal_axis,
            )

    def _update_highlight_widget_visibility(self) -> None:
        self._highlight_widget.setVisible(
            self._slice_set is not None and not self.show_mesh_radio.isChecked()
        )

    def _highlighted_slice_index(self) -> int | None:
        if not self.highlight_checkbox.isChecked():
            return None
        return self.highlight_spinbox.value()

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
        backplate: Backplate | None = None,
        backplate_normal_axis: BackplateNormalAxis | None = None,
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
        `render_geometry.py`. A `backplate` (alapértelmezetten `None` —
        a `use_backplate` kapcsoló ki volt kapcsolva) `backplate_normal_axis`
        nélkül nem ágyazható be a világkoordinátákba — a hívónak (`MainWindow`)
        mindkettőt vagy egyiket sem kell átadnia.
        """
        self._slice_set = slice_set
        self._mesh = slice_set.source_mesh
        self._dowel_positions = dowel_positions
        self._spacers = spacers
        self._backplate = backplate
        self._backplate_normal_axis = backplate_normal_axis
        self._switch_widget.setVisible(True)

        # `blockSignals` — a tartomány-igazítás önmagában nem tekinthető
        # felhasználói kiemelés-változtatásnak, a hívás végén amúgy is
        # explicit render következik.
        self.highlight_spinbox.blockSignals(True)
        self.highlight_spinbox.setRange(1, max(1, slice_set.slice_count))
        self.highlight_spinbox.blockSignals(False)
        self._update_highlight_widget_visibility()

        self._render_sliced_assembly(
            slice_set, dowel_positions, spacers, backplate, backplate_normal_axis
        )

    def _add_origin_gizmo(self, bounding_box: BoundingBox) -> None:
        """A világ-origó és a három pozitív tengelyirány (X, Y, Z)
        megjelenítése apró nyilakkal, valamint az X-Y sík halvány
        jelzése — kizárólag vizuális tájékozódási segédlet (nincs
        geometriai/üzleti hatása), hogy a 3D nézet és az exportált DXF
        egyértelműen, tévedés nélkül összevethető legyen.

        A nyilak/sík mérete a `bounding_box` legnagyobb kiterjedéséhez
        igazodik, hogy kis és nagy modelleknél egyaránt arányos maradjon.
        A színek szándékosan eltérnek a Dowel/Backplate/Spacer réteg-
        színeitől ("red"/"green"/"blue"/"lightgray"), hogy a meglévő,
        szín szerint csoportosító tesztek (`tests/gui/test_preview_panel.py`)
        ne keveredjenek össze velük.
        """
        max_extent = max(bounding_box.max[i] - bounding_box.min[i] for i in range(3))
        arrow_length = max(max_extent * 0.25, 1.0)

        for direction, color in (
            ((1.0, 0.0, 0.0), "orangered"),
            ((0.0, 1.0, 0.0), "mediumseagreen"),
            ((0.0, 0.0, 1.0), "royalblue"),
        ):
            arrow = pv.Arrow(
                start=(0.0, 0.0, 0.0), direction=direction, scale=arrow_length
            )
            self.plotter.add_mesh(arrow, color=color)

        plane_size = max_extent * 1.2
        plane = pv.Plane(
            center=(0.0, 0.0, 0.0),
            direction=(0.0, 0.0, 1.0),
            i_size=plane_size,
            j_size=plane_size,
        )
        self.plotter.add_mesh(plane, color="gainsboro", opacity=0.15)

    def _add_solid_with_edges(
        self, polydata: pv.PolyData, *, color: str, opacity: float = 1.0
    ) -> None:
        """Egy szolid test hozzáadása, valódi (nem háromszögesítési-
        diagonál) kontúréleivel.

        A PyVista/VTK `add_mesh(..., show_edges=True)` MINDEN cella-élt
        kirajzol, beleértve a belső háromszögesítésből (`triangulate()`)
        eredő, sík felületen belüli átlós éleket is — ezek nem valódi
        kontúr-/törésvonalak. Ehelyett a testet `show_edges` nélkül adjuk
        hozzá, a valódi éleket pedig külön réteg-ként,
        `polydata.extract_feature_edges()`-szel: `feature_edges=True` a
        90°-os (a diagonálisok 0°-os) dihedrál-szögű éleket választja ki,
        `manifold_edges=False` explicit kizárja a sík, belső (2 cellához
        tartozó, de nem törésvonal) éleket — empirikusan ellenőrizve egy
        kézzel épített kockán (lásd `tests/gui/test_preview_panel.py`): a
        12 valódi él megmarad, a 6 (lapokénti 1-1) háromszögesítési
        diagonális kimarad.

        A kontúr-réteg ugyanazt az `opacity`-t kapja, mint a hozzá
        tartozó test — a kiemeléskori elhalványítás (`opacity=0.15`) így
        az élekre is helyesen érvényesül.
        """
        self.plotter.add_mesh(polydata, color=color, opacity=opacity)
        edges = polydata.extract_feature_edges(
            feature_angle=30,
            boundary_edges=True,
            non_manifold_edges=True,
            feature_edges=True,
            manifold_edges=False,
        )
        if edges.n_points > 0:
            self.plotter.add_mesh(edges, color="dimgray", opacity=opacity)

    def _render_mesh(self, mesh: Mesh) -> None:
        self.plotter.clear()
        self._add_origin_gizmo(mesh.bounding_box)
        self._add_solid_with_edges(mesh_to_polydata(mesh), color="lightgray")
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
        backplate: Backplate | None = None,
        backplate_normal_axis: BackplateNormalAxis | None = None,
    ) -> None:
        self.plotter.clear()
        self._add_origin_gizmo(slice_set.source_mesh.bounding_box)
        highlighted_index = self._highlighted_slice_index()
        # Kiemeléskor minden más réteg elhalványodik, hogy a kiemelt
        # szelet köré szabadon körbejárható legyen a nézet — a kiemelt
        # szelet és a Dowel Hole-körvonalak mindig teljesen átlátszatlanok
        # maradnak (lásd lentebb, nekik nincs `opacity`-átadás).
        other_layers_opacity = 0.15 if highlighted_index is not None else 1.0

        self._add_solid_with_edges(
            slice_set_to_polydata(slice_set, exclude_slice_index=highlighted_index),
            color="lightgray",
            opacity=other_layers_opacity,
        )

        if highlighted_index is not None:
            highlight_polydata = single_slice_to_polydata(slice_set, highlighted_index)
            if highlight_polydata.n_points > 0:
                self._add_solid_with_edges(highlight_polydata, color="navy")

        dowel_polydata = dowel_positions_to_polydata(dowel_positions, slice_set)
        if dowel_polydata.n_points > 0:
            self.plotter.add_mesh(
                dowel_polydata, color="red", opacity=other_layers_opacity
            )

        hole_polydata = dowel_hole_contours_to_polydata(slice_set)
        if hole_polydata.n_points > 0:
            self.plotter.add_mesh(hole_polydata, color="black")

        spacer_polydata = spacers_to_polydata(spacers, slice_set)
        if spacer_polydata.n_points > 0:
            self.plotter.add_mesh(
                spacer_polydata, color="blue", opacity=other_layers_opacity
            )

        if backplate is not None and backplate_normal_axis is not None:
            backplate_polydata = backplate_to_polydata(
                backplate, slice_set, backplate_normal_axis
            )
            if backplate_polydata.n_points > 0:
                self.plotter.add_mesh(
                    backplate_polydata,
                    color="green",
                    opacity=other_layers_opacity,
                )

        self.plotter.reset_camera()  # type: ignore[call-arg]
