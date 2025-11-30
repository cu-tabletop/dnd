import logging
from aiogram import Router
from aiogram.types import BufferedInputFile
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import (
    Button,
    Row,
    Group,
    Back,
    Cancel,
    Select,
    SwitchTo,
)
from aiogram_dialog.widgets.text import Const, Format, Multi
from aiogram_dialog.widgets.input import TextInput, ManagedTextInput
from aiogram.types import Message, CallbackQuery
from functools import partial
import json

from services.api_client import api_client
from . import states as campaign_states

logger = logging.getLogger(__name__)


# === Геттеры ===
async def get_characters(dialog_manager: DialogManager, **kwargs):
    selected_campaign = dialog_manager.start_data.get("selected_campaign", {})
    dialog_manager.dialog_data["selected_campaign"] = selected_campaign
    campaign_id = selected_campaign.get("id", 0)
    characters = await api_client.get_campaign_characters(campaign_id)

    return {"characters": characters}


async def get_character_data(manager: DialogManager, **kwargs):
    character_id = manager.dialog_data.get("character_id", 0)
    character = await api_client.get_character(character_id)
    return {"character": character}


async def get_invite_data(manager: DialogManager, **kwargs):
    """Геттер для данных приглашения"""
    return {
        "invite_url": manager.dialog_data.get("invite_url", ""),
        "campaign_name": manager.dialog_data.get("selected_campaign", {}).get(
            "title", "Кампания"
        ),
    }


# === Кнопки ===
async def on_character_selected(
    callback: CallbackQuery,
    widget: Select,
    manager: DialogManager,
    item_id: str,
):
    manager.dialog_data["character_id"] = int(item_id)
    await manager.next()


async def on_change_level(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(campaign_states.ManageCharacters.change_level)


async def on_change_rating(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(campaign_states.ManageCharacters.change_rating)


async def on_view_inventory(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.start(
        campaign_states.ManageInventory.view_inventory,
        data={"character_id": manager.dialog_data.get("character_id", 0)},
    )


async def on_download_jpeg(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    character_id = manager.dialog_data.get("character_id", 0)
    try:
        character = await api_client.get_character(character_id)
        if character:
            # Создаем JSON файл с данными персонажа
            character_data = character.model_dump()
            json_str = json.dumps(character_data, ensure_ascii=False, indent=2)
            json_bytes = json_str.encode("utf-8")

            await callback.message.answer_document(
                document=BufferedInputFile(
                    json_bytes,
                    filename=f"character_{character_id}.json",
                )
            )
    except Exception as e:
        logger.error(f"Error downloading character: {e}")
        await callback.message.answer("❌ Ошибка при загрузке файла")


async def on_change_rating_click(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(campaign_states.ManageCharacters.change_rating)


async def on_quick_rating_change(
    callback: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    item_id: str,
):
    try:
        character_id = manager.dialog_data.get("character_id", 0)
        current_character = await api_client.get_character(character_id)
        if not current_character:
            await callback.answer("❌ Персонаж не найден")
            return

        current_rating = current_character.data.get("rating", 0)
        change = int(item_id)
        new_rating = current_rating + change

        # Валидация
        if new_rating < 0:
            new_rating = 0
        if new_rating > 1000:
            new_rating = 1000

        # Обновление
        result = await api_client.update_character(
            character_id,
            {"rating": new_rating},
        )

        if hasattr(result, "error"):
            await callback.answer(f"❌ Ошибка: {result.error}")
        else:
            await manager.show(campaign_states.ManageCharacters.character_menu)

    except Exception as e:
        logger.error(f"Error in quick rating change: {e}")
        await callback.answer("❌ Ошибка при изменении рейтинга")


async def on_rating_input(
    message: Message,
    widget: ManagedTextInput,
    manager: DialogManager,
    text: str,
):
    try:
        rating = int(text)
        character_id = manager.dialog_data.get("character_id")

        # Валидация рейтинга
        if rating < 0:
            await message.answer("❌ Рейтинг не может быть отрицательным")
            return
        if rating > 1000:
            await message.answer("❌ Рейтинг не может превышать 1000")
            return

        # Обновляем рейтинг через API
        result = await api_client.update_character(
            character_id,
            {"rating": rating},
        )

        if hasattr(result, "error"):
            await message.answer(f"❌ Ошибка: {result.error}")
        else:
            await message.answer(f"✅ Рейтинг успешно изменен на {rating}")
            await manager.switch_to(
                campaign_states.ManageCharacters.character_menu
            )

    except ValueError:
        await message.answer("❌ Пожалуйста, введите целое число")
    except Exception as e:
        logger.error(f"Error updating rating: {e}")
        await message.answer("❌ Ошибка при обновлении рейтинга")


async def on_level_input(
    message: Message,
    widget: ManagedTextInput,
    manager: DialogManager,
    text: str,
):
    try:
        level = int(text)
        character_id = manager.dialog_data.get("character_id", 0)
        result = await api_client.update_character(
            character_id, {"level": level}
        )

        if hasattr(result, "error"):
            await message.answer(f"❌ Ошибка: {result.error}")
        else:
            await message.answer(f"✅ Уровень изменен на {level}")
            await manager.back()
    except ValueError:
        await message.answer("❌ Введите целое число")
    except Exception as e:
        logger.error(f"Error updating level: {e}")
        await message.answer("❌ Ошибка при обновлении уровня")


async def on_add_player(
    message: Message,
    widget: ManagedTextInput,
    manager: DialogManager,
    text: str,
):
    if text.startswith("@"):
        username = text.lstrip("@")

        manager.dialog_data["username"] = username

        try:
            campaign_id = manager.dialog_data["selected_campaign"].get("id", 0)
            invited_by_telegram_id = message.from_user.id

            try:
                await api_client.create_invitation_by_username(
                    campaign_id=campaign_id,
                    username=username,
                    invited_by_telegram_id=invited_by_telegram_id,
                )

                message.answer("✅ Успешно")
                await manager.switch_to(
                    campaign_states.ManageCharacters.character_selection
                )

            except ValueError as e:
                logger.warning(e)
                await message.answer("❌ Ошибка при отправки приглашения")
                return
                await message.answer(
                    f"❌ Игрок @{username} не найден в системе.\n"
                    "Попросите игрока сначала запустить игрового бота."
                )
        except Exception as e:
            logger.warning(e)
            await message.answer("❌ Ошибка при поиске игрока")
    else:
        await message.answer("Введите имя в формате @username")


# === Окна ===
character_window = Window(
    Const("🧙 Выберите персонажа:"),
    Group(
        Select(
            Format("{item.data[name]} (Ур. {item.data[level]})"),
            id="character_select",
            item_id_getter=lambda x: str(x.id),
            items="characters",
            on_click=on_character_selected,
        ),
        width=1,
    ),
    SwitchTo(
        Const("➕ Добавить игрока"),
        id="add_player",
        state=campaign_states.ManageCharacters.add_player,
    ),
    Cancel(Const("⬅️ Назад")),
    state=campaign_states.ManageCharacters.character_selection,
    getter=get_characters,
)

add_player_window = Window(
    Const("Ввдите @username игрока:"),
    TextInput(id="username", on_success=on_add_player),
    SwitchTo(
        Const("🔙 Назад"),
        id="swt_chars_menu",
        state=campaign_states.ManageCharacters.character_selection,
    ),
    state=campaign_states.ManageCharacters.add_player,
)

rating_window = Window(
    Multi(
        Format("🏆 Изменение рейтинга для {character.data[name]}"),
        Format("Текущий рейтинг: {character.data[rating]}"),
        Const(""),
        Const("Введите новый рейтинг:"),
        sep="\n",
    ),
    TextInput(
        id="rating_input",
        on_success=on_rating_input,
    ),
    Button(
        Const("⬅️ Назад"),
        id="back",
        on_click=lambda c, b, m: m.switch_to(
            campaign_states.ManageCharacters.character_menu
        ),
    ),
    state=campaign_states.ManageCharacters.change_rating,
    getter=get_character_data,
)

quick_rating_window = Window(
    Multi(
        Format("🏆 Быстрое изменение рейтинга"),
        Format("Персонаж: {character.data[name]}"),
        Format("Текущий рейтинг: {character.data[rating]}"),
        Const(""),
        Const("Выберите изменение:"),
        sep="\n",
    ),
    Group(
        Row(
            Button(
                Const("+1"),
                id="rating_plus_1",
                on_click=partial(on_quick_rating_change, item_id="1"),
            ),
            Button(
                Const("+5"),
                id="rating_plus_5",
                on_click=partial(on_quick_rating_change, item_id="5"),
            ),
            Button(
                Const("+10"),
                id="rating_plus_10",
                on_click=partial(on_quick_rating_change, item_id="10"),
            ),
        ),
        Row(
            Button(
                Const("-1"),
                id="rating_minus_1",
                on_click=partial(on_quick_rating_change, item_id="-1"),
            ),
            Button(
                Const("-5"),
                id="rating_minus_5",
                on_click=partial(on_quick_rating_change, item_id="-5"),
            ),
            Button(
                Const("-10"),
                id="rating_minus_10",
                on_click=partial(on_quick_rating_change, item_id="-10"),
            ),
        ),
        Button(
            Const("✏️ Ввести точное значение"),
            id="exact_rating",
            on_click=on_change_rating_click,
        ),
    ),
    Button(
        Const("⬅️ Назад"),
        id="back",
        on_click=lambda c, b, m: m.switch_to(
            campaign_states.ManageCharacters.character_menu
        ),
    ),
    state=campaign_states.ManageCharacters.quick_rating,
    getter=get_character_data,
)

level_window = Window(
    Const("Введите новый уровень персонажа:"),
    TextInput(
        id="level_input",
        on_success=on_level_input,
    ),
    Back(Const("⬅️ Назад")),
    state=campaign_states.ManageCharacters.change_level,
)

character_menu_window = Window(
    Multi(
        Format("🧙 Персонаж: {character.data[name]}"),
        Format("⭐ Уровень: {character.data[level]}"),
        Format("🏆 Рейтинг: {character.data[rating]}"),
        sep="\n",
    ),
    Row(
        Button(
            Const("📈 Уровень"), id="change_level", on_click=on_change_level
        ),
        Button(
            Const("🏆 Рейтинг"),
            id="change_rating",
            on_click=lambda c, b, m: m.switch_to(
                campaign_states.ManageCharacters.quick_rating
            ),
        ),
    ),
    Row(
        Button(
            Const("🎒 Инвентарь"),
            id="view_inventory",
            on_click=on_view_inventory,
        ),
        Button(
            Const("📥 Скачать JSON"),
            id="download_json",
            on_click=on_download_jpeg,
        ),
    ),
    Back(Const("⬅️ Назад")),
    Cancel(Const("❌ Выход")),
    state=campaign_states.ManageCharacters.character_menu,
    getter=get_character_data,
)

# === Создание диалога и роутера ===
dialog = Dialog(
    add_player_window,
    character_window,
    character_menu_window,
    level_window,
    rating_window,
    quick_rating_window,
)

router = Router()
router.include_router(dialog)
