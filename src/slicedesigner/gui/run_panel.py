"""Futtatás / DXF Export / állapot-panel (prompt 2.4 szakasz).

A DXF Export paraméter-widgetek itt, nem a bal paraméter-panelen
jelennek meg: az export logikailag a pipeline-futtatás kimeneti
lépéséhez tartozik (nem a bemeneti geometriai/összeépítési
paraméterekhez), így egy panelen belül olvasható a "Futtatás" gombbal
és az azt követő állapot-naplóval együtt.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)

# Az ezdxf által ténylegesen támogatott DXF-verziók közül a gyakorlatban
# használt részhalmaz — export_nests_to_dxf() maga sima str-t vár, a
# tényleges érvényesítést futásidőben az ezdxf végzi (lásd
# dxf_export_engine.py: `dxf_version` nem enum/Literal a domain rétegben).
_DXF_VERSIONS = ("R12", "R2000", "R2004", "R2007", "R2010", "R2013", "R2018")


class _CollapsibleSection(QWidget):
    """Összecsukható "Speciális beállítások" alrész — azonos elv, mint
    `parameter_panel._CollapsibleSection`, e panel attól függetlenül."""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._toggle_button = QToolButton(self)
        self._toggle_button.setText(title)
        self._toggle_button.setCheckable(True)
        self._toggle_button.setChecked(False)
        self._toggle_button.setArrowType(Qt.ArrowType.RightArrow)
        self._toggle_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self._toggle_button.toggled.connect(self._on_toggled)

        self.content = QWidget(self)
        self.content.setVisible(False)
        self.content_layout = QFormLayout(self.content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._toggle_button)
        layout.addWidget(self.content)

    def _on_toggled(self, checked: bool) -> None:
        self.content.setVisible(checked)
        self._toggle_button.setArrowType(
            Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow
        )


class RunPanel(QWidget):
    """Futtatás-gomb, DXF Export paraméterek és állapot-/log-terület.

    A "Futtatás" gomb kattintás-eseményét a `MainWindow` köti a tényleges
    `run_pipeline()`-végrehajtáshoz (`MainWindow._on_run_clicked`) — e
    panel csak a widgeteket biztosítja, pipeline-hívást nem végez.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.addWidget(self._build_dxf_export_group())

        self.run_button = QPushButton("Futtatás")
        layout.addWidget(self.run_button)

        # A legutóbbi sikeres Futtatás Nest-jein indítható DXF Export
        # (ADR-0009) — kezdetben, és minden új Futtatás indításakor
        # letiltva; a `MainWindow` engedélyezi sikeres Futtatás után.
        self.export_dxf_button = QPushButton("DXF Export")
        self.export_dxf_button.setEnabled(False)
        layout.addWidget(self.export_dxf_button)

        # Határozatlan (0/0) módú sáv — a `run_pipeline()` nem ad
        # köztes/lépésenkénti előrehaladást, ezért csak azt jelzi, hogy a
        # háttérszál dolgozik, nem azt, hogy hol tart.
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_log = QTextEdit(self)
        self.status_log.setReadOnly(True)
        self.status_log.setPlaceholderText("Állapot- és hibaüzenetek...")
        layout.addWidget(self.status_log)
        logger.debug("RunPanel felépítve.")

    def _build_dxf_export_group(self) -> QGroupBox:
        group = QGroupBox("DXF Export")
        layout = QFormLayout(group)

        output_dir_widget = QWidget()
        output_dir_layout = QHBoxLayout(output_dir_widget)
        output_dir_layout.setContentsMargins(0, 0, 0, 0)
        self.output_directory_label = QLabel("(nincs kiválasztva)")
        self.output_directory_label.setWordWrap(True)
        self.output_directory_button = QPushButton("Tallózás...")
        self.output_directory_button.clicked.connect(self._on_browse_output_directory)
        output_dir_layout.addWidget(self.output_directory_button)
        output_dir_layout.addWidget(self.output_directory_label)
        layout.addRow("Kimeneti könyvtár:", output_dir_widget)

        advanced = _CollapsibleSection("Speciális beállítások")

        self.dxf_version_combo = QComboBox()
        self.dxf_version_combo.addItems(_DXF_VERSIONS)
        self.dxf_version_combo.setCurrentText("R12")
        advanced.content_layout.addRow("DXF verzió:", self.dxf_version_combo)

        self.cut_layer_name_edit = QLineEdit("CUT")
        advanced.content_layout.addRow("Vágás réteg neve:", self.cut_layer_name_edit)

        self.cut_layer_color_spin = QSpinBox()
        self.cut_layer_color_spin.setRange(1, 255)
        self.cut_layer_color_spin.setValue(1)
        advanced.content_layout.addRow(
            "Vágás réteg színe (ACI):", self.cut_layer_color_spin
        )

        self.engrave_layer_name_edit = QLineEdit("ENGRAVE")
        advanced.content_layout.addRow(
            "Gravírozás réteg neve:", self.engrave_layer_name_edit
        )

        self.engrave_layer_color_spin = QSpinBox()
        self.engrave_layer_color_spin.setRange(1, 255)
        self.engrave_layer_color_spin.setValue(5)
        advanced.content_layout.addRow(
            "Gravírozás réteg színe (ACI):", self.engrave_layer_color_spin
        )

        self.output_filename_pattern_edit = QLineEdit(
            "{material_id}_sheet{sheet_number}"
        )
        advanced.content_layout.addRow(
            "Fájlnév-minta:", self.output_filename_pattern_edit
        )

        layout.addRow(advanced)
        return group

    def _on_browse_output_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self, "Kimeneti könyvtár kiválasztása"
        )
        if directory:
            self.output_directory_label.setText(directory)
