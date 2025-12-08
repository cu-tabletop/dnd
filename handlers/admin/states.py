from aiogram.fsm.state import State, StatesGroup


class CampaignList(StatesGroup):
    main = State()


class CreateCampaign(StatesGroup):
    select_title = State()
    select_description = State()
    select_icon = State()
    confirm = State()


class CampaignManage(StatesGroup):
    main = State()


class EditPermissions(StatesGroup):
    main = State()
    selected_master = State()


class InviteMenu(StatesGroup):
    main = State()
    view_qr = State()
    invite = State()


class ManageCharacters(StatesGroup):
    character_selection = State()
    character_menu = State()
    change_level = State()
    change_rating = State()
    quick_rating = State()
    delete_accept = State()


class ManageInventory(StatesGroup):
    view_inventory = State()
    add_inventory_item = State()
    add_inventory_item_description = State()
    add_inventory_item_quantity = State()
    edit_inventory_item = State()
    edit_inventory_item_name = State()
    edit_inventory_item_description = State()
    edit_inventory_item_quantity = State()
    accept_delete = State()


class EditCampaignInfo(StatesGroup):
    select_field = State()
    edit_title = State()
    edit_description = State()
    edit_icon = State()
    confirm = State()
    confirm_delete = State()


class MeetingsMenu(StatesGroup):
    meeting_selection = State()
    meeting_menu = State()


class MeetingCreate(StatesGroup):
    select_title = State()
    select_date = State()
    confirm = State()
