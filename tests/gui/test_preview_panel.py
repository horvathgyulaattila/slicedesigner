"""`PreviewPanel` szeletenkénti kiemelés vezérlőelemének tesztjei (prompt
2.2 szakasz) — a `ParameterPanel`/`RunPanel` közvetlen példányosítási
mintáját követve (lásd `test_config_builder.py`), a nehezebb
`MainWindow`-fixture nélkül."""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator
from typing import cast

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
import pyvista as pv  # noqa: E402
from pytestqt.qtbot import QtBot  # noqa: E402
from pyvistaqt import QtInteractor  # noqa: E402

from slicedesigner.engines.backplate_engine import (  # noqa: E402
    Backplate,
    BackplateNormalAxis,
)
from slicedesigner.engines.dowel_engine import DowelPosition  # noqa: E402
from slicedesigner.engines.gap_engine import Spacer  # noqa: E402
from slicedesigner.engines.mesh_import import BoundingBox, Mesh  # noqa: E402
from slicedesigner.engines.slice_engine import (  # noqa: E402
    Contour,
    HoleKind,
    Slice,
    SliceAxis,
    SliceSet,
)
from slicedesigner.gui.preview_panel import PreviewPanel  # noqa: E402


def _empty_mesh() -> Mesh:
    return Mesh(
        vertices=(),
        triangles=(),
        source_path="empty.stl",
        bounding_box=BoundingBox(min=(0.0, 0.0, 0.0), max=(0.0, 0.0, 0.0)),
        is_valid=True,
        warnings=(),
    )


def _square_contour(cx: float, cy: float, half: float) -> Contour:
    return Contour(
        points=(
            (cx - half, cy - half),
            (cx + half, cy - half),
            (cx + half, cy + half),
            (cx - half, cy + half),
        )
    )


def _slice_set(slice_count: int, *, thickness_mm: float = 3.0) -> SliceSet:
    slices = tuple(
        Slice(
            thickness_mm=thickness_mm,
            contours=(_square_contour(cx=0.0, cy=0.0, half=10.0),),
            position_mm=(i - 0.5) * thickness_mm,
            index=i,
        )
        for i in range(1, slice_count + 1)
    )
    return SliceSet(
        source_mesh=_empty_mesh(),
        gap_mm=0.0,
        slices=slices,
        slice_count=slice_count,
        slice_axis=SliceAxis.Z,
    )


def _slice_set_with_hole(slice_count: int, *, thickness_mm: float = 3.0) -> SliceSet:
    """Ugyanaz, mint `_slice_set()`, de az 1. szelet egy Dowel Hole-
    kontúrral is kiegészül — a Dowel Hole-körvonalak `opacity`-
    kihagyásának teszteléséhez szükséges, mivel a sima `_slice_set()`
    egyetlen szeletén sincs lyuk-kontúr."""
    hole = Contour(
        points=((-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0)),
        hole_kind=HoleKind.DOWEL_THROUGH,
        depth_mm=1.0,
    )
    slices = []
    for i in range(1, slice_count + 1):
        contours: tuple[Contour, ...] = (_square_contour(cx=0.0, cy=0.0, half=10.0),)
        if i == 1:
            contours = contours + (hole,)
        slices.append(
            Slice(
                thickness_mm=thickness_mm,
                contours=contours,
                position_mm=(i - 0.5) * thickness_mm,
                index=i,
            )
        )
    return SliceSet(
        source_mesh=_empty_mesh(),
        gap_mm=0.0,
        slices=tuple(slices),
        slice_count=slice_count,
        slice_axis=SliceAxis.Z,
    )


def _dowel_position() -> DowelPosition:
    return DowelPosition(
        x_mm=0.0,
        y_mm=0.0,
        diameter_mm=4.0,
        length_mm=15.0,
        start_slice_index=1,
        end_slice_index=5,
        region_id=1,
    )


def _spacer() -> Spacer:
    return Spacer(
        shape="cylinder",
        x_mm=0.0,
        y_mm=0.0,
        diameter_mm=4.0,
        thickness_mm=1.0,
        start_slice_index=1,
        region_id=1,
    )


def _backplate() -> Backplate:
    return Backplate(
        contours=(_square_contour(cx=0.0, cy=0.0, half=5.0),),
        thickness_mm=2.0,
        common_plane_mm=0.0,
        material_reference=None,
    )


@pytest.fixture
def preview_panel(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> Iterator[PreviewPanel]:
    """A `QtInteractor` explicit `close()`-a nélkül a beépített auto-update
    időzítője egy már törölt render-kontextusra próbál renderelni egy
    későbbi teszt event-loop feldolgozásakor — ugyanaz a mintázat, mint a
    `test_main_window.py` `main_window` fixture-jében (natív összeomlás
    elkerülése).

    A tényleges VTK `add_mesh()`/`reset_camera()` (valódi geometriával,
    offscreen alatt, ezen a build-en) natív összeomlást (access violation)
    okoz — ugyanaz a dokumentált instabilitás, ami miatt `test_main_window.py`
    sosem hívja a valódi `show_sliced_assembly()`-t (mindig mockolja). Itt
    viszont pont a `PreviewPanel` belső állapot-vezénylését (spinbox
    tartomány, widget-láthatóság, kiemelés-állapot) teszteljük, nem a
    VTK-rajzolást (azt a `render_geometry.py` tiszta, Qt-független tesztjei
    már lefedik) — ezért kizárólag az `add_mesh`/`reset_camera` metódusokat
    semlegesítjük, a `show_sliced_assembly()`/`_render_sliced_assembly()`
    teljes vezérlési logikája (a `render_geometry.py`-hívásokkal együtt)
    valós marad.
    """
    panel = PreviewPanel()
    qtbot.addWidget(panel)
    # `isVisible()` a teljes ős-hierarchia láthatóságát figyelembe veszi —
    # `show()` nélkül a widget sosem "látható" ténylegesen, még akkor sem,
    # ha `setVisible(True)` már megtörtént rajta (ugyanaz a mintázat, mint
    # a `test_main_window.py` `main_window` fixture-jében).
    panel.show()
    monkeypatch.setattr(panel.plotter, "add_mesh", lambda *args, **kwargs: None)
    monkeypatch.setattr(panel.plotter, "reset_camera", lambda *args, **kwargs: None)
    yield panel
    panel.plotter.close()


def test_highlight_widget_hidden_before_any_data_loaded(
    preview_panel: PreviewPanel,
) -> None:
    assert not preview_panel._highlight_widget.isVisible()
    assert not preview_panel.highlight_checkbox.isChecked()
    assert not preview_panel.highlight_spinbox.isEnabled()


def test_show_sliced_assembly_shows_highlight_widget_and_sets_spinbox_range(
    preview_panel: PreviewPanel,
) -> None:
    preview_panel.show_sliced_assembly(_slice_set(5))

    assert preview_panel._highlight_widget.isVisible()
    assert preview_panel.highlight_spinbox.minimum() == 1
    assert preview_panel.highlight_spinbox.maximum() == 5


def test_highlight_spinbox_range_updates_on_new_slice_set(
    preview_panel: PreviewPanel,
) -> None:
    preview_panel.show_sliced_assembly(_slice_set(3))
    assert preview_panel.highlight_spinbox.maximum() == 3

    preview_panel.show_sliced_assembly(_slice_set(7))
    assert preview_panel.highlight_spinbox.maximum() == 7


def test_switching_to_mesh_view_hides_highlight_widget(
    preview_panel: PreviewPanel,
) -> None:
    preview_panel.show_sliced_assembly(_slice_set(5))
    assert preview_panel._highlight_widget.isVisible()

    preview_panel.show_mesh_radio.setChecked(True)
    assert not preview_panel._highlight_widget.isVisible()

    preview_panel.show_sliced_assembly_radio.setChecked(True)
    assert preview_panel._highlight_widget.isVisible()


def test_highlight_checkbox_toggled_enables_spinbox(
    preview_panel: PreviewPanel,
) -> None:
    preview_panel.show_sliced_assembly(_slice_set(5))
    assert not preview_panel.highlight_spinbox.isEnabled()

    preview_panel.highlight_checkbox.setChecked(True)
    assert preview_panel.highlight_spinbox.isEnabled()

    preview_panel.highlight_checkbox.setChecked(False)
    assert not preview_panel.highlight_spinbox.isEnabled()


def test_highlighted_slice_index_none_while_checkbox_unchecked(
    preview_panel: PreviewPanel,
) -> None:
    preview_panel.show_sliced_assembly(_slice_set(5))
    preview_panel.highlight_spinbox.setValue(3)

    assert preview_panel._highlighted_slice_index() is None


def test_highlighted_slice_index_matches_spinbox_once_checked(
    preview_panel: PreviewPanel,
) -> None:
    preview_panel.show_sliced_assembly(_slice_set(5))
    preview_panel.highlight_checkbox.setChecked(True)
    preview_panel.highlight_spinbox.setValue(3)

    assert preview_panel._highlighted_slice_index() == 3


def test_checking_highlight_renders_without_error(preview_panel: PreviewPanel) -> None:
    preview_panel.show_sliced_assembly(_slice_set(5))

    preview_panel.highlight_checkbox.setChecked(True)
    preview_panel.highlight_spinbox.setValue(3)
    preview_panel.highlight_spinbox.setValue(5)
    preview_panel.highlight_checkbox.setChecked(False)


def _record_add_mesh_calls(
    preview_panel: PreviewPanel, monkeypatch: pytest.MonkeyPatch
) -> list[tuple[tuple[object, ...], dict[str, object]]]:
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []
    monkeypatch.setattr(
        preview_panel.plotter,
        "add_mesh",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )
    return calls


def _group_calls_by_color(
    calls: list[tuple[tuple[object, ...], dict[str, object]]],
) -> dict[object, list[dict[str, object]]]:
    """`add_mesh`-hívások csoportosítása `color` szerint.

    A `_add_solid_with_edges()` bevezetése óta a "dimgray" szín TÖBBSZÖR
    is előfordulhat (minden test/kontúr-pár saját él-réteget kap) —
    ezért listát gyűjtünk színenként, nem egyetlen `kwargs`-ot (ami a
    duplikátumok közül csak az utolsót őrizné meg)."""
    grouped: dict[object, list[dict[str, object]]] = {}
    for _args, kwargs in calls:
        grouped.setdefault(kwargs["color"], []).append(kwargs)
    return grouped


def test_no_highlight_layers_are_fully_opaque_with_base_colors(
    preview_panel: PreviewPanel, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _record_add_mesh_calls(preview_panel, monkeypatch)

    preview_panel.show_sliced_assembly(
        _slice_set_with_hole(5),
        dowel_positions=(_dowel_position(),),
        spacers=(_spacer(),),
        backplate=_backplate(),
        backplate_normal_axis=BackplateNormalAxis.PLUS_X,
    )

    grouped = _group_calls_by_color(calls)
    assert grouped.keys() == {
        "lightgray",
        "dimgray",
        "red",
        "black",
        "blue",
        "green",
        "orangered",
        "mediumseagreen",
        "royalblue",
        "gainsboro",
    }

    # A test réteg sosem kap `show_edges`/`edge_color`-t — a valódi
    # kontúrélek külön "dimgray" rétegként érkeznek
    # (`_add_solid_with_edges()`).
    base_kwargs = grouped["lightgray"][0]
    assert "show_edges" not in base_kwargs
    assert "edge_color" not in base_kwargs
    assert base_kwargs["opacity"] == 1.0

    # Egyetlen "dimgray" él-réteg: az alap-összeállításé, ugyanazzal az
    # opacity-vel, mint a hozzá tartozó test.
    assert len(grouped["dimgray"]) == 1
    assert grouped["dimgray"][0]["opacity"] == 1.0

    assert grouped["red"][0]["opacity"] == 1.0
    assert grouped["blue"][0]["opacity"] == 1.0
    assert grouped["green"][0]["opacity"] == 1.0

    # A Dowel Hole-körvonalak sosem kapnak `opacity`-átadást — mindig
    # teljesen átlátszatlanok.
    assert "opacity" not in grouped["black"][0]


def test_origin_gizmo_layers_added_when_showing_mesh(
    preview_panel: PreviewPanel, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Az origó-jelölő (tengelynyilak + halvány XY-sík) az "Eredeti Mesh"
    nézetben (`show_mesh()`) is megjelenik."""
    calls = _record_add_mesh_calls(preview_panel, monkeypatch)

    preview_panel.show_mesh(_empty_mesh())

    grouped = _group_calls_by_color(calls)
    assert {"orangered", "mediumseagreen", "royalblue", "gainsboro"} <= grouped.keys()


def test_origin_gizmo_layers_added_when_showing_sliced_assembly(
    preview_panel: PreviewPanel, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Az origó-jelölő a "Szeletelt összeállítás" nézetben
    (`show_sliced_assembly()`) is megjelenik."""
    calls = _record_add_mesh_calls(preview_panel, monkeypatch)

    preview_panel.show_sliced_assembly(_slice_set(5))

    grouped = _group_calls_by_color(calls)
    assert {"orangered", "mediumseagreen", "royalblue", "gainsboro"} <= grouped.keys()


def test_highlight_dims_other_layers_keeps_highlight_and_holes_opaque(
    preview_panel: PreviewPanel, monkeypatch: pytest.MonkeyPatch
) -> None:
    preview_panel.show_sliced_assembly(
        _slice_set_with_hole(5),
        dowel_positions=(_dowel_position(),),
        spacers=(_spacer(),),
        backplate=_backplate(),
        backplate_normal_axis=BackplateNormalAxis.PLUS_X,
    )
    preview_panel.highlight_spinbox.setValue(3)

    calls = _record_add_mesh_calls(preview_panel, monkeypatch)
    preview_panel.highlight_checkbox.setChecked(True)

    grouped = _group_calls_by_color(calls)
    assert grouped.keys() == {
        "lightgray",
        "navy",
        "dimgray",
        "red",
        "black",
        "blue",
        "green",
        "orangered",
        "mediumseagreen",
        "royalblue",
        "gainsboro",
    }

    base_kwargs = grouped["lightgray"][0]
    assert "show_edges" not in base_kwargs
    assert base_kwargs["opacity"] == 0.15

    highlight_kwargs = grouped["navy"][0]
    assert "show_edges" not in highlight_kwargs
    assert highlight_kwargs["opacity"] == 1.0

    # Két külön "dimgray" él-réteg: az elhalványuló alap-összeállításé
    # (0.15) és a mindig teljesen átlátszatlan kiemelt szeleté (1.0) —
    # mindkettő a hozzá tartozó test opacity-jét követi.
    assert len(grouped["dimgray"]) == 2
    dimgray_opacities = sorted(
        cast(float, kwargs["opacity"]) for kwargs in grouped["dimgray"]
    )
    assert dimgray_opacities == [0.15, 1.0]

    assert grouped["red"][0]["opacity"] == 0.15
    assert grouped["blue"][0]["opacity"] == 0.15
    assert grouped["green"][0]["opacity"] == 0.15

    # A Dowel Hole-körvonalak kiemeléskor sem kapnak `opacity`-átadást.
    assert "opacity" not in grouped["black"][0]


def _hand_built_triangulated_cube() -> pv.PolyData:
    """Kézzel épített, 12 háromszögből (6 lap x 2 diagonálisan felezett
    háromszög) álló egységkocka — ugyanaz a fajta háromszögesített
    geometria, mint amit a `render_geometry.py` `_extrude_contour()`
    (`triangulate()` + `extrude(capping=True)`) is előállít."""
    points = [
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (1.0, 1.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
        (1.0, 0.0, 1.0),
        (1.0, 1.0, 1.0),
        (0.0, 1.0, 1.0),
    ]
    triangles = [
        (0, 2, 1),
        (0, 3, 2),  # alsó lap (z=0)
        (4, 5, 6),
        (4, 6, 7),  # felső lap (z=1)
        (0, 1, 5),
        (0, 5, 4),  # elülső lap (y=0)
        (3, 7, 6),
        (3, 6, 2),  # hátsó lap (y=1)
        (0, 4, 7),
        (0, 7, 3),  # bal lap (x=0)
        (1, 2, 6),
        (1, 6, 5),  # jobb lap (x=1)
    ]
    faces = []
    for a, b, c in triangles:
        faces.extend([3, a, b, c])
    cleaned: pv.PolyData = pv.PolyData(points, faces=faces).clean()
    return cleaned


def test_extract_feature_edges_keeps_real_edges_excludes_diagonals() -> None:
    """A prompt 2.1 szakaszának empirikus ellenőrzése: a `PreviewPanel.
    _add_solid_with_edges()`-ben ténylegesen használt
    `extract_feature_edges()`-paraméterezés egy kézzel épített,
    háromszögesített kockán a 12 valódi élt adja vissza, a 6 (lapokénti
    1-1) háromszögesítési diagonálist nem."""
    cube = _hand_built_triangulated_cube()
    assert cube.n_cells == 12  # 6 lap x 2 háromszög

    # Ugyanaz a `extract_all_edges()` referencia igazolja, hogy a
    # háromszögesített kockának ténylegesen 18 egyedi éle van (12 valódi
    # + 6 diagonális) — enélkül a lenti 12-es eredmény nem lenne
    # önmagában bizonyító erejű (elvileg triviálisan is kijöhetne, ha a
    # geometria maga hibás lenne).
    assert cube.extract_all_edges().n_lines == 18

    edges = cube.extract_feature_edges(
        feature_angle=30,
        boundary_edges=True,
        non_manifold_edges=True,
        feature_edges=True,
        manifold_edges=False,
    )

    assert edges.n_lines == 12


def test_enable_depth_peeling_called_with_number_of_peels_zero(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`number_of_peels=0` — a PyVista/VTK-ban "nincs felső korlát"-ot
    jelent (lásd `PreviewPanel.__init__()`); a PyVista-alapértelmezett
    `number_of_peels=4` élő teszteléskor nem bizonyult elégnek 4-nél
    több szeletet tartalmazó összeállításoknál."""
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []
    original = QtInteractor.enable_depth_peeling

    def _spy(self: QtInteractor, *args: object, **kwargs: object) -> object:
        calls.append((args, kwargs))
        return original(self, *args, **kwargs)

    monkeypatch.setattr(QtInteractor, "enable_depth_peeling", _spy)

    panel = PreviewPanel()
    qtbot.addWidget(panel)
    panel.show()

    assert len(calls) == 1
    _args, kwargs = calls[0]
    assert kwargs == {"number_of_peels": 0}

    panel.plotter.close()


def test_enable_depth_peeling_failure_does_not_prevent_panel_construction(
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A `PreviewPanel.__init__()`-ben az `enable_depth_peeling()` hívás
    védett — egy hibázó (pl. offscreen/szoftveres OpenGL alatt nem
    támogatott) hívás sem akadályozza a panel felépülését, csak
    naplózásra kerül."""

    def _raise(*args: object, **kwargs: object) -> None:
        raise RuntimeError("depth peeling not supported on this backend")

    monkeypatch.setattr(QtInteractor, "enable_depth_peeling", _raise)

    with caplog.at_level(logging.WARNING):
        panel = PreviewPanel()
    qtbot.addWidget(panel)
    panel.show()

    assert any(
        "enable_depth_peeling" in record.getMessage() for record in caplog.records
    )

    panel.plotter.close()
