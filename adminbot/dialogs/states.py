from aiogram.fsm.state import State, StatesGroup


class CampaignManagerMain(StatesGroup):
    main = State()


class CampaignManage(StatesGroup):
    main = State()
    edit_info = State()
    manage_characters = State()
    permissions = State()
    # stats = State()


class CreateCampaign(StatesGroup):
    select_title = State()
    select_description = State()
    select_icon = State()
    confirm = State()


class EditCampaignInfo(StatesGroup):
    select_field = State()
    edit_title = State()
    edit_description = State()
    edit_icon = State()
    confirm = State()


class EditPermissions(StatesGroup):
    main = State()
    select_permission = State()
    invite_master = State()


class ManageCharacters(StatesGroup):
    character_selection = State()
    character_menu = State()
    change_level = State()
    change_rating = State()
    quick_rating = State()


class ManageInventory(StatesGroup):
    view_inventory = State()
