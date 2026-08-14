"""Példák megnyitása funkció: a repó `examples/` mappájának listázása és
a kiválasztott példa "regenerálás + megnyitás" munkafolyamata
(`EXAMPLES_LAUNCHER_SPEC.md`, ROADMAP Phase 7 7.2 tétele).

A `preview_panel.py` mintáját követve, ez a modul birtokolja a funkció
teljes, Qt-widget-független (`ExampleInfo`, `discover_examples()`) ÉS
widget-függő (`ExamplesDialog`, `ExampleGenerationWorker`) logikáját.
"""

from __future__ import annotations

import logging
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExampleInfo:
    """Egy érvényes `examples/` alkönyvtár leírása — a `README.md`-ből
    származtatott név/leírás (EXAMPLES_LAUNCHER_SPEC.md 3. szakasz)."""

    directory: Path
    name: str
    description: str


def _parse_readme(readme_path: Path, fallback_name: str) -> tuple[str, str]:
    """A `README.md` elejéből a cím (`name`) és az azt követő első, nem
    üres bekezdés (`description`) kinyerése — defenzíven: ha a fájl nem
    olvasható, vagy nem a várt formátumú (nincs `#`-cím), a mappa neve
    (`fallback_name`) kerül `name`-ként, üres leírással
    (EXAMPLES_LAUNCHER_SPEC.md 7. szakasz)."""
    try:
        text = readme_path.read_text(encoding="utf-8")
    except OSError:
        return fallback_name, ""

    lines = text.splitlines()
    title_index: int | None = None
    name = fallback_name
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#"):
            name = stripped.lstrip("#").strip() or fallback_name
            title_index = index
            break

    if title_index is None:
        return name, ""

    paragraph_lines: list[str] = []
    for line in lines[title_index + 1 :]:
        stripped = line.strip()
        if not stripped:
            if paragraph_lines:
                break
            continue
        paragraph_lines.append(stripped)

    return name, " ".join(paragraph_lines)


def discover_examples(examples_root: Path) -> tuple[ExampleInfo, ...]:
    """A `examples_root` érvényes alkönyvtárainak felsorolása, ábécé-
    sorrendben (mappanév szerint) — egy alkönyvtár csak akkor kerül be,
    ha benne VAN `generate_example.py` ÉS `README.md`
    (EXAMPLES_LAUNCHER_SPEC.md 3. szakasz).

    Ha `examples_root` maga nem létezik (vagy nem könyvtár), üres
    tuple-t ad vissza — ez nem hiba, l. a specifikáció 7. szakaszát."""
    if not examples_root.is_dir():
        return ()

    infos: list[ExampleInfo] = []
    for entry in sorted(examples_root.iterdir(), key=lambda path: path.name):
        if not entry.is_dir():
            continue
        if not (entry / "generate_example.py").is_file():
            continue
        readme_path = entry / "README.md"
        if not readme_path.is_file():
            continue
        name, description = _parse_readme(readme_path, entry.name)
        infos.append(ExampleInfo(directory=entry, name=name, description=description))

    return tuple(infos)


class ExamplesDialog(QDialog):
    """Listázó dialógus a `examples/` érvényes alkönyvtáraihoz
    (EXAMPLES_LAUNCHER_SPEC.md 6.2–6.4. pont).

    Üres eredmény esetén egy nem kiválasztható, tájékoztató sor jelenik
    meg a lista helyén, a "Megnyitás" gomb letiltva marad. Kiválasztás
    (egyszeri kattintás) engedélyezi a "Megnyitás" gombot; dupla
    kattintás közvetlenül elfogadja a dialógust, ugyanúgy, mint a
    "Megnyitás" gomb."""

    def __init__(self, examples_root: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Példák megnyitása")
        self._examples = discover_examples(examples_root)
        self._selected_example: ExampleInfo | None = None

        layout = QVBoxLayout(self)

        self._list_widget = QListWidget(self)
        layout.addWidget(self._list_widget)

        button_widget = QWidget(self)
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)
        self._open_button = QPushButton("Megnyitás", button_widget)
        self._cancel_button = QPushButton("Mégse", button_widget)
        self._open_button.setEnabled(False)
        button_layout.addWidget(self._open_button)
        button_layout.addWidget(self._cancel_button)
        layout.addWidget(button_widget)

        self._open_button.clicked.connect(self._on_open_clicked)
        self._cancel_button.clicked.connect(self.reject)

        if not self._examples:
            empty_item = QListWidgetItem("Nincs elérhető példaprojekt.")
            empty_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self._list_widget.addItem(empty_item)
        else:
            for example in self._examples:
                item = QListWidgetItem(f"{example.name}\n{example.description}")
                item.setData(Qt.ItemDataRole.UserRole, example)
                self._list_widget.addItem(item)
            self._list_widget.itemSelectionChanged.connect(self._on_selection_changed)
            self._list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)

    def _on_selection_changed(self) -> None:
        self._open_button.setEnabled(bool(self._list_widget.selectedItems()))

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        self._accept_item(item)

    def _on_open_clicked(self) -> None:
        selected_items = self._list_widget.selectedItems()
        if selected_items:
            self._accept_item(selected_items[0])

    def _accept_item(self, item: QListWidgetItem) -> None:
        example = item.data(Qt.ItemDataRole.UserRole)
        if example is None:
            return  # az "üres" tájékoztató sor — nem kiválasztható elem
        self._selected_example = example
        self.accept()

    @property
    def selected_example(self) -> ExampleInfo | None:
        """`accept()` után a kiválasztott `ExampleInfo`, egyébként `None`."""
        return self._selected_example


class ExampleGenerationWorker(QThread):
    """Háttérszál: a kiválasztott példa `generate_example.py`-jának
    lefuttatása önálló Python-processzként, `subprocess.run()`-nal.

    A `main_window.py::_PipelineWorker` mintáját követi: `QThread`-
    alosztály `run()`-felülírással, egyetlen blokkoló hívást végez el
    egyszer, `succeeded`/`failed` jelzéssel adja vissza az eredményt a
    fő szálon futó fogadóhoz — `run()` szigorúan nem ér hozzá semmilyen
    widget-hez.

    A `cwd` a példa saját könyvtára — a scriptek maguk `Path(__file__).parent`-
    re támaszkodnak, ez a `cwd`-től függetlenül is helyesen működik, de
    ez a beállítás tükrözi a README-k dokumentált futtatási módját
    leginkább (EXAMPLES_LAUNCHER_SPEC.md, prompt 4. szakasz)."""

    succeeded = Signal(object)  # Path — a friss projektfájl útvonala
    failed = Signal(object)  # Exception

    def __init__(self, example: ExampleInfo, parent: QObject | None = None) -> None:
        super().__init__(parent)
        # Publikus (nem csak a `run()` belsejéhez szükséges) — a
        # `MainWindow` a sikeres/sikertelen jelzés fogadásakor ebből
        # olvassa ki a példa nevét a `status_log`-üzenethez, a
        # `_PipelineWorker.config` mintáját követve.
        self.example = example

    def run(self) -> None:
        script_path = self.example.directory / "generate_example.py"
        try:
            completed = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(self.example.directory),
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as error:
            self.failed.emit(error)
            return

        if completed.returncode != 0:
            self.failed.emit(
                RuntimeError(
                    f"A(z) '{script_path.name}' script hibával tért vissza "
                    f"(kilépő kód: {completed.returncode}). "
                    f"{completed.stderr.strip()}"
                )
            )
            return

        # A projektfájl neve determinisztikusan levezethető: mind a négy
        # meglévő példánál a minta `{mappanév}.json` (l. a
        # `generate_example.py`-k `PROJECT_PATH` konstansát) — nem
        # hardkódolt névlistából, hanem ebből a mintából számítva.
        project_path = self.example.directory / f"{self.example.directory.name}.json"
        self.succeeded.emit(project_path)
