"""3D előnézet-widget: `pyvistaqt.QtInteractor` beágyazása, az eredeti Mesh
és a szeletelt összeállítás megjelenítésével (ADR-0002, prompt 2.3 szakasz;
ROADMAP Phase 5 "teljes workflow" 1. rész — 3D előnézet feltöltése).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import pyvista as pv
from PySide6.QtCore import QObject, QPointF, QRectF, Qt, QThread, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QGuiApplication,
    QPainterPath,
    QPen,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QPushButton,
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
from slicedesigner.engines.nesting_engine import MaterialDefinition, Nest
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

# --- 2D export-előnézet (EXPORT_PREVIEW_SPEC.md 5. szakasz) ---
#
# A vágási kontúrok/azonosítók előnézeti színei szándékosan függetlenek a
# tényleges DXF export réteg-színeitől (`cut_layer_color`/
# `engrave_layer_color`), mert azok Futtatáskor még nem feltétlenül
# állítottak be — l. `PreviewPanel._render_current_sheet()`.
_PREVIEW_CUT_COLOR = QColor("black")
_PREVIEW_ENGRAVE_COLOR = QColor("blue")
_PREVIEW_SHEET_BACKGROUND_COLOR = QColor("whitesmoke")
_PREVIEW_SHEET_BORDER_COLOR = QColor("darkgray")

# A nagyítás megengedett tartománya, a lapváltáskori "illessz ablakhoz"
# alapállapothoz (fitInView) képest relatív szorzóként értelmezve — l.
# `_NestingGraphicsView.wheelEvent()`.
_PREVIEW_MIN_ZOOM = 0.1
_PREVIEW_MAX_ZOOM = 10.0
# Egérgörgő-notch-onkénti fix nagyítási szorzó.
_PREVIEW_ZOOM_STEP_FACTOR = 1.15


def _to_scene_point(x: float, y: float) -> QPointF:
    """Domain-koordináta (X jobbra, Y felfelé, mm) → `QGraphicsScene`-
    koordináta (X jobbra, Y lefelé) — a Y-tengely megfordítása EGYETLEN,
    jól látható helyen történik, hogy a 2D előnézet a fizikai/DXF-
    elrendezéssel megegyező (nem tükrözött) tájolást mutasson."""
    return QPointF(x, -y)


def _points_to_path(
    points: tuple[tuple[float, float], ...], *, closed: bool
) -> QPainterPath:
    """Egy pontsorozat `QPainterPath`-szá alakítása — zárt (`closed=True`,
    vágási kontúrok) vagy nyitott (`closed=False`, azonosító-vonáskötegek)
    módban."""
    path = QPainterPath()
    if not points:
        return path
    path.moveTo(_to_scene_point(*points[0]))
    for x, y in points[1:]:
        path.lineTo(_to_scene_point(x, y))
    if closed:
        path.closeSubpath()
    return path


class _NestingGraphicsView(QGraphicsView):
    """`QGraphicsView`-alosztály, kizárólag az egérgörgős nagyítás
    felülírásához (EXPORT_PREVIEW_SPEC.md 6.7. pont) — a kattintva-húzva
    mozgatás (pan) a Qt beépített `ScrollHandDrag` módjával működik,
    felülírás nélkül (l. `PreviewPanel.__init__`).

    `self._zoom_factor` az utolsó `reset_zoom_tracking()` (lapváltáskor, a
    `fitInView`-hívás UTÁN) óta alkalmazott, összesített nagyítási szorzót
    követi — ez korlátozza a nagyítást `_PREVIEW_MIN_ZOOM`/
    `_PREVIEW_MAX_ZOOM` közé, a fit-to-window alapállapothoz képest
    relatívan."""

    def __init__(self, scene: QGraphicsScene, parent: QWidget | None = None) -> None:
        super().__init__(scene, parent)
        self._zoom_factor = 1.0

    def reset_zoom_tracking(self) -> None:
        self._zoom_factor = 1.0

    def wheelEvent(self, event: QWheelEvent) -> None:
        angle_delta = event.angleDelta().y()
        if angle_delta == 0:
            return
        step_factor = (
            _PREVIEW_ZOOM_STEP_FACTOR
            if angle_delta > 0
            else 1 / _PREVIEW_ZOOM_STEP_FACTOR
        )
        new_zoom_factor = self._zoom_factor * step_factor
        if not (_PREVIEW_MIN_ZOOM <= new_zoom_factor <= _PREVIEW_MAX_ZOOM):
            return
        self._zoom_factor = new_zoom_factor
        self.scale(step_factor, step_factor)


@dataclass(frozen=True)
class _PreviewGeometryBundle:
    """A szeletelt összeállítás geometria-építő részének
    (`render_geometry.py`-hívások) kész eredménye, egy kötegben —
    `_PreviewComputeWorker` adja vissza a `succeeded` jelzéssel, hogy a
    tényleges VTK-renderelés (`PreviewPanel._render_geometry_bundle()`)
    a fő szálon, már kizárólag kész `PolyData`-objektumokból, további
    geometria-építés nélkül történhessen (ADR-0011).

    A `highlight_polydata`/`backplate_polydata` `None`, ha nincs
    megjelenítendő kiemelés/Backplate (vagy a hozzá tartozó `PolyData`
    üres) — `_render_geometry_bundle()` ezt a korábbi, egybefont
    `_render_sliced_assembly()` `if ... n_points > 0` feltételeivel
    megegyezően értelmezi.
    """

    slice_set: SliceSet
    other_layers_opacity: float
    main_polydata: pv.PolyData
    highlight_polydata: pv.PolyData | None
    dowel_polydata: pv.PolyData
    hole_polydata: pv.PolyData
    spacer_polydata: pv.PolyData
    backplate_polydata: pv.PolyData | None


def _build_sliced_assembly_geometry(
    slice_set: SliceSet,
    dowel_positions: tuple[DowelPosition, ...],
    spacers: tuple[Spacer, ...],
    backplate: Backplate | None,
    backplate_normal_axis: BackplateNormalAxis | None,
    highlighted_index: int | None,
) -> _PreviewGeometryBundle:
    """A szeletelt összeállítás geometria-építő része — kizárólag
    `render_geometry.py`-hívások, semmilyen Qt/VTK-`plotter`-hozzáférés
    (l. e modul és a `render_geometry.py` docstringjét) — hogy
    `_PreviewComputeWorker` háttérszálon biztonságosan futtathassa
    (ADR-0011). A `render_geometry.py` maga nem változott — ez a
    függvény szó szerint ugyanazokat a hívásokat végzi el, ugyanabban a
    sorrendben, mint amit korábban a rendereléssel egybefont
    `_render_sliced_assembly()` tett.
    """
    other_layers_opacity = 0.15 if highlighted_index is not None else 1.0

    main_polydata = slice_set_to_polydata(
        slice_set, exclude_slice_index=highlighted_index
    )

    highlight_polydata: pv.PolyData | None = None
    if highlighted_index is not None:
        candidate = single_slice_to_polydata(slice_set, highlighted_index)
        if candidate.n_points > 0:
            highlight_polydata = candidate

    dowel_polydata = dowel_positions_to_polydata(dowel_positions, slice_set)
    hole_polydata = dowel_hole_contours_to_polydata(slice_set)
    spacer_polydata = spacers_to_polydata(spacers, slice_set)

    backplate_polydata: pv.PolyData | None = None
    if backplate is not None and backplate_normal_axis is not None:
        candidate = backplate_to_polydata(backplate, slice_set, backplate_normal_axis)
        if candidate.n_points > 0:
            backplate_polydata = candidate

    return _PreviewGeometryBundle(
        slice_set=slice_set,
        other_layers_opacity=other_layers_opacity,
        main_polydata=main_polydata,
        highlight_polydata=highlight_polydata,
        dowel_polydata=dowel_polydata,
        hole_polydata=hole_polydata,
        spacer_polydata=spacer_polydata,
        backplate_polydata=backplate_polydata,
    )


@dataclass(frozen=True)
class _PreviewRenderSucceeded:
    """A `_PreviewComputeWorker.succeeded` jelzésének kísérő adatai —
    a `generation` (l. `PreviewPanel._render_generation`, ADR-0012) és az
    `is_post_run` (Futtatás utáni vs. interaktív kiemelés-/nézet-váltás
    eredetű) együtt utazik a kész `bundle`-lel, hogy a fogadó
    (`PreviewPanel._on_preview_geometry_ready()`) egyetlen, megosztott
    slotként tudja helyesen kezelni MINDHÁROM hívási helyet."""

    generation: int
    is_post_run: bool
    bundle: _PreviewGeometryBundle


@dataclass(frozen=True)
class _PreviewRenderFailed:
    """A `_PreviewComputeWorker.failed` jelzésének kísérő adatai — l.
    `_PreviewRenderSucceeded` docstringje."""

    generation: int
    is_post_run: bool
    error: Exception


class _PreviewComputeWorker(QThread):
    """Háttérszál: kizárólag a szeletelt összeállítás GEOMETRIA-építő
    részét (`_build_sliced_assembly_geometry()`, azaz a
    `render_geometry.py`-hívásokat) végzi el — semmilyen VTK/`plotter`-
    hívás nem történik itt (Qt/OpenGL-kontextus-kötött, kizárólag a fő
    szálon biztonságos), ezért futtatása a fő száltól elkülönítve
    biztonságos (ADR-0011).

    A Futtatás utáni első megjelenítéshez ÉS a kiemelés-/nézet-váltás
    interaktív újraépítéséhez is EZT az egyetlen worker-osztályt
    használja (ADR-0012) — a `generation`/`is_post_run` paraméterek
    különböztetik meg a két esetet a `PreviewPanel` fogadó oldalán (l.
    `_on_preview_geometry_ready()`/`_on_preview_geometry_failed()`): a
    `generation` teszi lehetővé, hogy egy elavult (közben egy újabb
    render által felülírt) interaktív eredmény csendben eldobásra
    kerüljön ahelyett, hogy hibásan felülírná a plottert egy frissebb
    eredmény felett.

    A `main_window.py::_PipelineWorker` mintáját követi: `QThread`-
    alosztály `run()`-felülírással, egyetlen blokkoló hívás-sorozatot
    végez el egyszer, `succeeded`/`failed` jelzéssel adja vissza az
    eredményt a fő szálon futó fogadóhoz (queued connection — a
    `PreviewPanel`, a fogadó, a fő szál affinitású marad, csak a
    `run()`-on belüli kód fut ténylegesen a háttérszálon).
    """

    succeeded = Signal(object)  # _PreviewRenderSucceeded
    failed = Signal(object)  # _PreviewRenderFailed

    def __init__(
        self,
        slice_set: SliceSet,
        dowel_positions: tuple[DowelPosition, ...],
        spacers: tuple[Spacer, ...],
        backplate: Backplate | None,
        backplate_normal_axis: BackplateNormalAxis | None,
        highlighted_index: int | None,
        generation: int,
        *,
        is_post_run: bool,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._slice_set = slice_set
        self._dowel_positions = dowel_positions
        self._spacers = spacers
        self._backplate = backplate
        self._backplate_normal_axis = backplate_normal_axis
        self._highlighted_index = highlighted_index
        self._generation = generation
        self._is_post_run = is_post_run

    def run(self) -> None:
        try:
            bundle = _build_sliced_assembly_geometry(
                self._slice_set,
                self._dowel_positions,
                self._spacers,
                self._backplate,
                self._backplate_normal_axis,
                self._highlighted_index,
            )
        except Exception as error:  # a render_geometry.py függvényei tiszta,
            # már validált SliceSet-en dolgoznak — gyakorlatban itt hiba nem
            # várható, de a `_PipelineWorker`-nél megszokott, szándékosan
            # tág védelem itt is indokolt: egy háttérszálon elszálló,
            # elkapatlan kivétel a `succeeded`/`failed` jelzés nélkül
            # néma szál-leállást okozna, a `PreviewPanel`-t örökre "függő"
            # (Futtatás gomb letiltva maradó) állapotban hagyva.
            self.failed.emit(
                _PreviewRenderFailed(
                    generation=self._generation,
                    is_post_run=self._is_post_run,
                    error=error,
                )
            )
        else:
            self.succeeded.emit(
                _PreviewRenderSucceeded(
                    generation=self._generation,
                    is_post_run=self._is_post_run,
                    bundle=bundle,
                )
            )


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

    A Futtatás utáni első megjelenítés (`show_sliced_assembly()`), a
    kiemelés-váltás (`_on_highlight_changed()`) ÉS a nézet-váltás
    (`_on_view_switch_toggled()`, "Szeletelt összeállítás" ág) geometria-
    építése egyaránt háttérszálon fut (ADR-0011, ADR-0012) — a hívó
    (`MainWindow`) kizárólag a Futtatás utáni útvonalról szerez tudomást
    az `assembly_render_succeeded`/`assembly_render_failed` jelzéseken
    keresztül (a Futtatás-állapot lezárásához); a kiemelés-/nézet-váltás
    ezeket a jelzéseket SOSEM emittálja (ADR-0012 — a `MainWindow`-t nem
    érinti). Egy `self._render_generation` számláló biztosítja, hogy egy
    elavult (közben egy újabb render által felülírt) interaktív eredmény
    sose írja felül a nézeten egy közben elindult, frissebb rendert — a
    Futtatás utáni renderre ez az ellenőrzés nem vonatkozik (l.
    `_on_preview_geometry_ready()` docstringjét).
    """

    assembly_render_succeeded = Signal()
    assembly_render_failed = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._mesh: Mesh | None = None
        self._slice_set: SliceSet | None = None
        self._dowel_positions: tuple[DowelPosition, ...] = ()
        self._spacers: tuple[Spacer, ...] = ()
        self._backplate: Backplate | None = None
        self._backplate_normal_axis: BackplateNormalAxis | None = None
        self._preview_worker: _PreviewComputeWorker | None = None
        # Minden async-render indításkor eggyel nő (a Futtatás utáni is
        # beleértve) — l. `_start_async_sliced_assembly_render()` és
        # `_on_preview_geometry_ready()` (ADR-0012).
        self._render_generation = 0

        # 2D export-előnézet (EXPORT_PREVIEW_SPEC.md) — a legutóbbi
        # sikeres Futtatás `Nest`-jei és a hozzájuk tartozó
        # anyag-lapméretek; l. `show_nests()`.
        self._nests: tuple[Nest, ...] = ()
        self._material_definitions: tuple[MaterialDefinition, ...] = ()
        # Determinisztikus lap-sorrend: (material_id, sheet_number) párok,
        # material_id szerint ábécésorrendben, azon belül 1..sheet_count
        # laponkénti sorszám szerint — l. `show_nests()`.
        self._sheet_keys: list[tuple[str, int]] = []
        self._current_sheet_index = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 3D/2D nézet-váltó — a `switch_widget` FÖLÖTT, önálló sorban
        # (EXPORT_PREVIEW_SPEC.md). A `show_2d_radio` kezdetben letiltott —
        # csak `show_nests()` után válik engedélyezetté.
        mode_widget = QWidget(self)
        mode_layout = QHBoxLayout(mode_widget)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        self.show_3d_radio = QRadioButton("3D", mode_widget)
        self.show_2d_radio = QRadioButton("2D (export-előnézet)", mode_widget)
        self.show_3d_radio.setChecked(True)
        self.show_2d_radio.setEnabled(False)
        self.show_2d_radio.setToolTip("Nincs még Futtatás eredménye.")
        mode_layout.addWidget(self.show_3d_radio)
        mode_layout.addWidget(self.show_2d_radio)
        layout.addWidget(mode_widget)
        self.show_2d_radio.toggled.connect(self._on_3d_2d_toggled)

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

        # 2D export-előnézet widget-csoport (EXPORT_PREVIEW_SPEC.md) —
        # kezdetben rejtett, csak 2D módban látható (l.
        # `_sync_view_mode_visibility()`).
        nesting_2d_widget = QWidget(self)
        nesting_2d_layout = QVBoxLayout(nesting_2d_widget)
        nesting_2d_layout.setContentsMargins(0, 0, 0, 0)

        nesting_nav_widget = QWidget(nesting_2d_widget)
        nesting_nav_layout = QHBoxLayout(nesting_nav_widget)
        nesting_nav_layout.setContentsMargins(0, 0, 0, 0)
        self.nesting_prev_button = QPushButton("◀ Előző lap", nesting_nav_widget)
        self.nesting_sheet_label = QLabel("", nesting_nav_widget)
        self.nesting_next_button = QPushButton("Következő lap ▶", nesting_nav_widget)
        self.nesting_prev_button.setEnabled(False)
        self.nesting_next_button.setEnabled(False)
        self.nesting_prev_button.clicked.connect(self._on_nesting_prev_clicked)
        self.nesting_next_button.clicked.connect(self._on_nesting_next_clicked)
        nesting_nav_layout.addWidget(self.nesting_prev_button)
        nesting_nav_layout.addWidget(self.nesting_sheet_label)
        nesting_nav_layout.addWidget(self.nesting_next_button)
        nesting_2d_layout.addWidget(nesting_nav_widget)

        self._nesting_scene = QGraphicsScene(nesting_2d_widget)
        self.nesting_view = _NestingGraphicsView(self._nesting_scene, nesting_2d_widget)
        self.nesting_view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        nesting_2d_layout.addWidget(self.nesting_view)

        nesting_2d_widget.setVisible(False)
        self._nesting_2d_widget = nesting_2d_widget
        layout.addWidget(nesting_2d_widget)

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

        self._sync_view_mode_visibility()
        logger.debug("PreviewPanel felépítve, üres jelenettel.")

    def _on_view_switch_toggled(self, mesh_checked: bool) -> None:
        self._update_highlight_widget_visibility()
        if mesh_checked:
            if self._mesh is not None:
                self._render_mesh(self._mesh)
        else:
            if self._slice_set is not None:
                self._start_async_sliced_assembly_render(
                    self._slice_set,
                    self._dowel_positions,
                    self._spacers,
                    self._backplate,
                    self._backplate_normal_axis,
                    is_post_run=False,
                )

    def _on_highlight_changed(self) -> None:
        """A kiemelés-checkbox/spinbox változásra kötött slot — csak akkor
        renderel újra, ha van már betöltött Slice Set és a "Szeletelt
        összeállítás" nézet aktív (a nézet-váltás ugyanígy ezt hívja meg,
        lásd `_on_view_switch_toggled()`)."""
        if self._slice_set is not None and not self.show_mesh_radio.isChecked():
            self._start_async_sliced_assembly_render(
                self._slice_set,
                self._dowel_positions,
                self._spacers,
                self._backplate,
                self._backplate_normal_axis,
                is_post_run=False,
            )

    def _update_highlight_widget_visibility(self) -> None:
        self._highlight_widget.setVisible(
            not self.show_2d_radio.isChecked()
            and self._slice_set is not None
            and not self.show_mesh_radio.isChecked()
        )

    def _on_3d_2d_toggled(self, show_2d: bool) -> None:
        """A 3D/2D nézet-váltó rádiógombjaira kötött slot
        (EXPORT_PREVIEW_SPEC.md 6.1–6.2. pont) — kizárólag a widget-
        láthatóságot vezérli, nem indít pipeline- vagy geometria-
        újraszámítást: a 2D rajz a már eltárolt `self._nests`-ből, a 3D
        pedig a már eltárolt `self._mesh`/`self._slice_set`-ből azonnal
        elérhető."""
        self._sync_view_mode_visibility()
        if show_2d:
            self._render_current_sheet()

    def _sync_view_mode_visibility(self) -> None:
        """A 3D-widgetek (nézet-váltó, kiemelés, `plotter`) és a 2D-widget-
        csoport láthatóságának szinkronizálása az aktuális 3D/2D
        mód-választással.

        A `show_mesh()`/`show_sliced_assembly()` (amik korábban a
        `switch_widget`-et feltétel nélkül láthatóvá tették) is EZT hívják
        a láthatóság frissítéséhez — enélkül egy, a 2D nézetben aktívan
        tartózkodó felhasználónál egy közben lezajló új Futtatás
        visszakapcsolná láthatóvá a 3D-widgeteket a 2D-csoport mögött."""
        show_2d = self.show_2d_radio.isChecked()
        self._switch_widget.setVisible(not show_2d and self._mesh is not None)
        self.plotter.setVisible(not show_2d)
        self._update_highlight_widget_visibility()
        self._nesting_2d_widget.setVisible(show_2d)

    def _highlighted_slice_index(self) -> int | None:
        if not self.highlight_checkbox.isChecked():
            return None
        return self.highlight_spinbox.value()

    def show_mesh(self, mesh: Mesh) -> None:
        """Az eredeti Mesh megjelenítése, és eltárolása a nézet-váltóhoz."""
        self._mesh = mesh
        self._sync_view_mode_visibility()
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

        A widget-állapot (tárolt referenciák, spinbox-tartomány,
        láthatóság) SZINKRON, azonnal frissül — csak a tényleges
        geometria-építés/renderelés indul háttérszálon, azonnal visszatérő
        hívással (ADR-0011). A hívó (`MainWindow`) az
        `assembly_render_succeeded`/`assembly_render_failed` jelzésekre
        kötve értesül a tényleges befejezésről.
        """
        self._slice_set = slice_set
        self._mesh = slice_set.source_mesh
        self._dowel_positions = dowel_positions
        self._spacers = spacers
        self._backplate = backplate
        self._backplate_normal_axis = backplate_normal_axis

        # `blockSignals` — a tartomány-igazítás önmagában nem tekinthető
        # felhasználói kiemelés-változtatásnak, a hívás végén amúgy is
        # explicit render következik.
        self.highlight_spinbox.blockSignals(True)
        self.highlight_spinbox.setRange(1, max(1, slice_set.slice_count))
        self.highlight_spinbox.blockSignals(False)
        self._sync_view_mode_visibility()

        self._start_async_sliced_assembly_render(
            slice_set,
            dowel_positions,
            spacers,
            backplate,
            backplate_normal_axis,
            is_post_run=True,
        )

    def _start_async_sliced_assembly_render(
        self,
        slice_set: SliceSet,
        dowel_positions: tuple[DowelPosition, ...],
        spacers: tuple[Spacer, ...],
        backplate: Backplate | None,
        backplate_normal_axis: BackplateNormalAxis | None,
        *,
        is_post_run: bool,
    ) -> None:
        """A geometria-építés háttérszálra indítása, azonnali visszatéréssel
        (ADR-0011) — a Futtatás utáni első megjelenítéshez
        (`show_sliced_assembly()`, `is_post_run=True`) ÉS a kiemelés-/
        nézet-váltáshoz (`_on_highlight_changed()`/`_on_view_switch_toggled()`,
        `is_post_run=False`) egyaránt (ADR-0012).

        Minden hívás — a Futtatás utáni is — eggyel növeli
        `self._render_generation`-t, és ezt a (hívás pillanatában
        rögzített) generációt adja át a workernek; lásd
        `_on_preview_geometry_ready()` a felhasználásáról.

        A kiemelés-index a HÍVÁS PILLANATÁBAN kerül rögzítésre (átadva a
        workernek), nem a renderelés idején újra lekérdezve — ez teszi
        lehetővé, hogy egy gyors egymásutáni kiemelés-váltás-sorozat
        minden tagja a SAJÁT, indításkori állapotát építse fel, még akkor
        is, ha a widget-állapot időközben tovább változik.
        """
        self._render_generation += 1
        highlighted_index = self._highlighted_slice_index()
        worker = _PreviewComputeWorker(
            slice_set,
            dowel_positions,
            spacers,
            backplate,
            backplate_normal_axis,
            highlighted_index,
            self._render_generation,
            is_post_run=is_post_run,
            parent=self,
        )
        worker.succeeded.connect(self._on_preview_geometry_ready)
        worker.failed.connect(self._on_preview_geometry_failed)
        worker.finished.connect(worker.deleteLater)
        self._preview_worker = worker
        worker.start()

    def _on_preview_geometry_ready(self, outcome: _PreviewRenderSucceeded) -> None:
        """A `_PreviewComputeWorker.succeeded` jelzésre kötött, MEGOSZTOTT
        slot (fő szál) — a Futtatás utáni ÉS a kiemelés-/nézet-váltás
        eredetű workerek is ide futnak be (ADR-0012).

        **Futtatás utáni** (`outcome.is_post_run`): változatlan viselkedés
        — mindig renderel, mindig emittálja a publikus
        `assembly_render_succeeded`-t, staleness-ellenőrzés nélkül (két
        egyidejű Futtatás-eredetű worker strukturálisan kizárt, mert a
        "Futtatás" gomb a teljes folyamat alatt letiltva marad).

        **Kiemelés-/nézet-váltás eredetű** (`not outcome.is_post_run`):
        HA `outcome.generation` már nem egyezik `self._render_generation`
        aktuális értékével (mert közben — akár interaktív, akár Futtatás-
        eredetű — egy újabb render indult), a bundle csendben eldobásra
        kerül — SEM a plotter, SEM a `MainWindow` felé nem emittált
        publikus jelzés nem történik. Ez zárja el az ADR-0011
        "külön mérlegelés tárgya" pontját: egy régebbi, később
        befejeződő interaktív render sosem írhatja felül egy közben
        elindult, frissebb (akár Futtatás-eredetű) render eredményét.
        """
        if outcome.is_post_run:
            self._render_geometry_bundle(outcome.bundle)
            self._preview_worker = None
            self.assembly_render_succeeded.emit()
            return

        if outcome.generation != self._render_generation:
            return  # elavult interaktív render — csendes eldobás
        self._render_geometry_bundle(outcome.bundle)
        self._preview_worker = None

    def _on_preview_geometry_failed(self, outcome: _PreviewRenderFailed) -> None:
        """A `_PreviewComputeWorker.failed` jelzésre kötött, MEGOSZTOTT
        slot (fő szál) — l. `_on_preview_geometry_ready()` docstringjét a
        Futtatás utáni/kiemelés-/nézet-váltás eredetű megkülönböztetésről.

        A `render_geometry.py` függvényei tiszta, már validált
        `SliceSet`-en dolgoznak — gyakorlatban itt hiba nem várható, de a
        `_PipelineWorker` mintáját követve, védelemből mégis kezelve van
        (CODING_STANDARDS 5. szakasz: minden elkapott kivétel naplózásra
        kerül, kivéve az elavult interaktív hibát — az a csendes eldobás
        részeként ugyanúgy figyelmen kívül marad, mint egy elavult siker).
        """
        if outcome.is_post_run:
            logger.exception(
                "Hiba a 3D-előnézet geometria-építése során (háttérszál).",
                exc_info=outcome.error,
            )
            self._preview_worker = None
            self.assembly_render_failed.emit(outcome.error)
            return

        if outcome.generation != self._render_generation:
            return  # elavult interaktív render — csendes eldobás
        logger.exception(
            "Hiba a 3D-előnézet interaktív (kiemelés-/nézet-váltás) "
            "geometria-építése során (háttérszál).",
            exc_info=outcome.error,
        )
        self._preview_worker = None

    def _render_geometry_bundle(self, bundle: _PreviewGeometryBundle) -> None:
        """A `_PreviewGeometryBundle` tényleges VTK-renderelése —
        kizárólag `plotter`-hívások, geometria-építés nélkül. Ez a rész
        MINDIG a fő szálon fut (ADR-0011: `clear()`/`add_mesh()`/
        `reset_camera()` Qt/OpenGL-kontextus-kötött, kizárólag a fő
        szálon biztonságos)."""
        self._clear_plotter()
        self._add_origin_gizmo(bundle.slice_set.source_mesh.bounding_box)

        self._add_solid_with_edges(
            bundle.main_polydata,
            color="#7E4B26",
            opacity=bundle.other_layers_opacity,
            edge_color="#1A1719",
            ambient=0.3,
        )
        if bundle.highlight_polydata is not None:
            self._add_solid_with_edges(bundle.highlight_polydata, color="navy")

        if bundle.dowel_polydata.n_points > 0:
            self.plotter.add_mesh(
                bundle.dowel_polydata, color="red", opacity=bundle.other_layers_opacity
            )

        if bundle.hole_polydata.n_points > 0:
            self.plotter.add_mesh(bundle.hole_polydata, color="black")

        if bundle.spacer_polydata.n_points > 0:
            self.plotter.add_mesh(
                bundle.spacer_polydata,
                color="blue",
                opacity=bundle.other_layers_opacity,
            )

        if bundle.backplate_polydata is not None:
            self.plotter.add_mesh(
                bundle.backplate_polydata,
                color="green",
                opacity=bundle.other_layers_opacity,
            )

        self.plotter.reset_camera()  # type: ignore[call-arg]

    def _clear_plotter(self) -> None:
        """`self.plotter.clear()`, a jelenet fényforrásainak visszaállításával.

        A PyVista `Plotter.clear()` — a dokumentációjával ellentétben, ami
        csak "removing all actors and properties"-t ígér — a jelenet
        ÖSSZES fényforrását (`renderer.lights`) is eltávolítja, és semmi
        nem állítja azokat automatikusan vissza. Fényforrás nélkül a
        renderelés kizárólag az ambiens komponensre esik vissza — ez
        okozta azt, hogy a `_add_solid_with_edges()` `smooth_shading`/
        `specular` beállítása (2026-08-21-i kiegészítés) az ELSŐ
        `clear()`-t (azaz gyakorlatilag minden renderelést) követően
        látszólag semmilyen hatással nem volt: a felület lapos,
        egybefüggő, egyszínű maszatnak látszott, függetlenül a GPU-tól/
        drivertől — élő teszteléskor derült ki, hogy nem renderelési
        háttér-korlátozás, hanem ez a fényforrás-elvesztés az ok.

        A `plotter.enable_lightkit()` állítja vissza a `QtInteractor`
        konstruktorakor alapértelmezetten beállított 5 fényforrásos
        "light kit"-et."""
        self.plotter.clear()
        self.plotter.enable_lightkit()

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
        self,
        polydata: pv.PolyData,
        *,
        color: str,
        opacity: float = 1.0,
        edge_color: str = "dimgray",
        smooth_shading: bool = False,
        ambient: float = 0.0,
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

        A `smooth_shading` (alapértelmezetten `False`) mérsékelt
        `specular`-ral együtt kapcsolja be a Phong-árnyalást
        (2026-08-21-i kiegészítés) — enélkül a lapos (facettázott)
        árnyékolás és a nulla specularitás miatt finom, alacsony
        amplitúdójú felületmintázatoknál (pl. Wave Generator relief)
        gyakorlatilag csak a fenti kontúrél-réteg látszott, maga a
        felület vizuálisan "belesimult" egy sík, egyszínű testbe. Ez
        kizárólag az "Eredeti Mesh" nézetben (`_render_mesh()`) kell —
        a "Szeletelt összeállítás" nézetben (`_render_geometry_bundle()`)
        a geometria fizikailag is lapos, vízszintes rétegek egymásra
        halmozásából áll (`render_geometry.py::slice_set_to_polydata()`
        — minden Slice külön, saját lapos extrudálású test), ott a Phong-
        árnyalás nem tudna mit "elsimítani", csak a rétegek határán
        keltene zavaró, a tényleges geometriától idegen fényes csíkokat.
        A kontúrél-réteg (egyszerű vonalgeometria) SOSEM kap
        `smooth_shading`/`specular`-t — ott nincs értelme.

        Az `ambient` (alapértelmezetten `0.0` — nincs hatása, a
        korábbi viselkedést megőrzi) iránytól független alap-
        megvilágítást ad hozzá — a `smooth_shading`-től eltérően NEM
        interpolál normálvektorokat, ezért nem hozza vissza a rétegek
        közti hamis fénycsíkozást. Bevezetése: a 2026-08-21-i
        fényforrás-hiba javítása (`enable_lightkit()`) óta a "Szeletelt
        összeállítás" nézet fénytől elforduló, facettázott felületei
        (a `smooth_shading=False` miatt) túl sötétnek látszottak —
        élő tesztelés jelezte.
        """
        solid_kwargs: dict[str, object] = {}
        if smooth_shading:
            solid_kwargs["smooth_shading"] = True
            solid_kwargs["specular"] = 0.5
            solid_kwargs["specular_power"] = 15
        if ambient != 0.0:
            solid_kwargs["ambient"] = ambient
        self.plotter.add_mesh(polydata, color=color, opacity=opacity, **solid_kwargs)
        edges = polydata.extract_feature_edges(
            feature_angle=30,
            boundary_edges=True,
            non_manifold_edges=True,
            feature_edges=True,
            manifold_edges=False,
        )
        if edges.n_points > 0:
            self.plotter.add_mesh(edges, color=edge_color, opacity=opacity)

    def _render_mesh(self, mesh: Mesh) -> None:
        self._clear_plotter()
        self._add_origin_gizmo(mesh.bounding_box)
        self._add_solid_with_edges(
            mesh_to_polydata(mesh), color="lightgray", smooth_shading=True
        )
        # pyvista `Plotter.reset_camera` is `@wraps`-decorated from
        # `Renderer.reset_camera`, which confuses mypy into requiring an
        # explicit `self` argument on the already-bound call — a pyvista
        # typing quirk, not a real argument-count error.
        self.plotter.reset_camera()  # type: ignore[call-arg]

    # --- 2D export-előnézet (EXPORT_PREVIEW_SPEC.md) ---

    def show_nests(
        self,
        nests: tuple[Nest, ...],
        material_definitions: tuple[MaterialDefinition, ...],
    ) -> None:
        """A legutóbbi sikeres Futtatás `Nest`-jeinek eltárolása a 2D
        export-előnézethez, és a `show_2d_radio` engedélyezése, ha van
        megjeleníthető lap.

        Ha éppen 2D mód aktív, a nézet azonnal újrarajzolásra kerül, az
        ELSŐ lapra visszaállva (EXPORT_PREVIEW_SPEC.md 6.4. pont). Ha 3D
        mód aktív, a mód-választás NEM változik — csak az eltárolt adat
        frissül, a tényleges 2D rajzolás a következő 2D-re váltáskor
        történik meg."""
        self._nests = nests
        self._material_definitions = material_definitions
        self._sheet_keys = [
            (nest.material_id, sheet_number)
            for nest in sorted(nests, key=lambda n: n.material_id)
            for sheet_number in range(1, nest.sheet_count + 1)
        ]
        self._current_sheet_index = 0

        has_sheets = len(self._sheet_keys) > 0
        self.show_2d_radio.setEnabled(has_sheets)
        self.show_2d_radio.setToolTip(
            "" if has_sheets else "Nincs még Futtatás eredménye."
        )

        if self.show_2d_radio.isChecked():
            self._render_current_sheet()

    def _on_nesting_prev_clicked(self) -> None:
        if self._current_sheet_index > 0:
            self._current_sheet_index -= 1
            self._render_current_sheet()

    def _on_nesting_next_clicked(self) -> None:
        if self._current_sheet_index < len(self._sheet_keys) - 1:
            self._current_sheet_index += 1
            self._render_current_sheet()

    def _render_current_sheet(self) -> None:
        """Az aktuális lap (`self._sheet_keys[self._current_sheet_index]`)
        2D rajzolása — szinkron, a fő szálon: a `Nest`-adat már teljesen
        kiszámított, nincs geometria-építés, csak meglévő pontlisták
        rajzolása (EXPORT_PREVIEW_SPEC.md korlátozás)."""
        self._nesting_scene.clear()

        if not self._sheet_keys:
            self.nesting_sheet_label.setText("Nincs megjeleníthető lap.")
            self.nesting_prev_button.setEnabled(False)
            self.nesting_next_button.setEnabled(False)
            return

        material_id, sheet_number = self._sheet_keys[self._current_sheet_index]
        nest = next(n for n in self._nests if n.material_id == material_id)
        material = next(
            m for m in self._material_definitions if m.material_id == material_id
        )

        sheet_rect = QRectF(
            0.0,
            -material.sheet_height_mm,
            material.sheet_width_mm,
            material.sheet_height_mm,
        )
        background_item = self._nesting_scene.addRect(
            sheet_rect,
            QPen(_PREVIEW_SHEET_BORDER_COLOR),
            QBrush(_PREVIEW_SHEET_BACKGROUND_COLOR),
        )
        background_item.setZValue(-1.0)

        # `setWidthF(0.0)` — kozmetikai (mindig 1px vékony) toll, a
        # nagyítástól függetlenül, hogy a kontúrok minden zoom-szinten
        # jól láthatók, de ne torzítsák a geometria méretarányát.
        cut_pen = QPen(_PREVIEW_CUT_COLOR)
        cut_pen.setWidthF(0.0)
        engrave_pen = QPen(_PREVIEW_ENGRAVE_COLOR)
        engrave_pen.setWidthF(0.0)

        for placed_part in nest.placed_parts:
            if placed_part.sheet_number != sheet_number:
                continue
            for contour in placed_part.contours:
                self._nesting_scene.addPath(
                    _points_to_path(contour.points, closed=True), cut_pen
                )
            for mark in placed_part.numbering_marks:
                for stroke in mark.strokes:
                    self._nesting_scene.addPath(
                        _points_to_path(stroke, closed=False), engrave_pen
                    )

        self.nesting_view.resetTransform()
        self.nesting_view.fitInView(
            self._nesting_scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio
        )
        self.nesting_view.reset_zoom_tracking()

        self.nesting_sheet_label.setText(
            f"{material_id} — {sheet_number}/{nest.sheet_count}. lap"
        )
        self.nesting_prev_button.setEnabled(self._current_sheet_index > 0)
        self.nesting_next_button.setEnabled(
            self._current_sheet_index < len(self._sheet_keys) - 1
        )
