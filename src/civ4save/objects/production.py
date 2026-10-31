"""Typed city production orders; no installed game data is required."""

from __future__ import annotations

from enum import IntEnum
from typing import Any

import attrs

from civ4save.vanilla import enums as e


class OrderType(IntEnum):
    """SDK OrderTypes values, kept separate from generated game enums."""

    ORDER_TRAIN = 0
    ORDER_CONSTRUCT = 1
    ORDER_CREATE = 2
    ORDER_MAINTAIN = 3


@attrs.define(slots=True)
class ProductionOrder:
    """One queued order, with saved progress for its item.

    Progress belongs to the item type, not the queue position: repeated orders
    for the same item share that progress. Processes have no stored production.
    Unit AI is a unit's assigned role; other orders have no unit AI.
    """

    order_type: OrderType
    item: e.UnitType | e.BuildingType | e.ProjectType | e.ProcessType
    repeat: bool
    invested_production: int | None
    unit_ai: e.UnitAIType | None = None

    @classmethod
    def from_struct(cls, data: Any, city: Any) -> ProductionOrder:
        """Decode an OrderData record and look up its city's stored progress."""
        order_type = OrderType(data.order_type)
        if data.data1 < 0:
            raise ValueError(f"Negative production item ID: {data.data1}")
        item: e.UnitType | e.BuildingType | e.ProjectType | e.ProcessType
        progress: int | None
        unit_ai = None
        if order_type == OrderType.ORDER_TRAIN:
            item = e.UnitType(data.data1)
            progress = city.unit_production[data.data1]
            unit_ai = e.UnitAIType(data.data2)
        elif order_type == OrderType.ORDER_CONSTRUCT:
            item = e.BuildingType(data.data1)
            progress = city.building_production[data.data1]
        elif order_type == OrderType.ORDER_CREATE:
            item = e.ProjectType(data.data1)
            progress = city.project_production[data.data1]
        else:
            item = e.ProcessType(data.data1)
            progress = None
        return cls(order_type, item, data.save, progress, unit_ai)
