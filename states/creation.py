from aiogram.fsm.state import StatesGroup, State

class AdCreation(StatesGroup):
    region = State()
    title = State()
    media = State()
    description = State()
    price = State()
    contact = State()
    preview = State()

