"""Fő alkalmazásablak: bal paraméter-panel, középső 3D előnézet, alsó
futtatás/export/állapot-panel (prompt 2.1 szakasz)."""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QAction, QCloseEvent
from PySide6.QtWidgets import QFileDialog, QMainWindow, QSplitter, QVBoxLayout, QWidget

from slicedesigner.engines.backplate_engine import BackplateNormalAxis
from slicedesigner.engines.exceptions import SliceDesignerError
from slicedesigner.engines.nesting_engine import Nest
from slicedesigner.gui import app_settings, config_builder, config_loader
from slicedesigner.gui.parameter_panel import ParameterPanel
from slicedesigner.gui.preview_panel import PreviewPanel
from slicedesigner.gui.run_panel import RunPanel
from slicedesigner.project import persistence
from slicedesigner.project.exceptions import PipelineConfigurationError
from slicedesigner.project.pipeline import (
    MeshImportParams,
    PipelineConfig,
    PipelineResult,
    export_pipeline_result_to_dxf,
    import_mesh_preview,
    run_pipeline,
)

logger = logging.getLogger(__name__)

_PROJECT_FILE_FILTER = "Slice Designer projekt (*.json)"


class _PipelineWorker(QThread):
    """Háttérszál: kizárólag a kész `PipelineConfig`-on hívja meg `run_pipeline()`-t.

    `QThread`-alosztály `run()`-felülírással, nem `QObject` +
    `moveToThread()` — a Qt-dokumentáció a worker-objektum + `moveToThread()`
    mintát elsősorban akkor javasolja, ha a worker-objektumnak több
    slot-ját kell a háttérszálon, queued connection-nel, ismételten
    meghívni. Ez a worker egyetlen, blokkoló hívást (`run_pipeline()`)
    végez el egyszer, `self`-en nincs a háttérszálon meghívandó külön
    slot — csak a felülírt `run()` fut ott, a `succeeded`/`failed` jelzés
    pedig a szokásos Qt-mód szerint (a fogadó — `MainWindow` — szálán,
    queued connection-nel) jut el a GUI-hoz. Ezért itt az egyszerűbb
    `QThread`-alosztályozás is biztonságos és megfelelő; minden
    futtatáshoz új példány készül (nem hívjuk újra ugyanazt a worker-t).

    `run()` szigorúan **nem** ér hozzá semmilyen widget-hez — kizárólag a
    `run_pipeline()` hívása és a kivétel elkapása történik itt; minden
    GUI-frissítés a `succeeded`/`failed` jelzésekre kötött, a fő szálon
    futó `MainWindow`-slotokban zajlik.
    """

    succeeded = Signal(object)
    failed = Signal(object)

    def __init__(self, config: PipelineConfig, parent: QObject | None = None) -> None:
        super().__init__(parent)
        # Publikus (nem csak a `run()` belsejéhez szükséges) — a sikeres
        # futás után a `MainWindow` ebből olvassa ki a
        # `backplate_normal_axis`-t (a `PipelineResult` maga nem
        # tartalmazza, lásd `_on_pipeline_succeeded()`).
        self.config = config

    def run(self) -> None:
        try:
            result = run_pipeline(self.config)
        except SliceDesignerError as error:
            self.failed.emit(error)
        else:
            self.succeeded.emit(result)


class MainWindow(QMainWindow):
    """A Slice Designer fő ablaka.

    A bal paraméter-panel három kapcsolója a Dowel/Gap/Backplate
    csoportok show/hide állapotát vezérli; a "Futtatás" gomb a
    `config_builder.build_pipeline_config()` + `run_pipeline()` teljes
    végrehajtási útvonalat indítja (ROADMAP Phase 5, "teljes workflow"
    1. rész).
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Slice Designer")
        self._worker: _PipelineWorker | None = None
        # A legutóbbi sikeres Futtatás Nest-jei — a "DXF Export" gomb
        # (ADR-0009) ezeket exportálja; új Futtatás indításakor `None`-ra
        # áll vissza, és a gomb újra letiltásra kerül.
        self._last_nests: tuple[Nest, ...] | None = None

        self.parameter_panel = ParameterPanel(self)
        self.preview_panel = PreviewPanel(self)
        self.run_panel = RunPanel(self)
        self.run_panel.run_button.clicked.connect(self._on_run_clicked)
        self.run_panel.export_dxf_button.clicked.connect(self._on_export_dxf_clicked)
        self.parameter_panel.mesh_file_selected.connect(self._on_mesh_file_selected)
        # A 3D-előnézet geometria-építése a Futtatás utáni első
        # megjelenítéskor háttérszálon fut (ADR-0011) — a Futtatás-állapot
        # (gomb/menü/folyamatjelző) lezárása (`_finish_run()`) ezért csak
        # ENNEK befejezésekor történik, nem közvetlenül a pipeline-számítás
        # végén (l. `_on_pipeline_succeeded()`).
        self.preview_panel.assembly_render_succeeded.connect(self._finish_run)
        self.preview_panel.assembly_render_failed.connect(
            self._on_preview_render_failed
        )
        self._build_menu_bar()

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(self.parameter_panel)
        splitter.addWidget(self.preview_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        central_widget = QWidget(self)
        central_layout = QVBoxLayout(central_widget)
        central_layout.addWidget(splitter)
        central_layout.addWidget(self.run_panel)

        self.setCentralWidget(central_widget)
        logger.debug("MainWindow felépítve.")

        app_settings.load_startup_config(self.parameter_panel, self.run_panel)

    def closeEvent(self, event: QCloseEvent) -> None:
        """A jelenlegi widget-állapot mentése alkalmazás-szintű
        alapértelmezésként, bezárás előtt.

        Amíg a Futtatás folyamatban van — a pipeline háttérszála (`self._worker`)
        VAGY az azt követő, a 3D-előnézet geometria-építését végző
        háttérszál (`PreviewPanel._preview_worker`, ADR-0011) fut —, a
        bezárás elutasításra kerül (`event.ignore()`): egyiknek sincs
        megszakítási pontja, egy futó szál mellett bezárt ablak esetén a
        szál widget-hozzáférés nélkül, de befejezetlenül maradna hátra.
        `self._worker` a `_finish_run()`-ig (amit a 3D-előnézet befejezése
        indít el, l. `__init__`) nem `None`, ezért ez az egyetlen
        ellenőrzés mindkét szakaszt lefedi.

        Ha a szál nem fut, a mentés kimenetelétől függetlenül mindig
        engedélyezi a bezárást (`app_settings.save_current_config()` sosem
        dob kivételt).
        """
        if self._worker is not None:
            self.run_panel.status_log.append(
                "Futtatás folyamatban — kérem várja meg, amíg befejeződik, "
                "mielőtt bezárja az alkalmazást."
            )
            event.ignore()
            return
        app_settings.save_current_config(self.parameter_panel, self.run_panel)
        super().closeEvent(event)

    def _build_menu_bar(self) -> None:
        file_menu = self.menuBar().addMenu("Fájl")

        self._save_action = QAction("Projekt mentése...", self)
        self._save_action.triggered.connect(self._on_save_project_clicked)
        file_menu.addAction(self._save_action)

        self._open_action = QAction("Projekt megnyitása...", self)
        self._open_action.triggered.connect(self._on_open_project_clicked)
        file_menu.addAction(self._open_action)

    def _on_save_project_clicked(self) -> None:
        """A jelenlegi (akár részleges) widget-állapot mentése projektfájlba.

        A `build_pipeline_config()` `require_complete=False` mellett hívva
        — a mesh-fájl/kimeneti könyvtár "nincs kiválasztva" ellenőrzése
        itt nem fut, hogy részleges állapot is menthető legyen.
        """
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Projekt mentése", "", _PROJECT_FILE_FILTER
        )
        if not file_path:
            return

        try:
            config = config_builder.build_pipeline_config(
                self.parameter_panel, self.run_panel, require_complete=False
            )
            persistence.save_project_config(config, file_path)
        except PipelineConfigurationError as error:
            logger.warning("Projektmentési konfigurációs hiba: %s", error)
            self.run_panel.status_log.append(f"Konfigurációs hiba: {error}")
        except SliceDesignerError as error:
            logger.exception("Hiba a projekt mentése során.")
            self.run_panel.status_log.append(f"Hiba a mentés során: {error}")
        else:
            self.run_panel.status_log.append("Projekt elmentve.")

    def _on_open_project_clicked(self) -> None:
        """Projektfájl betöltése és alkalmazása a jelenlegi widget-állapotra.

        Ha a betöltött konfiguráció a GUI táblái által jelenleg nem
        szerkeszthető felülbírálásokat tartalmaz, egy külön figyelmeztető
        sor is a `status_log`-ba kerül (lásd `config_loader.apply_pipeline_config()`).
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Projekt megnyitása", "", _PROJECT_FILE_FILTER
        )
        if not file_path:
            return

        try:
            config = persistence.load_project_config(file_path)
            override_count = config_loader.apply_pipeline_config(
                config, self.parameter_panel, self.run_panel
            )
        except PipelineConfigurationError as error:
            logger.warning("Projektbetöltési konfigurációs hiba: %s", error)
            self.run_panel.status_log.append(f"Konfigurációs hiba: {error}")
        except SliceDesignerError as error:
            logger.exception("Hiba a projekt betöltése során.")
            self.run_panel.status_log.append(f"Hiba a betöltés során: {error}")
        else:
            self.run_panel.status_log.append("Projekt betöltve.")
            if override_count > 0:
                self.run_panel.status_log.append(
                    f"Figyelem: {override_count} kézi felülbírálás van a "
                    "fájlban, amit a felület jelenleg nem jelenít meg."
                )

    def _on_mesh_file_selected(self, file_path: str) -> None:
        """Automatikus 3D-előnézet betöltése egy sikeres mesh-fájl-választás után.

        A paraméter-panel jelenlegi (mesh-importhoz tartozó) widget-
        értékeiből állít elő egy `MeshImportParams`-t, és kizárólag az
        `import_mesh_preview()`-t hívja meg — `run_pipeline()` ilyenkor
        nem fut le, a "Futtatás" gomb állapotát ez a művelet nem érinti.
        Ha a mezők a fájlválasztás után módosulnak, az előnézet nem
        frissül automatikusan (csak új fájlválasztásra).
        """
        panel = self.parameter_panel
        params = MeshImportParams(
            file_path=file_path,
            origin_alignment=panel.origin_alignment_combo.currentData(),
            min_plausible_size_mm=panel.min_plausible_size_spin.value(),
            max_plausible_size_mm=panel.max_plausible_size_spin.value(),
        )
        try:
            mesh = import_mesh_preview(params)
        except SliceDesignerError as error:
            logger.exception("Hiba az előnézet betöltése során.")
            self.run_panel.status_log.append(
                f"Hiba az előnézet betöltése során: {error}"
            )
        else:
            self.preview_panel.show_mesh(mesh)

    def _on_run_clicked(self) -> None:
        """A teljes pipeline futtatása a jelenlegi widget-állapotokból.

        A `config_builder.build_pipeline_config()` (widget-olvasás) a fő
        szálon, szinkron fut — ha ez hibázik, a szál el sem indul. Sikeres
        konfiguráció esetén a tényleges (lassú) `run_pipeline()`-hívás egy
        `_PipelineWorker` háttérszálon fut le; az eredmény a
        `_on_pipeline_succeeded`/`_on_pipeline_failed` slotokban, a fő
        szálon kerül feldolgozásra (`_PipelineWorker.succeeded`/`failed`).

        A `run_button`, a "Fájl" menü két akciója és a folyamatjelző
        állapota a futtatás idejére vált, a kimenettől függetlenül a
        `_finish_run()`-ban áll vissza. Minden elkapott kivétel a
        `logger`-be is naplózásra kerül (CODING_STANDARDS 5. szakasz).
        """
        self.run_panel.run_button.setEnabled(False)
        self.run_panel.export_dxf_button.setEnabled(False)
        self._last_nests = None
        self._save_action.setEnabled(False)
        self._open_action.setEnabled(False)
        self.run_panel.progress_bar.setVisible(True)

        try:
            config = config_builder.build_pipeline_config(
                self.parameter_panel, self.run_panel
            )
        except PipelineConfigurationError as error:
            logger.warning("Pipeline-konfigurációs hiba: %s", error)
            self.run_panel.status_log.append(f"Konfigurációs hiba: {error}")
            self._finish_run()
            return
        except SliceDesignerError as error:
            logger.exception("Hiba a pipeline-feldolgozás során.")
            self.run_panel.status_log.append(f"Hiba a feldolgozás során: {error}")
            self._finish_run()
            return

        self._worker = _PipelineWorker(config, self)
        self._worker.succeeded.connect(self._on_pipeline_succeeded)
        self._worker.failed.connect(self._on_pipeline_failed)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    def _on_pipeline_succeeded(self, result: PipelineResult) -> None:
        """A `_PipelineWorker.succeeded` jelzésre kötött slot (fő szál).

        Szó szerint a korábbi, szinkron `_on_run_clicked()` `else`-ágának
        viselkedése, kiegészítve a Backplate előnézettel. A `PipelineResult`
        nem tartalmazza a `backplate_normal_axis`-t (a `Backplate` objektum
        maga sem tárolja, hol helyezkedik el e tengely mentén) — ezért a
        `self._worker.config`-ból (a ténylegesen lefutott `PipelineConfig`-ból)
        olvassuk ki, ha volt Backplate.

        A DXF Export a Futtatásról leválasztva, önálló interakcióvá vált
        (ADR-0009) — a `PipelineResult` már nem tartalmaz automatikusan
        előállított exportot, ezért a sikeres üzenet a Nest-ek (lapok)
        számát jelzi, és a `self._last_nests` kerül beállításra a "DXF
        Export" gomb engedélyezésével együtt.

        A `_finish_run()` hívása itt SZÁNDÉKOSAN NEM történik meg — a
        3D-előnézet geometria-építése (`show_sliced_assembly()`) mostantól
        háttérszálon fut (ADR-0011), és a `_finish_run()`-t csak annak
        befejezésekor (`PreviewPanel.assembly_render_succeeded`/
        `assembly_render_failed`, l. `__init__`) hívjuk meg — így a
        "Futtatás" gomb/menü a teljes, felhasználó számára látható
        művelet (pipeline-számítás + 3D-megjelenítés) végéig letiltott
        marad, ugyanúgy, ahogy a korábbi, szinkron viselkedésnél is
        (amikor a renderelés még a hívás része volt) — ez egyúttal
        kizárja, hogy egy újabb Futtatás a még folyamatban lévő
        előnézet-építéssel versenyhelyzetbe kerüljön.
        """
        message = (
            f"Futtatás sikeres — {result.slice_set.slice_count} szelet, "
            f"{len(result.nests)} lap."
        )
        logger.info(message)
        self.run_panel.status_log.append(message)

        self._last_nests = result.nests
        self.run_panel.export_dxf_button.setEnabled(True)

        backplate_normal_axis: BackplateNormalAxis | None = None
        if result.backplate is not None and self._worker is not None:
            backplate_params = self._worker.config.backplate
            if backplate_params is not None:
                backplate_normal_axis = backplate_params.backplate_normal_axis

        self.preview_panel.show_sliced_assembly(
            result.slice_set,
            result.dowel_positions,
            result.spacers,
            result.backplate,
            backplate_normal_axis,
        )

    def _on_preview_render_failed(self, error: Exception) -> None:
        """A `PreviewPanel.assembly_render_failed` jelzésre kötött slot (fő
        szál, ADR-0011) — a 3D-előnézet geometria-építése (háttérszálon)
        hibába ütközött.

        A `PreviewPanel` már naplózta a kivételt (CODING_STANDARDS 5.
        szakasz); itt csak a felhasználó felé látható állapot-üzenet és a
        futtatás-állapot lezárása (`_finish_run()`) történik — a Futtatás
        maga (a pipeline-számítás) sikeres volt, ezért ez figyelmeztetés,
        nem a Futtatás sikerességének visszavonása.
        """
        self.run_panel.status_log.append(
            f"Figyelem: a 3D-előnézet felépítése hibába ütközött: {error}"
        )
        self._finish_run()

    def _on_pipeline_failed(self, error: SliceDesignerError) -> None:
        """A `_PipelineWorker.failed` jelzésre kötött slot (fő szál).

        Szó szerint a korábbi, szinkron `_on_run_clicked()`
        `except`-ágainak viselkedése — a `PipelineConfigurationError`/
        egyéb `SliceDesignerError` megkülönböztetés itt, a fő szálon
        történik (a worker csak a kivétel-objektumot továbbítja).
        """
        if isinstance(error, PipelineConfigurationError):
            logger.warning("Pipeline-konfigurációs hiba: %s", error)
            self.run_panel.status_log.append(f"Konfigurációs hiba: {error}")
        else:
            logger.exception("Hiba a pipeline-feldolgozás során.", exc_info=error)
            self.run_panel.status_log.append(f"Hiba a feldolgozás során: {error}")
        self._finish_run()

    def _finish_run(self) -> None:
        """A futtatás-állapot (gomb, menü, folyamatjelző) visszaállítása —
        siker, hiba és a konfiguráció-építési hiba ágán is ez zárja le."""
        self.run_panel.run_button.setEnabled(True)
        self._save_action.setEnabled(True)
        self._open_action.setEnabled(True)
        self.run_panel.progress_bar.setVisible(False)
        self._worker = None

    def _on_export_dxf_clicked(self) -> None:
        """A "DXF Export" gomb kattintás-eseménye (ADR-0009).

        A `self._last_nests` a legutóbbi sikeres Futtatás Nest-jei — ha
        `None` (nem futott még sikeres Futtatás, vagy egy újabb Futtatás
        már érvénytelenítette), a gomb `_on_run_clicked()`/
        `_on_pipeline_succeeded()` révén letiltott állapotban van, de erre
        nem támaszkodunk kizárólagosan: explicit ellenőrzés is történik.
        """
        if self._last_nests is None:
            self.run_panel.status_log.append(
                "Nincs friss futtatási eredmény — előbb indítsa el a Futtatást."
            )
            return

        try:
            dxf_export = config_builder.build_dxf_export_params(self.run_panel)
            exports = export_pipeline_result_to_dxf(self._last_nests, dxf_export)
        except PipelineConfigurationError as error:
            logger.warning("DXF Export konfigurációs hiba: %s", error)
            self.run_panel.status_log.append(f"Konfigurációs hiba: {error}")
        except SliceDesignerError as error:
            logger.exception("Hiba a DXF Export során.")
            self.run_panel.status_log.append(f"Hiba a DXF Export során: {error}")
        else:
            self.run_panel.status_log.append(f"{len(exports)} DXF fájl exportálva.")
