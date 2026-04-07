from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text="📢 Разместить объявление", 
        callback_data="create_ad")
    )
    builder.row(types.InlineKeyboardButton(
        text="❓ Помощь", 
        callback_data="help")
    )

    await message.answer(
        f"Привет, {message.from_user.full_name}! 👋\n\n"
        "Я помогу тебе разместить объявление в наших тематических каналах.\n"
        "Просто нажми кнопку ниже, чтобы начать.",
        reply_markup=builder.as_markup()
    )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "Инструкция по использованию:\n\n"
        "1. Нажмите 'Разместить объявление'.\n"
        "2. Выберите подходящую категорию.\n"
        "3. Следуйте инструкциям бота для ввода данных.\n\n"
        "Ваше объявление будет опубликовано после проверки модератором."
    )
