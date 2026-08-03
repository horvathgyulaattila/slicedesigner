"""Alkalmazás-szintű alapértelmezések: a teljes widget-állapot automatikus
be-/kitöltése egy fix, felhasználónkénti beállítás-fájlból.

ROADMAP Phase 5, ötödik (utolsó) tétel. Kizárólag a már elfogadott
`config_builder.build_pipeline_config(..., require_complete=False)`,
`config_loader.apply_pipeline_config()` és `persistence.py`
újrahasználásával — nincs új UI, nincs új fájlformátum. A `MainWindow`
induláskor `load_startup_config()`-ot, bezáráskor `save_current_config()`-ot
hív; egyik függvény sem dobhat kivételt a hívója felé, mert egy sérült
beállítás-fájl nem akadályozhatja az indulást, egy sikertelen mentés pedig
a bezárást.
"""

from __future__ import annotations

import logging
from pathlib import Path

from slicedesigner.engines.exceptions import SliceDesignerError
from slicedesigner.gui import config_builder, config_loader
from slicedesigner.gui.parameter_panel import ParameterPanel
from slicedesigner.gui.run_panel import RunPanel
from slicedesigner.project import persistence

logger = logging.getLogger(__name__)

SETTINGS_PATH: Path = Path.home() / ".slicedesigner" / "settings.json"


def load_startup_config(parameter_panel: ParameterPanel, run_panel: RunPanel) -> None:
    """A korábban `save_current_config()`-gal elmentett widget-állapot
    visszaállítása induláskor.

    Ha `SETTINGS_PATH` nem létezik (első indulás), nem történik semmi — a
    hardkódolt widget-alapértékek maradnak. Minden hibát elkap és
    naplóz, sosem dob tovább.
    """
    if not SETTINGS_PATH.is_file():
        return

    try:
        config = persistence.load_project_config(str(SETTINGS_PATH))
        config_loader.apply_pipeline_config(config, parameter_panel, run_panel)
    except SliceDesignerError as error:
        logger.warning("A beállítás-fájl nem tölthető be: %s", error)
    except Exception:
        logger.exception("Váratlan hiba a beállítás-fájl betöltése során.")


def save_current_config(parameter_panel: ParameterPanel, run_panel: RunPanel) -> None:
    """A jelenlegi widget-állapot elmentése a `SETTINGS_PATH` fájlba, hogy
    a következő induláskor `load_startup_config()` visszaállíthassa.

    Minden hibát elkap és naplóz, sosem dob tovább.
    """
    try:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        config = config_builder.build_pipeline_config(
            parameter_panel, run_panel, require_complete=False
        )
        persistence.save_project_config(config, str(SETTINGS_PATH))
    except SliceDesignerError as error:
        logger.warning("A beállítás-fájl nem menthető: %s", error)
    except Exception:
        logger.exception("Váratlan hiba a beállítás-fájl mentése során.")
