"""Effect Processing — az EffectSpec[] egyetlen ReliefValue-vá (itt:
float) történő kombinálása egy adott ponton.

Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_EFFECT_PROCESSING.md.
"""

from __future__ import annotations

from plugins.relief_generator.domain.region_resolution import EffectSpec
from plugins.relief_generator.exceptions import EffectProcessingConflictError


def combine(effect_specs: tuple[EffectSpec, ...], x: float, y: float) -> float:
    """Egy adott ponton az aktív EffectSpec-ek elevation-jéből egyetlen
    ReliefValue-t (itt: float) állít elő.

    Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_EFFECT_PROCESSING.md.

    Args:
        effect_specs: a Region Resolver (`resolve_regions`) teljes
            kimenete.
        x: térbeli X-koordináta, ugyanabban a koordinátarendszerben,
            mint a `Mask.member` hívásokban.
        y: térbeli Y-koordináta.

    Returns:
        A kombinált `ReliefValue` az adott ponton — `0.0`, ha egyetlen
        EffectSpec sem aktív.

    Raises:
        EffectProcessingConflictError: ha legalább egy nem-rokon,
            ellentétes irányú aktív EffectSpec-pár van jelen, és
            egyikük sem rendelkezik egyértelmű, maximális
            `TieBreakPriority`-val (l. 5–6. szakasz).
    """
    active = tuple(spec for spec in effect_specs if spec.mask.member(x, y))
    s_prime = _filter_without_active_descendant(active)

    if not s_prime:
        return 0.0
    if len(s_prime) == 1:
        return s_prime[0].elevation

    positive = tuple(spec for spec in s_prime if spec.elevation > 0.0)
    negative = tuple(spec for spec in s_prime if spec.elevation < 0.0)

    if not positive or not negative:
        return _envelope(s_prime)

    return _tiebreak(positive, negative)


def _filter_without_active_descendant(
    active: tuple[EffectSpec, ...],
) -> tuple[EffectSpec, ...]:
    """Kizárja azokat a tagokat, amelyeknek van `active`-ben lévő
    leszármazottja a `ParentRef`-lánc mentén (lineage-menti occlusion,
    l. 3. szakasz)."""
    return tuple(
        candidate
        for candidate in active
        if not any(
            _is_ancestor(candidate, other)
            for other in active
            if other is not candidate
        )
    )


def _is_ancestor(candidate: EffectSpec, other: EffectSpec) -> bool:
    """Eldönti, hogy `candidate` a `other` őse-e a `ParentRef`-lánc mentén."""
    current = other.parent_ref
    while current is not None:
        if current is candidate:
            return True
        current = current.parent_ref
    return False


def _envelope(specs: tuple[EffectSpec, ...]) -> float:
    """A legnagyobb `|elevation|`-jű tag elevation-jét adja vissza.

    Determinisztikus: Python `max()` az első, maximális kulcsú elemet
    adja vissza egyenlőség esetén, a `specs` bemeneti sorrendje pedig a
    Resolver preorder bejárásából származó, stabil sorrend (l. 4.
    szakasz).
    """
    return max(specs, key=lambda spec: abs(spec.elevation)).elevation


def _tiebreak(
    positive: tuple[EffectSpec, ...], negative: tuple[EffectSpec, ...]
) -> float:
    """A maradék, nem-rokon, ellentétes irányú ütközés feloldása.

    Lásd: IMAGE_RELIEF_EFFECT_PROCESSING.md 5–6. szakasz.

    Raises:
        EffectProcessingConflictError: ha nincs egyértelmű, maximális
            `TieBreakPriority`-jú tag az érintettek között.
    """
    affected = positive + negative
    prioritized = tuple(
        spec for spec in affected if spec.tie_break_priority is not None
    )

    if prioritized:
        max_priority = max(spec.tie_break_priority for spec in prioritized)
        winners = tuple(
            spec
            for spec in prioritized
            if spec.tie_break_priority == max_priority
        )
        if len(winners) == 1:
            return winners[0].elevation

    raise EffectProcessingConflictError(
        f"Nem-rokon, ellentétes irányú ütközés {len(positive)} pozitív és "
        f"{len(negative)} negatív elevation-ű EffectSpec között, "
        "egyértelmű TieBreakPriority nélkül."
    )
