"""Fő alkalmazásablak: bal paraméter-panel, középső 3D előnézet, alsó
futtatás/export/állapot-panel (prompt 2.1 szakasz)."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QCloseEvent
from PySide6.QtWidgets import QFileDialog, QMainWindow, QSplitter, QVBoxLayout, QWidget

from slicedesigner.engines.exceptions import SliceDesignerError
from slicedesigner.gui import app_settings, config_builder, config_loader
from slicedesigner.gui.parameter_panel import ParameterPanel
from slicedesigner.gui.preview_panel import PreviewPanel
from slicedesigner.gui.run_panel import RunPanel
from slicedesigner.project import persistence
from slicedesigner.project.exceptions import PipelineConfigurationError
from slicedesigner.project.pipeline import (
    MeshImportParams,
    import_mesh_preview,
    run_pipeline,
)

logger = logging.getLogger(__name__)

_PROJECT_FILE_FILTER = "Slice Designer projekt (*.json)"


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

        self.parameter_panel = ParameterPanel(self)
        self.preview_panel = PreviewPanel(self)
        self.run_panel = RunPanel(self)
        self.run_panel.run_button.clicked.connect(self._on_run_clicked)
        self.parameter_panel.mesh_file_selected.connect(self._on_mesh_file_selected)
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

        A mentés kimenetelétől függetlenül mindig engedélyezi a bezárást
        (`app_settings.save_current_config()` sosem dob kivételt).
        """
        app_settings.save_current_config(self.parameter_panel, self.run_panel)
        super().closeEvent(event)

    def _build_menu_bar(self) -> None:
        file_menu = self.menuBar().addMenu("Fájl")

        save_action = QAction("Projekt mentése...", self)
        save_action.triggered.connect(self._on_save_project_clicked)
        file_menu.addAction(save_action)

        open_action = QAction("Projekt megnyitása...", self)
        open_action.triggered.connect(self._on_open_project_clicked)
        file_menu.addAction(open_action)

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

        A `run_button` a futtatás idejére letiltásra, végén (a kimenettől
        függetlenül) újra engedélyezésre kerül. Minden elkapott kivétel a
        `logger`-be is naplózásra kerül (CODING_STANDARDS 5. szakasz).
        """
        self.run_panel.run_button.setEnabled(False)
        try:
            config = config_builder.build_pipeline_config(
                self.parameter_panel, self.run_panel
            )
            result = run_pipeline(config)
        except PipelineConfigurationError as error:
            logger.warning("Pipeline-konfigurációs hiba: %s", error)
            self.run_panel.status_log.append(f"Konfigurációs hiba: {error}")
        except SliceDesignerError as error:
            logger.exception("Hiba a pipeline-feldolgozás során.")
            self.run_panel.status_log.append(f"Hiba a feldolgozás során: {error}")
        else:
            message = (
                f"Futtatás sikeres — {result.slice_set.slice_count} szelet, "
                f"{len(result.exports)} exportált DXF fájl."
            )
            logger.info(message)
            self.run_panel.status_log.append(message)
            self.preview_panel.show_sliced_assembly(result.slice_set)
        finally:
            self.run_panel.run_button.setEnabled(True)
