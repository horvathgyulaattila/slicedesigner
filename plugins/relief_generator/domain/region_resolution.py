"""Region Resolution — a Region-fa/-erdő EffectSpec[]-szé feloldása.

Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_REGION_RESOLUTION.md,
ADR-0019.
"""

from __future__ import annotations

from dataclasses import dataclass

from plugins.relief_generator.domain.region import DepthBehavior, Mask, Region
from plugins.relief_generator.exceptions import RegionResolutionError


@dataclass(frozen=True)
class EffectSpec:
    """Egy Region már feloldott, önálló, a lineage mentén már felhalmozott
    relief-hozzájárulása.

    Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_REGION_RESOLUTION.md
    3. szakasz.

    Attributes:
        mask: a forrás `Region.Mask`-ja, változtatás nélkül átvéve.
        elevation: előjeles, a szülőlánc mentén felhalmozott skalár
            (6. szakasz).
        parent_ref: opcionális, strukturális (nem szemantikai) mutató a
            szülő Region már létrehozott EffectSpecjére. `None`
            top-level Regionnél.
        tie_break_priority: opcionális, a maradék, nem-rokon ellentétes
            irányú ütközés feloldásához (Phase 13.4). A Resolver
            kimenetén mindig `None` — l. 7. szakasz.
    """

    mask: Mask
    elevation: float
    parent_ref: "EffectSpec | None" = None
    tie_break_priority: int | None = None


@dataclass(frozen=True)
class _ParentContext:
    """A Resolver belső, tranziens kontextusa — nem kerül az EffectSpecbe.

    Lásd: IMAGE_RELIEF_REGION_RESOLUTION.md 4. szakasz.
    """

    effective_depth_behavior: DepthBehavior
    elevation: float


def resolve_regions(roots: tuple[Region, ...]) -> tuple[EffectSpec, ...]:
    """A Region-fa/-erdő MINDEN csomópontját feloldja EffectSpec-ekké.

    1:1 leképezés — nem csak a leveleket vagy a gyökereket, minden
    bejárt Region pontosan egy EffectSpecet termel.

    Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_REGION_RESOLUTION.md.

    Args:
        roots: a top-level (gyökér) Regionök tuple-je (erdő, l.
            Region Model "Gyökér/erdő").

    Returns:
        Az ÖSSZES bejárt Region EffectSpecjének tuple-je, a Region-fa
        preorder bejárásának megfelelő, determinisztikus sorrendben.

    Raises:
        RegionResolutionError: ha egy top-level Region DepthBehavior-ja
            `Inherit` (kontraktussértés, l. 4. szakasz).
    """
    effect_specs: list[EffectSpec] = []

    def resolve(
        region: Region,
        parent_context: _ParentContext | None,
        parent_effect_spec: EffectSpec | None,
    ) -> None:
        if parent_context is None:
            if region.depth_behavior == DepthBehavior.INHERIT:
                raise RegionResolutionError(
                    "Egy top-level Region DepthBehavior-ja nem lehet "
                    "Inherit (kontraktussértés)."
                )
            effective_depth_behavior = region.depth_behavior
            base_elevation = 0.0
        else:
            effective_depth_behavior = (
                region.depth_behavior
                if region.depth_behavior != DepthBehavior.INHERIT
                else parent_context.effective_depth_behavior
            )
            base_elevation = parent_context.elevation

        signed_contribution = (
            region.contribution
            if effective_depth_behavior == DepthBehavior.RAISED
            else -region.contribution
        )
        elevation = base_elevation + signed_contribution

        effect_spec = EffectSpec(
            mask=region.mask,
            elevation=elevation,
            parent_ref=parent_effect_spec,
        )
        effect_specs.append(effect_spec)

        child_context = _ParentContext(
            effective_depth_behavior=effective_depth_behavior,
            elevation=elevation,
        )
        for child in region.children:
            resolve(child, child_context, effect_spec)

    for root in roots:
        resolve(root, None, None)

    return tuple(effect_specs)
