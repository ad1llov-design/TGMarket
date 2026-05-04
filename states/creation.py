from aiogram.fsm.state import StatesGroup, State

class AdCreation(StatesGroup):
    region = State()
    category = State()
    title = State()
    media = State()
    description = State()
    price = State()
    contact = State()
    preview = State()
