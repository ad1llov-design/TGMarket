from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command

from states.creation import AdCreation

router = Router()

REGIONS = {
    "osh": "📍 Ош",
    "bishkek": "📍 Бишкек",
    "jalalabad": "📍 Джалал-Абад"
}

CATEGORIES = {
    "phones": "📱 Телефоны",
    "cars": "🚗 Автомобили",
    "realty": "🏠 Недвижимость",
    "other": "📦 Разное"
}

@router.callback_query(F.data == "create_ad")
async def start_ad_creation(callback: types.CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    for code, name in REGIONS.items():
        builder.row(types.InlineKeyboardButton(text=name, callback_data=f"reg_{code}"))
    
    await callback.message.edit_text(
        "Выберите ваш регион:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(AdCreation.region)
    await callback.answer()

@router.callback_query(AdCreation.region, F.data.startswith("reg_"))
async def select_region(callback: types.CallbackQuery, state: FSMContext):
    reg_code = callback.data.split("_")[1]
    await state.update_data(region=reg_code)
    
    builder = InlineKeyboardBuilder()
    for code, name in CATEGORIES.items():
        builder.row(types.InlineKeyboardButton(text=name, callback_data=f"cat_{code}"))
    
    await callback.message.edit_text(
        f"Регион: {REGIONS[reg_code]}\nТеперь выберите категорию:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(AdCreation.category)
    await callback.answer()

@router.callback_query(AdCreation.category, F.data.startswith("cat_"))
async def select_category(callback: types.CallbackQuery, state: FSMContext):
    cat_code = callback.data.split("_")[1]
    await state.update_data(category=cat_code)
    
    await callback.message.edit_text(
        "Введите название товара (Заголовок):"
    )
    await state.set_state(AdCreation.title)
    await callback.answer()

@router.message(AdCreation.title)
async def handle_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer(
        "Теперь отправьте до 10 фотографий товара.\n"
        "Когда закончите, нажмите кнопку 'Готово'.",
        reply_markup=InlineKeyboardBuilder().row(
            types.InlineKeyboardButton(text="✅ Готово (загрузил)", callback_data="photos_done")
        ).as_markup()
    )
    await state.set_state(AdCreation.photos)

@router.message(AdCreation.photos, F.photo)
async def handle_photos(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    
    if len(photos) >= 10:
        await message.answer("Максимальное количество фото (10) загружено. Переходим к описанию.")
        await ask_description(message, state)
    else:
        await message.answer(f"Фото получено ({len(photos)}/10). Жду еще или нажмите 'Готово'.")

@router.callback_query(AdCreation.photos, F.data == "photos_done")
async def photos_done_handler(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("photos"):
        await callback.answer("Нужно отправить хотя бы одно фото!", show_alert=True)
        return
    await ask_description(callback.message, state)
    await callback.answer()

async def ask_description(message: types.Message, state: FSMContext):
    await message.answer("Введите подробное описание:")
    await state.set_state(AdCreation.description)

@router.message(AdCreation.description)
async def handle_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Введите цену:")
    await state.set_state(AdCreation.price)

@router.message(AdCreation.price)
async def handle_price(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer("Введите ваш номер телефона:")
    await state.set_state(AdCreation.contact)

@router.message(AdCreation.contact)
async def handle_contact(message: types.Message, state: FSMContext):
    await state.update_data(contact=message.text)
    data = await state.get_data()
    
    # Get user profile link
    user = message.from_user
    seller_link = f"tg://user?id={user.id}"
    if user.username:
        seller_link = f"https://t.me/{user.username}"

    preview_text = await format_post(data, seller_link, (await message.bot.get_me()).username)
    
    await message.answer("Вот как будет выглядеть ваше объявление:")
    await message.answer_photo(
        photo=data['photos'][0],
        caption=preview_text,
        reply_markup=InlineKeyboardBuilder().row(
            types.InlineKeyboardButton(text="🚀 Опубликовать", callback_data="publish_ad"),
            types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_ad")
        ).as_markup(),
        parse_mode="HTML"
    )
    await state.set_state(AdCreation.preview)

async def format_post(data: dict, seller_link: str, bot_username: str) -> str:
    return (
        f"🔥 <b>{data['title'].upper()}</b>\n\n"
        f"📍 Регион: {REGIONS[data['region']]}\n"
        f"📂 Категория: {CATEGORIES[data['category']]}\n\n"
        f"📝 <b>Описание:</b>\n{data['description']}\n\n"
        f"💰 <b>Цена:</b> {data['price']}\n\n"
        f"📞 <b>Контакты:</b> {data['contact']}\n"
        f"👤 <b>Продавец:</b> <a href='{seller_link}'>Написать</a>\n\n"
        f"--- \n"
        f"🤖 Разместить своё: @{bot_username}"
    )

@router.callback_query(AdCreation.preview, F.data == "publish_ad")
async def publish_ad_handler(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    
    # Channel mapping
    CHANNEL_IDS = {
        "phones": "@test_phones_channel",
        "cars": "@test_cars_channel",
        "realty": "@test_realty_channel",
        "other": "@test_other_channel"
    }
    channel_id = CHANNEL_IDS.get(data['category'])
    
    user = callback.from_user
    seller_link = f"tg://user?id={user.id}"
    if user.username:
        seller_link = f"https://t.me/{user.username}"
        
    post_text = await format_post(data, seller_link, (await bot.get_me()).username)

    try:
        if len(data['photos']) > 1:
            media = [types.InputMediaPhoto(media=data['photos'][0], caption=post_text, parse_mode="HTML")]
            for photo_id in data['photos'][1:]:
                media.append(types.InputMediaPhoto(media=photo_id))
            await bot.send_media_group(chat_id=channel_id, media=media)
        else:
            await bot.send_photo(chat_id=channel_id, photo=data['photos'][0], caption=post_text, parse_mode="HTML")

        await callback.message.edit_caption(
            caption=f"{callback.message.caption}\n\n✅ <b>Опубликовано!</b>",
            reply_markup=None,
            parse_mode="HTML"
        )
        await callback.answer("Объявление успешно опубликовано!", show_alert=True)
        await state.clear()
        
    except Exception as e:
        await callback.answer(f"Ошибка при публикации: {str(e)}", show_alert=True)

@router.callback_query(F.data == "cancel_ad")
async def cancel_ad_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.message.text:
        await callback.message.edit_text("🚫 Создание объявления отменено.")
    else:
        await callback.message.delete()
        await callback.message.answer("🚫 Создание объявления отменено.")
    await callback.answer()
