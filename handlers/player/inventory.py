import logging
from uuid import UUID

from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Back, Button, Cancel, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format
from pydantic import BaseModel, field_validator

from db.models import Campaign, Item
from states.inventory_view import InventoryView, TargetType

logger = logging.getLogger(__name__)
router = Router()


class InventoryRequest(BaseModel):
    target_type: TargetType
    target_id: int
    campaign_id: int | None = None

    @classmethod
    @field_validator("target_type", mode="before")
    def validate_target_type(cls, v: TargetType | int | str) -> TargetType | None:
        if isinstance(v, TargetType):
            return v
        try:
            if isinstance(v, int):
                return TargetType(v)
            if isinstance(v, str):
                try:
                    return TargetType(int(v))
                except ValueError:
                    return TargetType[v.upper()]
        except (ValueError, KeyError) as e:
            msg = f"Invalid target_type: {v}"
            raise ValueError(msg) from e

    @classmethod
    @field_validator("campaign_id", mode="wrap")
    def validate_campaign_id(cls, v: int | None, values: dict) -> int:
        if "target_type" in values and values["target_type"] == TargetType.CHARACTER and v is None:
            msg = "campaign_id is required for CHARACTER target type"
            raise ValueError(msg)
        return v


async def inventory_data_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    request = InventoryRequest(**dialog_manager.start_data)

    items = []
    if request.target_type == TargetType.USER:
        items = await Item.filter(holder_user=request.target_id).all()
    elif request.target_type == TargetType.CHARACTER:
        campaign = await Campaign.get(id=request.campaign_id)
        items = await Item.filter(holder_character=request.target_id, campaign=campaign.id)

    return {
        "inventory": items,
        "has_items": len(items) > 0,
    }


async def get_inventory_item_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных о выбранном предмете"""
    item_id = dialog_manager.dialog_data.get("selected_item_id")
    if not item_id:
        return {"item": None}

    item = await Item.get(id=item_id)
    return {"item": item, "has_description": item.description != ""}


async def on_inventory_item_selected(c: CallbackQuery, b: Button, m: DialogManager, item_id: UUID):
    m.dialog_data["selected_item_id"] = item_id
    await m.switch_to(InventoryView.preview)


router.include_router(
    Dialog(
        Window(
            Format("Инвентарь персонажа"),
            ScrollingGroup(
                Select(
                    Format("{item.title} ×{item.quantity}"),
                    id="inventory_select",
                    item_id_getter=lambda item: item.id,
                    items="inventory",
                    on_click=on_inventory_item_selected,
                    type_factory=UUID,
                ),
                id="inventory_scroll",
                width=1,
                height=10,
                hide_on_single_page=True,
                when="has_items",
            ),
            Cancel(Const("Назад")),
            getter=inventory_data_getter,
            state=InventoryView.view,
        ),
        Window(
            Format("📦 {item.title}"),
            Format("📝 Описание: {item.description}", when="has_description"),
            Const("📝 Описание отсутствует", when=~F["has_description"]),
            Format("🔢 Количество: {item.quantity}"),
            Back(Const("Назад")),
            getter=get_inventory_item_data,
            state=InventoryView.preview,
        ),
    )
)
