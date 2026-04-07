from aiogram.fsm.state import StatesGroup, State

class AdCreation(StatesGroup):
    region = State()
    category = State()
    title = State()
    photos = State()
    description = State()
    price = State()
    contact = State()
    preview = State()

