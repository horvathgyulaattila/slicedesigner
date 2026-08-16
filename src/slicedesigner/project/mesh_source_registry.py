"""MeshSource plugin discovery és a hozzá tartozó generikus GUI paraméter-séma.

L. ADR-0017. A `MeshSourceDescriptor`/`ParameterSpec` NEM módosítja és NEM
bővíti a `MeshSource` contractot (ADR-0014, MESH_SOURCE.md) — a `MeshSource`
interfész (`get_mesh() -> Mesh`, jelenleg duck-typed, formális Protocol
nélkül a kódban) ettől függetlenül, változatlanul létezik; ez a modul
kizárólag a discovery-időben és a GUI form-építéskor használt, külön
regisztrációs csomagolás.

A core sosem szembesül plugin-specifikus (pl. relief-specifikus) fogalommal
— kizárólag az itt rögzített, generikus típusokkal dolgozik.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from importlib.metadata import entry_points
from typing import Any, Literal

logger = logging.getLogger(__name__)

_ENTRY_POINT_GROUP = "slicedesigner.mesh_sources"

ParameterType = Literal["float", "int", "str", "enum"]


@dataclass(frozen=True)
class ParameterSpec:
    """Egy MeshSource plugin egyetlen, GUI-n generikusan megjeleníthető paramétere.

    Attributes:
        name: a paraméter programozott azonosítója (a `MeshSourceDescriptor.build()`
            `values` dict-jének kulcsa).
        label: a paraméter felhasználó felé megjelenő felirata.
        type: a widget-típus kiválasztásához ("float"/"int"/"str"/"enum").
        default: a paraméter alapértéke.
        minimum: opcionális alsó korlát ("float"/"int" típusnál értelmezett).
        maximum: opcionális felső korlát ("float"/"int" típusnál értelmezett).
        unit: opcionális mértékegység-felirat (pl. "mm", "°").
        choices: "enum" típusnál a választható értékek — más típusnál üres tuple.
    """

    name: str
    label: str
    type: ParameterType
    default: Any
    minimum: float | None = None
    maximum: float | None = None
    unit: str | None = None
    choices: tuple[str, ...] = ()


@dataclass(frozen=True)
class MeshSourceDescriptor:
    """Egy telepített MeshSource plugin generikus, GUI-n megjeleníthető leírója.

    A `build()` a kitöltött `values` dict-ből (kulcsok: az egyes
    `parameters[i].name` értékek) állít elő egy, a `MeshSource` contractot
    (ADR-0014, `get_mesh() -> Mesh`) teljesítő objektumot — ennek pontos
    osztálya plugin-specifikus, a core számára irreleváns, ezért `Any`.
    """

    display_name: str
    parameters: tuple[ParameterSpec, ...]
    build: Callable[[dict[str, Any]], Any]


def discover_mesh_sources() -> tuple[MeshSourceDescriptor, ...]:
    """A telepített MeshSource pluginok felismerése Python entry points
    alapján (`slicedesigner.mesh_sources` csoport, ADR-0017).

    Egyetlen entry point hibás betöltése vagy meghívása (pl. import hiba
    vagy kivétel a pluginban) nem akadályozhatja a többi plugin
    felismerését, és nem dobhat kivételt a hívó felé — naplózásra kerül,
    az adott entry point kimarad az eredményből (a core plugin nélkül/
    hibás pluginnal is teljes értékű marad, ADR-0015 elve).

    Returns:
        A sikeresen betöltött és meghívott entry pointok által visszaadott
        `MeshSourceDescriptor`-ok, felfedezési sorrendben. Nincs telepített
        plugin esetén üres tuple.
    """
    descriptors: list[MeshSourceDescriptor] = []
    for entry_point in entry_points(group=_ENTRY_POINT_GROUP):
        try:
            factory = entry_point.load()
            descriptor = factory()
        except Exception:
            logger.exception(
                "A(z) '%s' MeshSource entry point betöltése/meghívása "
                "sikertelen — kimarad.",
                entry_point.name,
            )
            continue
        descriptors.append(descriptor)
    return tuple(descriptors)
