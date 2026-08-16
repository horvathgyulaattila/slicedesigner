"""Projektmentés: `PipelineConfig` (de)szerializálása JSON fájlba/fájlból.

ROADMAP Phase 5, negyedik tétel, első rész — kizárólag a GUI-független
mentés/betöltés logika (a `pipeline.py` modul-docstringje már jelzi ezt a
felelősséget). A GUI "Mentés"/"Megnyitás" gombjai és a widget-visszatöltés
(`PipelineConfig` -> widget-állapotok) külön, következő kör — e modul
widgetről nem tud.

A (de)szerializálás generikus, `dataclasses.fields()`/
`typing.get_type_hints()` alapján rekurzívan bejárja a `PipelineConfig`
fastruktúráját, ahelyett hogy minden beágyazott dataclass/enum mezőjét
kézzel, egyenként sorolná fel — így a `pipeline.py` bővítése (új mező, új
beágyazott dataclass) e modul módosítása nélkül támogatott, amíg a
mező típusa a támogatott típusok egyike (dataclass, Enum, `tuple[X, ...]`,
`X | None`, `Literal`, `str`/`int`/`float`/`bool`).
"""

from __future__ import annotations

import dataclasses
import json
import typing
from enum import Enum
from pathlib import Path

from slicedesigner.project.exceptions import PipelineConfigurationError
from slicedesigner.project.pipeline import PipelineConfig

_SCHEMA_VERSION = 2


def save_project_config(config: PipelineConfig, file_path: str) -> None:
    """A `config` JSON fájlba írása, `{"schema_version": 2, "config": {...}}`
    gyökérszerkezettel.

    Raises:
        PipelineConfigurationError: a fájl nem írható, vagy a `config`
            egy plugin (pl. Relief Generator) által generált `Mesh`-t
            használ (`config.mesh is not None`) — a generált Mesh-es
            projektek mentése jelenleg nem támogatott, ismert korlátozás
            (ADR-0017 nyomán hozott projektgazdai döntés).
    """
    if config.mesh is not None:
        raise PipelineConfigurationError(
            "A jelenlegi projekt egy plugin által generált modellt "
            "(MeshSource, pl. Relief Generator) használ — az ilyen "
            "projektek mentése egyelőre nem támogatott, ismert korlátozás."
        )
    payload = {"schema_version": _SCHEMA_VERSION, "config": _serialize(config)}
    try:
        Path(file_path).write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except OSError as error:
        raise PipelineConfigurationError(
            f"A projektfájl nem írható: {file_path} ({error})."
        ) from error


def load_project_config(file_path: str) -> PipelineConfig:
    """A `file_path`-on található JSON fájlból `PipelineConfig` visszaállítása.

    Raises:
        PipelineConfigurationError: a fájl nem található vagy nem
            olvasható, a tartalma nem érvényes JSON, a gyökér-objektum nem
            a várt `{"schema_version": ..., "config": {...}}` szerkezetű,
            a `schema_version` hiányzik vagy nem `2`, vagy a `config`
            tartalma nem épül fel érvényes `PipelineConfig`-ként (hiányzó
            kötelező mező, érvénytelen enum-érték, típus-eltérés).
    """
    path = Path(file_path)
    if not path.is_file():
        raise PipelineConfigurationError(
            f"A megadott projektfájl nem található vagy nem olvasható: {file_path}"
        )

    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise PipelineConfigurationError(
            f"A projektfájl nem olvasható: {file_path} ({error})."
        ) from error

    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as error:
        raise PipelineConfigurationError(
            f"A projektfájl tartalma nem érvényes JSON: {file_path} ({error})."
        ) from error

    if not isinstance(payload, dict):
        raise PipelineConfigurationError(
            f"A projektfájl gyökér-eleme nem JSON-objektum: {file_path}"
        )

    if payload.get("schema_version") != _SCHEMA_VERSION:
        raise PipelineConfigurationError(
            "A projektfájl schema_version mezője hiányzik vagy nem támogatott "
            f"(kapott: {payload.get('schema_version')!r}, elvárt: {_SCHEMA_VERSION})."
        )

    if "config" not in payload:
        raise PipelineConfigurationError(
            f"A projektfájlból hiányzik a kötelező 'config' kulcs: {file_path}"
        )

    try:
        return typing.cast(
            PipelineConfig, _dataclass_from_dict(PipelineConfig, payload["config"])
        )
    except PipelineConfigurationError:
        raise
    except Exception as error:
        raise PipelineConfigurationError(
            f"A projektfájl 'config' tartalma nem épül fel érvényes "
            f"PipelineConfig-ként: {error}"
        ) from error


def _serialize(value: object) -> object:
    """Egy (beágyazott) dataclass-fastruktúra JSON-kompatibilis alakra
    hozása — a `value` tényleges futásidejű típusa alapján, mezőnkénti
    típus-leírás nélkül."""
    if value is None:
        return None
    if isinstance(value, Enum):
        return value.value
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _serialize(getattr(value, field.name))
            for field in dataclasses.fields(value)
        }
    if isinstance(value, tuple):
        return [_serialize(item) for item in value]
    if isinstance(value, (str, int, float, bool)):
        return value
    raise PipelineConfigurationError(
        f"Nem szerializálható típus a projektmentés során: {type(value)!r}."
    )


def _dataclass_from_dict(cls: type, data: object) -> object:
    """Egy dataclass-osztály és a hozzá tartozó JSON `dict` alapján a
    dataclass egy példányának visszaállítása, mezőnként rekurzívan."""
    if not isinstance(data, dict):
        raise PipelineConfigurationError(
            f"A(z) {cls.__name__} mentett adata nem JSON-objektum: {data!r}"
        )

    hints = typing.get_type_hints(cls)
    kwargs: dict[str, object] = {}
    for field in dataclasses.fields(cls):
        if field.name not in data:
            raise PipelineConfigurationError(
                f"Hiányzó kötelező mező a projektfájlban: {cls.__name__}.{field.name}"
            )
        kwargs[field.name] = _deserialize(data[field.name], hints[field.name])
    return cls(**kwargs)


def _deserialize(value: object, type_hint: object) -> object:
    """Egy JSON-kompatibilis érték visszaalakítása a `type_hint` szerinti
    Python objektummá (dataclass, Enum, tuple, primitív, vagy Optional
    ezek valamelyikéből)."""
    origin = typing.get_origin(type_hint)
    args = typing.get_args(type_hint)

    if origin is not None and type(None) in args:
        if value is None:
            return None
        inner_types = [arg for arg in args if arg is not type(None)]
        return _deserialize(value, inner_types[0])

    if value is None:
        raise PipelineConfigurationError(
            f"Váratlan 'null' érték egy nem opcionális ({type_hint!r}) mezőnél."
        )

    if isinstance(type_hint, type) and issubclass(type_hint, Enum):
        try:
            return type_hint(value)
        except ValueError as error:
            raise PipelineConfigurationError(
                f"Érvénytelen érték a(z) {type_hint.__name__} enumhoz: {value!r}."
            ) from error

    if dataclasses.is_dataclass(type_hint):
        return _dataclass_from_dict(typing.cast(type, type_hint), value)

    if origin is tuple:
        if not isinstance(value, list):
            raise PipelineConfigurationError(
                f"A(z) {type_hint!r} mentett adata nem JSON-tömb: {value!r}"
            )
        if len(args) == 2 and args[1] is Ellipsis:
            item_type = args[0]
            return tuple(_deserialize(item, item_type) for item in value)
        if len(args) != len(value):
            raise PipelineConfigurationError(
                f"A(z) {type_hint!r} mentett adatának hossza ({len(value)}) nem "
                f"egyezik az elvárttal ({len(args)})."
            )
        return tuple(
            _deserialize(item, item_type)
            for item, item_type in zip(value, args, strict=True)
        )

    if origin is typing.Literal:
        if value not in args:
            raise PipelineConfigurationError(
                f"Érvénytelen érték a(z) {type_hint!r} Literal-hoz: {value!r}."
            )
        return value

    return value
