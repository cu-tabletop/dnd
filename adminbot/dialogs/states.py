from aiogram.fsm.state import State, StatesGroup


class CharacterManagementSG(StatesGroup):
    company_selection = State()
    character_selection = State()
    character_menu = State()
    change_level = State()
    change_rating = State()
    quick_rating = State()
    view_inventory = State()
    add_inventory_item = State()
    add_inventory_item_description = State()
    add_inventory_item_quantity = State()
    delete_inventory_item = State()
    edit_inventory_item = State()
    edit_inventory_item_name = State()
    edit_inventory_item_description = State()
    edit_inventory_item_quantity = State()


class CompanyManagerSG1(StatesGroup):
    """Управление компаниями"""

    main = State()  # Список компаний


class CompanyManagerSG2(StatesGroup):
    """Управление компаниями"""

    add_company = State()  # Добавление компании


class CompanyManagerSG3(StatesGroup):
    """Управление компаниями"""

    delete_company = State()  # Удаление компании
    company_selected = State()  # Компания выбран


class CompanyWorkSG(StatesGroup):
    """Работа с конкретной компанией"""

    main = State()  # Главное меню компании
    add_master = State()  # Добавление мастера
    character_manager = State()  # Менеджер персонажей


class CharacterManagerSG(StatesGroup):
    """Управление персонажами в компании"""

    main = State()  # Список персонажей
    character_selected = State()  # Персонаж выбран
    # Состояния для редактирования персонажа (существующие)
    change_level = State()
    change_rating = State()
    view_inventory = State()
    add_inventory_item = State()
    edit_inventory_item = State()
    edit_inventory_item_name = State()
    edit_inventory_item_description = State()
    edit_inventory_item_quantity = State()
