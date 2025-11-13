from aiogram.fsm.state import State, StatesGroup


class CampaignManagerMain(StatesGroup):
    main = State()


class CampaignManage(StatesGroup):
    main = State()
    edit_info = State()
    manage_characters = State()
    permissions = State()
    stats = State()


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


class ManageCharacters(StatesGroup):
    main = State()
    add_character = State()
    remove_character = State()


class EditPermissions(StatesGroup):
    main = State()
    select_permission = State()
    invite_master = State()
