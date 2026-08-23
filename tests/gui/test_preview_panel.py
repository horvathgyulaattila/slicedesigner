"""`PreviewPanel` szeletenkénti kiemelés vezérlőelemének tesztjei (prompt
2.2 szakasz) — a `ParameterPanel`/`RunPanel` közvetlen példányosítási
mintáját követve (lásd `test_config_builder.py`), a nehezebb
`MainWindow`-fixture nélkül."""

from __future__ import annotations

import logging
import os
import threading
from collections.abc import Iterator

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
from slicedesigner.engines.nesting_engine import (  # noqa: E402
    MaterialDefinition,
    Nest,
    PartKind,
    PartReference,
    PlacedPart,
)
from slicedesigner.engines.slice_engine import (  # noqa: E402
    Contour,
    EngravingMark,
    HoleKind,
    Slice,
    SliceAxis,
    SliceSet,
)
from slicedesigner.gui import preview_panel as preview_panel_module  # noqa: E402
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


def _material_definition(
    material_id: str, *, width_mm: float = 100.0, height_mm: float = 50.0
) -> MaterialDefinition:
    return MaterialDefinition(
        material_id=material_id,
        thickness_mm=3.0,
        sheet_width_mm=width_mm,
        sheet_height_mm=height_mm,
        kerf_mm=0.1,
    )


def _placed_part(sheet_number: int) -> PlacedPart:
    return PlacedPart(
        reference=PartReference(
            kind=PartKind.SLICE_ISLAND, slice_index=1, island_index=0
        ),
        sheet_number=sheet_number,
        position=(0.0, 0.0),
        rotation_deg=0.0,
        contours=(_square_contour(cx=5.0, cy=5.0, half=2.0),),
        numbering_marks=(
            EngravingMark(
                text="1",
                strokes=(((0.0, 0.0), (1.0, 1.0)),),
                height_mm=5.0,
                island_index=0,
            ),
        ),
    )


def _nest(material_id: str, sheet_count: int) -> Nest:
    return Nest(
        material_id=material_id,
        sheet_count=sheet_count,
        placed_parts=tuple(_placed_part(n) for n in range(1, sheet_count + 1)),
        seams=(),
    )


def _show_sliced_assembly_sync(
    qtbot: QtBot, panel: PreviewPanel, *args: object, **kwargs: object
) -> None:
    """`show_sliced_assembly()` hívása, és szinkron megvárása a
    háttérszálas geometria-építés/renderelés befejezéséig (ADR-0011).

    A `show_sliced_assembly()` a widget-állapotot (tárolt referenciák,
    spinbox-tartomány, láthatóság) szinkron frissíti, de a tényleges
    `plotter`-hívásokat (`add_mesh`/`reset_camera`) egy háttérszál
    befejezésére kötött, queued slotban végzi el — enélkül a
    `qtbot.waitSignal` nélkül a tesztek vagy determinisztikusan hibás
    (üres) renderelési eredményt látnának, vagy — rosszabb esetben — egy,
    a teszt végeztével még futó/befejezetlen háttérszálat hagynának
    hátra, ami a KÖVETKEZŐ teszt lefutását is megzavarhatja (l. a
    `preview_panel` fixture docstringjét a VTK/offscreen instabilitásról).
    """
    with qtbot.waitSignal(panel.assembly_render_succeeded, timeout=5000):
        panel.show_sliced_assembly(*args, **kwargs)


def _wait_for_interactive_render(qtbot: QtBot, panel: PreviewPanel) -> None:
    """A kiemelés-/nézet-váltás eredetű (interaktív) async render
    befejezésének szinkron megvárása (ADR-0012).

    Az interaktív render — a Futtatás utáni renderrel ellentétben —
    SOSEM emittálja az `assembly_render_succeeded`/`assembly_render_failed`
    jelzéseket (ez maga a legfontosabb korlát, l. a modul docstringjét),
    ezért `qtbot.waitSignal` itt nem használható; a `_preview_worker`
    nullázódását kell megvárni. Csak EGYETLEN, egymással nem átfedő
    interaktív render megvárására alkalmas — több, gyorsan egymást követő
    render esetén (amikor a korábbiak elavulttá válhatnak, és emiatt
    sosem törlik a `_preview_worker`-referenciát) az
    `_install_ready_call_counter()`-rel számolt hívásszámra várakozás a
    helyes minta."""
    qtbot.waitUntil(lambda: panel._preview_worker is None, timeout=5000)


def _install_render_call_recorder(monkeypatch: pytest.MonkeyPatch) -> list[object]:
    """`PreviewPanel._render_geometry_bundle()` tényleges hívásainak (a
    ténylegesen renderelt köteg-objektumoknak) rögzítése — a metódus
    valós viselkedése (a monkeypatchelt `add_mesh`-en keresztüli
    "renderelés") is lefut, csak a hívás emellett fel is jegyzésre kerül.
    """
    calls: list[object] = []
    original = PreviewPanel._render_geometry_bundle

    def _recording(self: PreviewPanel, bundle: object) -> None:
        calls.append(bundle)
        original(self, bundle)

    monkeypatch.setattr(PreviewPanel, "_render_geometry_bundle", _recording)
    return calls


def _install_ready_call_counter(monkeypatch: pytest.MonkeyPatch) -> list[None]:
    """`PreviewPanel._on_preview_geometry_ready()` hívásainak számlálása —
    determinisztikus várakozási feltételként használható arra, hogy egy
    (akár elavultként csendben eldobott) worker eredménye ténylegesen
    feldolgozásra került-e a fő szálon — enélkül nem lenne mód
    `time.sleep()` nélkül megvárni egy olyan worker befejezését, amelynek
    NINCS megfigyelhető (renderelési vagy jelzés-) mellékhatása."""
    counter: list[None] = []
    original = PreviewPanel._on_preview_geometry_ready

    def _counting(self: PreviewPanel, outcome: object) -> None:
        original(self, outcome)
        counter.append(None)

    monkeypatch.setattr(PreviewPanel, "_on_preview_geometry_ready", _counting)
    return counter


def _install_blocking_build_on_first_call(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[threading.Event, threading.Event]:
    """A modul-szintű `_build_sliced_assembly_geometry()` ELSŐ (az
    installálás UTÁN induló) hívását a háttérszálon blokkolja, amíg a
    teszt explicit fel nem oldja — determinisztikus (`threading.Event`-
    alapú, nem `time.sleep()`) végrehajtási sorrend biztosításához két,
    egymást gyorsan követő async-render között (CODING_STANDARDS 4.
    szakasz).

    Returns:
        `(entered, may_proceed)` — `entered` akkor íródik, amikor az
        első hívás ténylegesen blokkolni kezdett (a teszt ezt várja meg,
        mielőtt a MÁSODIK rendert elindítaná); `may_proceed`-et a teszt
        állítja be, hogy az első hívás folytatódhasson.
    """
    entered = threading.Event()
    may_proceed = threading.Event()
    call_count = 0
    original = preview_panel_module._build_sliced_assembly_geometry

    def _blocking(*args: object, **kwargs: object) -> object:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            entered.set()
            assert may_proceed.wait(timeout=5.0)
        return original(*args, **kwargs)

    monkeypatch.setattr(
        preview_panel_module, "_build_sliced_assembly_geometry", _blocking
    )
    return entered, may_proceed


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
    semlegesítjük, a `show_sliced_assembly()`/kiemelés-/nézet-váltás
    teljes vezérlési logikája (a `render_geometry.py`-hívásokkal együtt,
    valódi háttérszálon, ADR-0011/ADR-0012) valós marad.
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
    preview_panel: PreviewPanel, qtbot: QtBot
) -> None:
    _show_sliced_assembly_sync(qtbot, preview_panel, _slice_set(5))

    assert preview_panel._highlight_widget.isVisible()
    assert preview_panel.highlight_spinbox.minimum() == 1
    assert preview_panel.highlight_spinbox.maximum() == 5


def test_highlight_spinbox_range_updates_on_new_slice_set(
    preview_panel: PreviewPanel, qtbot: QtBot
) -> None:
    _show_sliced_assembly_sync(qtbot, preview_panel, _slice_set(3))
    assert preview_panel.highlight_spinbox.maximum() == 3

    _show_sliced_assembly_sync(qtbot, preview_panel, _slice_set(7))
    assert preview_panel.highlight_spinbox.maximum() == 7


def test_switching_to_mesh_view_hides_highlight_widget(
    preview_panel: PreviewPanel, qtbot: QtBot
) -> None:
    _show_sliced_assembly_sync(qtbot, preview_panel, _slice_set(5))
    assert preview_panel._highlight_widget.isVisible()

    preview_panel.show_mesh_radio.setChecked(True)
    assert not preview_panel._highlight_widget.isVisible()

    preview_panel.show_sliced_assembly_radio.setChecked(True)
    assert preview_panel._highlight_widget.isVisible()
    _wait_for_interactive_render(qtbot, preview_panel)


def test_highlight_checkbox_toggled_enables_spinbox(
    preview_panel: PreviewPanel, monkeypatch: pytest.MonkeyPatch, qtbot: QtBot
) -> None:
    _show_sliced_assembly_sync(qtbot, preview_panel, _slice_set(5))
    ready_calls = _install_ready_call_counter(monkeypatch)
    assert not preview_panel.highlight_spinbox.isEnabled()

    preview_panel.highlight_checkbox.setChecked(True)
    assert preview_panel.highlight_spinbox.isEnabled()

    preview_panel.highlight_checkbox.setChecked(False)
    assert not preview_panel.highlight_spinbox.isEnabled()

    # Két, gyorsan egymást követő interaktív render indult (checkbox be,
    # majd ki) — mindkettő teljes feldolgozását (renderelést vagy
    # elavultkénti csendes eldobást) megvárjuk, hogy ne maradjon
    # befejezetlen háttérszál a teszt végeztével.
    qtbot.waitUntil(lambda: len(ready_calls) == 2, timeout=5000)


def test_highlighted_slice_index_none_while_checkbox_unchecked(
    preview_panel: PreviewPanel, qtbot: QtBot
) -> None:
    _show_sliced_assembly_sync(qtbot, preview_panel, _slice_set(5))
    preview_panel.highlight_spinbox.setValue(3)

    assert preview_panel._highlighted_slice_index() is None
    _wait_for_interactive_render(qtbot, preview_panel)


def test_highlighted_slice_index_matches_spinbox_once_checked(
    preview_panel: PreviewPanel, monkeypatch: pytest.MonkeyPatch, qtbot: QtBot
) -> None:
    _show_sliced_assembly_sync(qtbot, preview_panel, _slice_set(5))
    ready_calls = _install_ready_call_counter(monkeypatch)

    preview_panel.highlight_checkbox.setChecked(True)
    preview_panel.highlight_spinbox.setValue(3)

    assert preview_panel._highlighted_slice_index() == 3
    qtbot.waitUntil(lambda: len(ready_calls) == 2, timeout=5000)


def test_checking_highlight_renders_without_error(
    preview_panel: PreviewPanel, monkeypatch: pytest.MonkeyPatch, qtbot: QtBot
) -> None:
    _show_sliced_assembly_sync(qtbot, preview_panel, _slice_set(5))
    ready_calls = _install_ready_call_counter(monkeypatch)

    preview_panel.highlight_checkbox.setChecked(True)
    preview_panel.highlight_spinbox.setValue(3)
    preview_panel.highlight_spinbox.setValue(5)
    preview_panel.highlight_checkbox.setChecked(False)

    qtbot.waitUntil(lambda: len(ready_calls) == 4, timeout=5000)


def test_show_sliced_assembly_defers_render_to_background_worker(
    preview_panel: PreviewPanel, monkeypatch: pytest.MonkeyPatch, qtbot: QtBot
) -> None:
    """ADR-0011: a Futtatás utáni első megjelenítéskor a geometria-építés/
    renderelés egy külön háttérszálra (`_PreviewComputeWorker`) kerül,
    nem a hívó szálon, szinkron történik.

    Determinisztikus (nem időzítés-függő, CODING_STANDARDS 4. szakasz)
    bizonyíték: a `with qtbot.waitSignal(...)` blokkon BELÜL, közvetlenül
    a `show_sliced_assembly()` visszatérése után — még mielőtt bármilyen
    várakozás/eseményhurok-feldolgozás történne — a
    `preview_panel._preview_worker` már nem `None` (a worker-objektum
    szinkron, a hívás részeként jön létre és indul el, l.
    `_start_async_sliced_assembly_render()`), miközben a `plotter.add_mesh()`
    MÉG NEM futott le. Csak a jelzés (a háttérszál tényleges befejezése)
    UTÁN nullázódik a worker-referencia és jelennek meg az `add_mesh`-hívások."""
    calls = _record_add_mesh_calls(preview_panel, monkeypatch)
    assert preview_panel._preview_worker is None

    with qtbot.waitSignal(preview_panel.assembly_render_succeeded, timeout=5000):
        preview_panel.show_sliced_assembly(_slice_set(5))
        assert preview_panel._preview_worker is not None
        assert calls == []

    assert preview_panel._preview_worker is None
    assert len(calls) > 0


def test_interactive_render_never_emits_public_signals(
    preview_panel: PreviewPanel, monkeypatch: pytest.MonkeyPatch, qtbot: QtBot
) -> None:
    """ADR-0012 legfontosabb korlátja: a kiemelés-/nézet-váltás eredetű
    (interaktív) renderek SOSEM emittálják a publikus
    `assembly_render_succeeded`/`assembly_render_failed` jelzéseket — a
    `MainWindow` ezekről nem szerezhet (és nem is kell, hogy szerezzen)
    tudomást. Kiemelés be-/kikapcsolás, spinbox-érték-változás ÉS
    "Eredeti Mesh" → "Szeletelt összeállítás" nézet-váltás is szerepel."""
    _show_sliced_assembly_sync(qtbot, preview_panel, _slice_set(5))
    ready_calls = _install_ready_call_counter(monkeypatch)

    succeeded_events: list[None] = []
    preview_panel.assembly_render_succeeded.connect(
        lambda: succeeded_events.append(None)
    )
    failed_events: list[Exception] = []
    preview_panel.assembly_render_failed.connect(failed_events.append)

    preview_panel.highlight_checkbox.setChecked(True)
    preview_panel.highlight_spinbox.setValue(3)
    preview_panel.show_mesh_radio.setChecked(True)
    preview_panel.show_sliced_assembly_radio.setChecked(True)

    # A négy widget-interakció közül három indít interaktív rendert (a
    # "Eredeti Mesh"-re váltás szinkron `_render_mesh()`-t hív, nem
    # async-t) — mindhármat megvárjuk, mielőtt a jelzéseket ellenőriznénk.
    qtbot.waitUntil(lambda: len(ready_calls) == 3, timeout=5000)

    assert succeeded_events == []
    assert failed_events == []


def test_stale_interactive_render_discarded_when_newer_completes_first(
    preview_panel: PreviewPanel, monkeypatch: pytest.MonkeyPatch, qtbot: QtBot
) -> None:
    """ADR-0012: ha egy korábban induló kiemelés-váltás eredetű render
    KÉSŐBB fejeződik be, mint egy közben elindult, frissebb interaktív
    render, a korábbi eredménye csendben eldobásra kerül — sosem jut el
    a plotterig.

    Determinisztikus (`threading.Event`-alapú, CODING_STANDARDS 4.
    szakasz) végrehajtási sorrend: az ELSŐ (korábban induló) worker
    geometria-építése a háttérszálon blokkolva marad, amíg a teszt
    explicit fel nem oldja — ezalatt a MÁSODIK (frissebb) worker
    teljesen lefut és renderel. Csak EZUTÁN engedjük tovább az elsőt —
    a `_render_geometry_bundle()` hívásszáma igazolja, hogy a later
    érkező, elavult eredmény sosem jutott el a rendereléshez.
    """
    _show_sliced_assembly_sync(qtbot, preview_panel, _slice_set(5))

    # A checkbox bekapcsolása önmagában is indítana egy rendert — ezt itt,
    # a blokkoló intercept beállítása ELŐTT, kivárva végezzük el, hogy a
    # lenti hívásszámlálás egyértelműen csak a két, ténylegesen vizsgált
    # workerre vonatkozzon.
    preview_panel.highlight_checkbox.setChecked(True)
    _wait_for_interactive_render(qtbot, preview_panel)

    render_calls = _install_render_call_recorder(monkeypatch)
    ready_calls = _install_ready_call_counter(monkeypatch)
    entered, may_proceed = _install_blocking_build_on_first_call(monkeypatch)

    preview_panel.highlight_spinbox.setValue(2)  # korábban induló worker (blokkolva)
    assert entered.wait(timeout=5.0)

    preview_panel.highlight_spinbox.setValue(4)  # később induló, frissebb worker
    qtbot.waitUntil(lambda: len(ready_calls) == 1, timeout=5000)
    assert len(render_calls) == 1  # csak a frissebb jutott el a renderelésig

    may_proceed.set()  # a korábban induló (elavult) worker most fejeződik be
    qtbot.waitUntil(lambda: len(ready_calls) == 2, timeout=5000)

    # Az elavult eredmény SOSEM jutott el a rendereléshez.
    assert len(render_calls) == 1


def test_stale_interactive_render_does_not_override_or_signal_after_new_run(
    preview_panel: PreviewPanel, monkeypatch: pytest.MonkeyPatch, qtbot: QtBot
) -> None:
    """A PROMPT_2026-08-09_interactive-preview-render-background-thread.md
    1. szakaszának korrektségi kockázata: ha egy korábban elindult,
    kiemelés-váltás eredetű worker egy KÖZBEN elindult, Futtatás-eredetű
    (post-run) render UTÁN fejeződik be, az utóbbi eredményét nem írhatja
    felül a plotteren, és nem válthatja ki a `MainWindow`-t érintő
    publikus `assembly_render_succeeded`/`assembly_render_failed`
    jelzéseket sem (ADR-0012) — a kiemelés-/nézet-váltás eredetű workerek
    SOSEM emittálják ezeket a jelzéseket, függetlenül a befejezés
    időpontjától.
    """
    _show_sliced_assembly_sync(qtbot, preview_panel, _slice_set(5))

    succeeded_events: list[None] = []
    preview_panel.assembly_render_succeeded.connect(
        lambda: succeeded_events.append(None)
    )
    failed_events: list[Exception] = []
    preview_panel.assembly_render_failed.connect(failed_events.append)

    render_calls = _install_render_call_recorder(monkeypatch)
    ready_calls = _install_ready_call_counter(monkeypatch)
    entered, may_proceed = _install_blocking_build_on_first_call(monkeypatch)

    # 1) Interaktív (kiemelés-váltás) worker indítása — a háttérszálon
    # blokkolva marad.
    preview_panel.highlight_checkbox.setChecked(True)
    assert entered.wait(timeout=5.0)

    # 2) Egy ÚJ, Futtatás-eredetű render indul, MIELŐTT az interaktív
    # worker befejeződne — ez rendes, nem blokkolt módon lefut.
    _show_sliced_assembly_sync(qtbot, preview_panel, _slice_set(7))

    assert succeeded_events == [None]
    assert failed_events == []
    assert len(render_calls) == 1
    post_run_bundle = render_calls[-1]

    # 3) Az elavult interaktív worker most fejeződik be.
    may_proceed.set()
    qtbot.waitUntil(lambda: len(ready_calls) == 2, timeout=5000)

    # Az elavult eredmény SOSEM emittálta a publikus jelzéseket, és
    # SOSEM írta felül a plottert a Futtatás eredménye felett.
    assert succeeded_events == [None]
    assert failed_events == []
    assert len(render_calls) == 1
    assert render_calls[-1] is post_run_bundle


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
    preview_panel: PreviewPanel, monkeypatch: pytest.MonkeyPatch, qtbot: QtBot
) -> None:
    calls = _record_add_mesh_calls(preview_panel, monkeypatch)

    _show_sliced_assembly_sync(
        qtbot,
        preview_panel,
        _slice_set_with_hole(5),
        dowel_positions=(_dowel_position(),),
        spacers=(_spacer(),),
        backplate=_backplate(),
        backplate_normal_axis=BackplateNormalAxis.PLUS_X,
    )

    grouped = _group_calls_by_color(calls)
    assert grouped.keys() == {
        "#7E4B26",
        "#1A1719",
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
    # kontúrélek külön, "#1A1719" (RAL 8022) színű rétegként érkeznek
    # (`_add_solid_with_edges()`).
    base_kwargs = grouped["#7E4B26"][0]
    assert "show_edges" not in base_kwargs
    assert "edge_color" not in base_kwargs
    assert base_kwargs["opacity"] == 1.0

    # Egyetlen "#1A1719" él-réteg: az alap-összeállításé, ugyanazzal az
    # opacity-vel, mint a hozzá tartozó test.
    assert len(grouped["#1A1719"]) == 1
    assert grouped["#1A1719"][0]["opacity"] == 1.0

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
    preview_panel: PreviewPanel, monkeypatch: pytest.MonkeyPatch, qtbot: QtBot
) -> None:
    """Az origó-jelölő a "Szeletelt összeállítás" nézetben
    (`show_sliced_assembly()`) is megjelenik."""
    calls = _record_add_mesh_calls(preview_panel, monkeypatch)

    _show_sliced_assembly_sync(qtbot, preview_panel, _slice_set(5))

    grouped = _group_calls_by_color(calls)
    assert {"orangered", "mediumseagreen", "royalblue", "gainsboro"} <= grouped.keys()


def test_highlight_dims_other_layers_keeps_highlight_and_holes_opaque(
    preview_panel: PreviewPanel, monkeypatch: pytest.MonkeyPatch, qtbot: QtBot
) -> None:
    _show_sliced_assembly_sync(
        qtbot,
        preview_panel,
        _slice_set_with_hole(5),
        dowel_positions=(_dowel_position(),),
        spacers=(_spacer(),),
        backplate=_backplate(),
        backplate_normal_axis=BackplateNormalAxis.PLUS_X,
    )
    preview_panel.highlight_spinbox.setValue(3)
    _wait_for_interactive_render(qtbot, preview_panel)

    calls = _record_add_mesh_calls(preview_panel, monkeypatch)
    preview_panel.highlight_checkbox.setChecked(True)
    _wait_for_interactive_render(qtbot, preview_panel)

    grouped = _group_calls_by_color(calls)
    assert grouped.keys() == {
        "#7E4B26",
        "navy",
        "#1A1719",
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

    base_kwargs = grouped["#7E4B26"][0]
    assert "show_edges" not in base_kwargs
    assert base_kwargs["opacity"] == 0.15

    highlight_kwargs = grouped["navy"][0]
    assert "show_edges" not in highlight_kwargs
    assert highlight_kwargs["opacity"] == 1.0

    # Az elhalványuló alap-összeállítás éle a testéhez igazított "#1A1719"
    # (RAL 8022) színt kapja (opacity 0.15); a mindig teljesen
    # átlátszatlan kiemelt szelet éle az alapértelmezett "dimgray"-t
    # (opacity 1.0) — a `highlight_polydata` hívása nem ad át
    # `edge_color`-t.
    assert grouped["#1A1719"][0]["opacity"] == 0.15
    assert grouped["dimgray"][0]["opacity"] == 1.0

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


def test_original_mesh_uses_smooth_shading_and_specular(
    preview_panel: PreviewPanel, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A finom felületmintázatok (pl. Wave Generator relief) megfelelő
    árnyékolásához az "Eredeti Mesh" nézet (`show_mesh()`) szolid rétege
    `smooth_shading` + mérsékelt `specular` mellett kerül hozzáadásra
    (2026-08-21-i kiegészítés) — enélkül a lapos árnyékolás miatt
    gyakorlatilag csak a kontúrél-réteg volt látható finom mintázatoknál."""
    calls = _record_add_mesh_calls(preview_panel, monkeypatch)

    preview_panel.show_mesh(_empty_mesh())

    grouped = _group_calls_by_color(calls)
    base_kwargs = grouped["lightgray"][0]
    assert base_kwargs["smooth_shading"] is True
    assert base_kwargs["specular"] == 0.5
    assert base_kwargs["specular_power"] == 15


def test_sliced_assembly_does_not_use_smooth_shading(
    preview_panel: PreviewPanel, monkeypatch: pytest.MonkeyPatch, qtbot: QtBot
) -> None:
    """A "Szeletelt összeállítás" nézetben a geometria fizikailag is
    lapos, vízszintes rétegek egymásra halmozásából áll — a Phong-
    árnyalás itt nem tudna mit "elsimítani", csak a rétegek határán
    keltene, a tényleges geometriától idegen fényes csíkokat, ezért ez a
    nézet NEM kéri a `smooth_shading`-et (`_add_solid_with_edges()`
    alapértelmezése)."""
    calls = _record_add_mesh_calls(preview_panel, monkeypatch)

    _show_sliced_assembly_sync(qtbot, preview_panel, _slice_set(5))

    grouped = _group_calls_by_color(calls)
    base_kwargs = grouped["#7E4B26"][0]
    assert "smooth_shading" not in base_kwargs
    assert "specular" not in base_kwargs
    assert "specular_power" not in base_kwargs

    # A kontúrél-réteg SOSEM kap smooth_shading/specular-t — egyszerű
    # vonalgeometria, ahol ennek nincs értelme.
    edge_kwargs = grouped["#1A1719"][0]
    assert "smooth_shading" not in edge_kwargs
    assert "specular" not in edge_kwargs


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


# --- 2D export-előnézet (EXPORT_PREVIEW_SPEC.md, prompt 8. szakasz) ---


def test_show_2d_radio_initially_disabled(preview_panel: PreviewPanel) -> None:
    assert not preview_panel.show_2d_radio.isEnabled()
    assert preview_panel.show_3d_radio.isChecked()


def test_show_nests_enables_2d_radio(preview_panel: PreviewPanel) -> None:
    preview_panel.show_nests((_nest("wood", 1),), (_material_definition("wood"),))

    assert preview_panel.show_2d_radio.isEnabled()


def test_show_nests_does_not_switch_mode_while_3d_active(
    preview_panel: PreviewPanel,
) -> None:
    preview_panel.show_nests((_nest("wood", 1),), (_material_definition("wood"),))

    assert preview_panel.show_3d_radio.isChecked()
    assert not preview_panel.show_2d_radio.isChecked()


def test_show_nests_builds_deterministic_sheet_order(
    preview_panel: PreviewPanel,
) -> None:
    nests = (_nest("b_wood", 2), _nest("a_wood", 1))
    materials = (_material_definition("b_wood"), _material_definition("a_wood"))

    preview_panel.show_nests(nests, materials)

    assert preview_panel._sheet_keys == [
        ("a_wood", 1),
        ("b_wood", 1),
        ("b_wood", 2),
    ]


def test_switching_to_2d_hides_3d_widgets_and_shows_2d_widget(
    preview_panel: PreviewPanel, qtbot: QtBot
) -> None:
    _show_sliced_assembly_sync(qtbot, preview_panel, _slice_set(3))
    preview_panel.show_nests((_nest("wood", 2),), (_material_definition("wood"),))

    assert not preview_panel._nesting_2d_widget.isVisible()
    assert preview_panel._switch_widget.isVisible()

    preview_panel.show_2d_radio.setChecked(True)

    assert preview_panel._nesting_2d_widget.isVisible()
    assert not preview_panel._switch_widget.isVisible()
    assert not preview_panel._highlight_widget.isVisible()
    assert not preview_panel.plotter.isVisible()

    preview_panel.show_3d_radio.setChecked(True)

    assert not preview_panel._nesting_2d_widget.isVisible()
    assert preview_panel._switch_widget.isVisible()
    assert preview_panel.plotter.isVisible()


def test_navigation_buttons_disabled_for_single_sheet(
    preview_panel: PreviewPanel,
) -> None:
    preview_panel.show_nests((_nest("wood", 1),), (_material_definition("wood"),))
    preview_panel.show_2d_radio.setChecked(True)

    assert not preview_panel.nesting_prev_button.isEnabled()
    assert not preview_panel.nesting_next_button.isEnabled()


def test_navigation_buttons_enabled_at_boundaries_for_multiple_sheets(
    preview_panel: PreviewPanel,
) -> None:
    preview_panel.show_nests((_nest("wood", 3),), (_material_definition("wood"),))
    preview_panel.show_2d_radio.setChecked(True)

    assert not preview_panel.nesting_prev_button.isEnabled()
    assert preview_panel.nesting_next_button.isEnabled()

    preview_panel.nesting_next_button.click()
    assert preview_panel._current_sheet_index == 1
    assert preview_panel.nesting_prev_button.isEnabled()
    assert preview_panel.nesting_next_button.isEnabled()

    preview_panel.nesting_next_button.click()
    assert preview_panel._current_sheet_index == 2
    assert preview_panel.nesting_prev_button.isEnabled()
    assert not preview_panel.nesting_next_button.isEnabled()

    preview_panel.nesting_prev_button.click()
    assert preview_panel._current_sheet_index == 1
    assert preview_panel.nesting_prev_button.isEnabled()
    assert preview_panel.nesting_next_button.isEnabled()


def test_show_nests_resets_to_first_sheet_when_2d_mode_active(
    preview_panel: PreviewPanel,
) -> None:
    preview_panel.show_nests((_nest("wood", 3),), (_material_definition("wood"),))
    preview_panel.show_2d_radio.setChecked(True)
    preview_panel.nesting_next_button.click()
    assert preview_panel._current_sheet_index == 1

    preview_panel.show_nests((_nest("wood", 2),), (_material_definition("wood"),))

    assert preview_panel._current_sheet_index == 0


def test_render_current_sheet_draws_distinguishable_cut_and_engrave_paths(
    preview_panel: PreviewPanel,
) -> None:
    preview_panel.show_nests((_nest("wood", 1),), (_material_definition("wood"),))
    preview_panel.show_2d_radio.setChecked(True)

    pens = [
        item.pen()
        for item in preview_panel._nesting_scene.items()
        if hasattr(item, "pen")
    ]
    cut_pens = [
        pen for pen in pens if pen.color() == preview_panel_module._PREVIEW_CUT_COLOR
    ]
    engrave_pens = [
        pen
        for pen in pens
        if pen.color() == preview_panel_module._PREVIEW_ENGRAVE_COLOR
    ]

    assert len(cut_pens) >= 1
    assert len(engrave_pens) >= 1


def test_render_current_sheet_shows_material_and_sheet_position(
    preview_panel: PreviewPanel,
) -> None:
    preview_panel.show_nests((_nest("wood3", 2),), (_material_definition("wood3"),))
    preview_panel.show_2d_radio.setChecked(True)

    assert preview_panel.nesting_sheet_label.text() == "wood3 — 1/2. lap"

    preview_panel.nesting_next_button.click()

    assert preview_panel.nesting_sheet_label.text() == "wood3 — 2/2. lap"
