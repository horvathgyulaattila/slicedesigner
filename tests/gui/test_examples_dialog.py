"""Példák megnyitása funkció tesztjei: a `discover_examples()`/README-
parszolás (Qt-widget-független rész), az `ExamplesDialog` és az
`ExampleGenerationWorker` (EXAMPLES_LAUNCHER_SPEC.md, ROADMAP Phase 7
7.2 tétele)."""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from pytestqt.qtbot import QtBot  # noqa: E402

from slicedesigner.gui import examples_dialog as examples_dialog_module  # noqa: E402
from slicedesigner.gui.examples_dialog import (  # noqa: E402
    ExampleGenerationWorker,
    ExampleInfo,
    ExamplesDialog,
    discover_examples,
)


def _make_example_dir(
    root: Path,
    name: str,
    *,
    readme_text: str = "# Cím\n\nEgy bekezdésnyi leírás.\n",
    with_generate_script: bool = True,
    with_readme: bool = True,
) -> Path:
    directory = root / name
    directory.mkdir()
    if with_generate_script:
        (directory / "generate_example.py").write_text(
            "# teszt-stub\n", encoding="utf-8"
        )
    if with_readme:
        (directory / "README.md").write_text(readme_text, encoding="utf-8")
    return directory


# --- discover_examples() / README-parszolás ---


def test_discover_examples_missing_root_returns_empty(tmp_path: Path) -> None:
    assert discover_examples(tmp_path / "nincs-ilyen") == ()


def test_discover_examples_empty_root_returns_empty(tmp_path: Path) -> None:
    assert discover_examples(tmp_path) == ()


def test_discover_examples_filters_incomplete_directories(tmp_path: Path) -> None:
    _make_example_dir(tmp_path, "valid_example")
    _make_example_dir(tmp_path, "missing_generate", with_generate_script=False)
    _make_example_dir(tmp_path, "missing_readme", with_readme=False)
    (tmp_path / "not_a_directory.txt").write_text("x", encoding="utf-8")

    result = discover_examples(tmp_path)

    assert [example.directory.name for example in result] == ["valid_example"]


def test_discover_examples_sorted_alphabetically_by_directory_name(
    tmp_path: Path,
) -> None:
    _make_example_dir(tmp_path, "b_example")
    _make_example_dir(tmp_path, "a_example")
    _make_example_dir(tmp_path, "c_example")

    result = discover_examples(tmp_path)

    assert [example.directory.name for example in result] == [
        "a_example",
        "b_example",
        "c_example",
    ]


def test_discover_examples_parses_title_and_description(tmp_path: Path) -> None:
    _make_example_dir(
        tmp_path,
        "basic_example",
        readme_text=(
            "# Alap példaprojekt\n\n"
            "Ez a mappa a Slice Designer legegyszerűbb, teljes körű "
            "használatát mutatja be.\n\n"
            "## Mit demonstrál\n"
        ),
    )

    result = discover_examples(tmp_path)

    assert len(result) == 1
    assert result[0].name == "Alap példaprojekt"
    assert result[0].description == (
        "Ez a mappa a Slice Designer legegyszerűbb, teljes körű használatát mutatja be."
    )


def test_discover_examples_joins_multiline_paragraph(tmp_path: Path) -> None:
    _make_example_dir(
        tmp_path,
        "multi_line_example",
        readme_text=(
            "# Cím\n\nElső sor\nmásodik sor\nharmadik sor.\n\nUtána bekezdés.\n"
        ),
    )

    result = discover_examples(tmp_path)

    assert result[0].description == "Első sor második sor harmadik sor."


def test_discover_examples_missing_title_falls_back_to_directory_name(
    tmp_path: Path,
) -> None:
    _make_example_dir(
        tmp_path, "no_title_example", readme_text="Csak sima szöveg, cím nélkül.\n"
    )

    result = discover_examples(tmp_path)

    assert result[0].name == "no_title_example"
    assert result[0].description == ""


# --- ExamplesDialog ---


def test_dialog_shows_empty_state_when_no_examples(
    qtbot: QtBot, tmp_path: Path
) -> None:
    dialog = ExamplesDialog(tmp_path, None)
    qtbot.addWidget(dialog)

    assert dialog._list_widget.count() == 1
    assert not dialog._open_button.isEnabled()


def test_dialog_selecting_item_enables_open_button(
    qtbot: QtBot, tmp_path: Path
) -> None:
    _make_example_dir(tmp_path, "basic_example")
    _make_example_dir(tmp_path, "complex_example")
    dialog = ExamplesDialog(tmp_path, None)
    qtbot.addWidget(dialog)
    assert not dialog._open_button.isEnabled()

    dialog._list_widget.setCurrentRow(0)

    assert dialog._open_button.isEnabled()


def test_dialog_open_button_accepts_with_selected_example(
    qtbot: QtBot, tmp_path: Path
) -> None:
    _make_example_dir(tmp_path, "basic_example")
    _make_example_dir(tmp_path, "complex_example")
    dialog = ExamplesDialog(tmp_path, None)
    qtbot.addWidget(dialog)
    dialog._list_widget.setCurrentRow(1)

    dialog._open_button.click()

    assert dialog.result() == dialog.DialogCode.Accepted
    assert dialog.selected_example is not None
    assert dialog.selected_example.directory.name == "complex_example"


def test_dialog_double_click_accepts_immediately(qtbot: QtBot, tmp_path: Path) -> None:
    _make_example_dir(tmp_path, "basic_example")
    dialog = ExamplesDialog(tmp_path, None)
    qtbot.addWidget(dialog)
    item = dialog._list_widget.item(0)

    dialog._list_widget.itemDoubleClicked.emit(item)

    assert dialog.result() == dialog.DialogCode.Accepted
    assert dialog.selected_example is not None
    assert dialog.selected_example.directory.name == "basic_example"


def test_dialog_cancel_rejects_without_selection(qtbot: QtBot, tmp_path: Path) -> None:
    _make_example_dir(tmp_path, "basic_example")
    dialog = ExamplesDialog(tmp_path, None)
    qtbot.addWidget(dialog)
    dialog._list_widget.setCurrentRow(0)

    dialog._cancel_button.click()

    assert dialog.result() == dialog.DialogCode.Rejected
    assert dialog.selected_example is None


# --- ExampleGenerationWorker ---


def _example_info(tmp_path: Path, name: str = "basic_example") -> ExampleInfo:
    return ExampleInfo(
        directory=tmp_path / name, name="Alap példaprojekt", description=""
    )


def test_worker_succeeded_emits_project_path(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    example = _example_info(tmp_path)
    calls: list[tuple[list[str], str]] = []

    def _fake_run(
        args: list[str], *, cwd: str, capture_output: bool, text: bool, check: bool
    ) -> SimpleNamespace:
        calls.append((args, cwd))
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr(examples_dialog_module.subprocess, "run", _fake_run)

    worker = ExampleGenerationWorker(example)
    received: list[object] = []
    worker.succeeded.connect(received.append)
    with qtbot.waitSignal(worker.succeeded, timeout=5000):
        worker.start()

    assert received == [example.directory / "basic_example.json"]
    assert len(calls) == 1
    assert calls[0][1] == str(example.directory)


def test_worker_failed_on_nonzero_returncode(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    example = _example_info(tmp_path)

    def _fake_run(
        args: list[str], *, cwd: str, capture_output: bool, text: bool, check: bool
    ) -> SimpleNamespace:
        return SimpleNamespace(returncode=1, stderr="valami elszállt")

    monkeypatch.setattr(examples_dialog_module.subprocess, "run", _fake_run)

    worker = ExampleGenerationWorker(example)
    received: list[Exception] = []
    worker.failed.connect(received.append)
    with qtbot.waitSignal(worker.failed, timeout=5000):
        worker.start()

    assert len(received) == 1
    assert "valami elszállt" in str(received[0])


def test_worker_failed_on_subprocess_start_error(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    example = _example_info(tmp_path)
    original_error = OSError("nincs elérhető Python-értelmező")

    def _raise(
        args: list[str], *, cwd: str, capture_output: bool, text: bool, check: bool
    ) -> SimpleNamespace:
        raise original_error

    monkeypatch.setattr(examples_dialog_module.subprocess, "run", _raise)

    worker = ExampleGenerationWorker(example)
    received: list[Exception] = []
    worker.failed.connect(received.append)
    with qtbot.waitSignal(worker.failed, timeout=5000):
        worker.start()

    assert received == [original_error]
