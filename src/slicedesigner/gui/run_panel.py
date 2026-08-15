"""Futtatás / DXF Export / állapot-widgetek (prompt 2.3 szakasz, 7.4 GUI-átalakítás).

A `RunPanel` továbbra is felelős mindazon widgetek létrehozásáért, amiket
korábban is létrehozott (ugyanazokkal az attribútumnevekkel), de már nem
rakja mindet egyetlen közös, saját layoutba: három, logikailag
elkülönített, publikusan elérhető konténer-widgetet épít fel és tesz
elérhetővé a `MainWindow` számára.

* `export_settings_widget` — a DXF Export paraméterek `QGroupBox`-a; a
  `MainWindow` ezt illeszti be a `ParameterPanel` Export fülébe
  (`ParameterPanel.set_export_tab_content()`), mert az export
  logikailag a bemeneti geometriai/összeépítési paraméterekkel egy
  szinten, a fülsávban jelenik meg — nem a `RunPanel`-en belül.
* `action_container` — a `run_button`/`export_dxf_button`/`progress_bar`;
  a `MainWindow` a `ParameterPanel` oszlop aljára helyezi.
* `status_log` — önálló, húzással állítható magasságú `QSplitter`-panelbe
  kerül a `MainWindow`-ban.
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
    """Futtatás-gomb, DXF Export paraméterek és állapot-/log-terület
    widgetjeinek felépítője — vizuálisan három, elkülönített konténerbe
    szét vannak választva (l. modul-docstring), de mindegyik widget
    ugyanazzal az attribútumnévvel érhető el, mint korábban.

    A "Futtatás" gomb kattintás-eseményét a `MainWindow` köti a tényleges
    `run_pipeline()`-végrehajtáshoz (`MainWindow._on_run_clicked`) — e
    panel csak a widgeteket biztosítja, pipeline-hívást nem végez.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # 1. Export-beállítások konténer — a `MainWindow` illeszti be a
        # `ParameterPanel` Export fülébe.
        self.export_settings_widget = self._build_dxf_export_group()

        # 2. Akció-konténer — a `MainWindow` a `ParameterPanel` oszlop
        # aljára helyezi.
        self.action_container = QWidget(self)
        action_layout = QVBoxLayout(self.action_container)
        action_layout.setContentsMargins(0, 0, 0, 0)

        self.run_button = QPushButton("Futtatás")
        # Vizuálisan kiemelt (zöld) stílus — a projektgazda élő
        # tesztelés utáni visszajelzése alapján, hogy a fő cselekvés-gomb
        # megkülönböztethető legyen a többitől. `:disabled` egy tompított
        # zöld változatot ad, hogy a letiltott állapot (Futtatás/példa-
        # generálás alatt) is egyértelműen megkülönböztethető maradjon.
        self.run_button.setStyleSheet(
            "QPushButton {"
            "  background-color: #4CAF50;"
            "  color: white;"
            "  font-weight: bold;"
            "  padding: 4px;"
            "}"
            "QPushButton:disabled {"
            "  background-color: #A5D6A7;"
            "  color: #F0F0F0;"
            "}"
        )
        action_layout.addWidget(self.run_button)

        # A legutóbbi sikeres Futtatás Nest-jein indítható DXF Export
        # (ADR-0009) — kezdetben, és minden új Futtatás indításakor
        # letiltva; a `MainWindow` engedélyezi sikeres Futtatás után.
        self.export_dxf_button = QPushButton("DXF Export")
        self.export_dxf_button.setEnabled(False)
        action_layout.addWidget(self.export_dxf_button)

        # Határozatlan (0/0) módú sáv — a `run_pipeline()` nem ad
        # köztes/lépésenkénti előrehaladást, ezért csak azt jelzi, hogy a
        # háttérszál dolgozik, nem azt, hogy hol tart.
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        action_layout.addWidget(self.progress_bar)

        # 3. Állapot-/log-terület — a `MainWindow` önálló, húzással
        # állítható magasságú `QSplitter`-panelbe helyezi.
        self.status_log = QTextEdit(self)
        self.status_log.setReadOnly(True)
        self.status_log.setPlaceholderText("Állapot- és hibaüzenetek...")

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
