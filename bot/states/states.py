from aiogram.fsm.state import State, StatesGroup


class MainMenu(StatesGroup):
    main = State()


class CharacterList(StatesGroup):
    main = State()


class CharacterInfo(StatesGroup):
    main = State()
    inventory = State()


class CrateCharacter(StatesGroup):
    main = State()


class CampaignList(StatesGroup):
    main = State()


class RatingTable(StatesGroup):
    main = State()


class Notifications(StatesGroup):
    main = State()


class Invitation:
    main = State()
