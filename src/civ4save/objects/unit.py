"""Current serialized unit state."""

from __future__ import annotations

from typing import Any

import attrs

from civ4save.vanilla import enums as e


@attrs.define(slots=True)
class Unit:
    """A unit identified by the pair (owner, idx), not idx alone.

    Name is the saved custom name and may be empty. Damage is hit points lost.
    """

    idx: int
    owner: int
    unit_type: e.UnitType
    x: int
    y: int
    name: str
    turn_created: int
    group_id: int
    experience: int
    level: int
    damage: int
    promotions: list[e.PromotionType]

    @classmethod
    def from_struct(cls, data: Any) -> Unit:
        """Create a unit from a parsed CvUnit or CvUnitAI record."""
        return cls(
            idx=data.id,
            owner=data.owner,
            unit_type=e.UnitType(data.unit_type),
            x=data.x,
            y=data.y,
            name=data.name,
            turn_created=data.game_turn_created,
            group_id=data.group_id,
            experience=data.experience,
            level=data.level,
            damage=data.damage,
            promotions=[
                e.PromotionType(i)
                for i, enabled in enumerate(data.has_promotion)
                if enabled
            ],
        )
