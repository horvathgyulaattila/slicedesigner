"""Gyökérszintű pytest-konfiguráció: determinisztikus futtatási környezet ellenőrzése.

Lásd: docs/CODING_STANDARDS.md 7. szakasz (Determinizmus).
"""

import os

import pytest

_REQUIRED_HASH_SEED = "0"


def pytest_configure(config: pytest.Config) -> None:
    """Fail-fast ellenőrzés: a PYTHONHASHSEED rögzített értékre állítva induljon.

    A PYTHONHASHSEED kizárólag az interpreter indulásakor érvényesül, ezért
    utólag, a folyamaton belül nem állítható be megbízhatóan — a
    tesztfuttatás explicit hibával leáll, ha nem a helyes értékkel indult,
    ahelyett hogy csendben, esetleg tévesen próbálná magát újraindítani.
    """
    if os.environ.get("PYTHONHASHSEED") != _REQUIRED_HASH_SEED:
        raise pytest.UsageError(
            "A determinisztikus tesztfuttatáshoz a PYTHONHASHSEED környezeti "
            f'változónak "{_REQUIRED_HASH_SEED}" értékre kell lennie állítva '
            "(docs/CODING_STANDARDS.md 7. szakasz). Futtasd így: "
            f"PYTHONHASHSEED={_REQUIRED_HASH_SEED} uv run pytest"
        )
