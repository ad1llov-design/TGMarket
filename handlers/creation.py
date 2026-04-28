from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command

from states.creation import AdCreation

router = Router()


@router.callback_query(F.data == "create_ad")
async def start_ad_creation(callback: types.CallbackQuery, state: FSMContext):
    from database.client import supabase
    try:
        response = supabase.table('channels').select('*').execute()
        channels = response.data
    except Exception as e:
        await callback.answer(f"Ошибка при получении каналов: {e}", show_alert=True)
        return

    if not channels:
        await callback.answer("Каналы не найдены в базе данных.", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    for ch in channels:
        # Use channel_id as part of callback_data
        builder.row(types.InlineKeyboardButton(
            text=f"📢 {ch.get('name', 'Канал')}", 
            callback_data=f"chan_{ch['channel_id']}")
        )
    
    await callback.message.edit_text(
        "Выберите канал для размещения:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(AdCreation.category)
    await state.set_data({"photos": []}) # Clear old photos and data
    await callback.answer()

@router.callback_query(AdCreation.category, F.data.startswith("chan_"))
async def select_channel(callback: types.CallbackQuery, state: FSMContext):
    channel_id = callback.data.split("_", 1)[1]
    await state.update_data(channel_id=channel_id)
    
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
    # Use the custom atomic append_photo method to avoid race conditions
    await state.storage.append_photo(state.key, message.photo[-1].file_id)
    
    # We can't rely on getting accurate count here because of race conditions, 
    # but we can at least confirm receipt.
    await message.answer("Фото получено! Если закончили, нажмите кнопку 'Готово'.")

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
    if not message.text:
        await message.answer("Пожалуйста, введите текстовое описание.")
        return
    await state.update_data(description=message.text)
    await message.answer("Теперь введите цену (например, 5000 сом):")
    await state.set_state(AdCreation.price)

@router.message(AdCreation.price)
async def handle_price(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, введите цену текстом.")
        return
    await state.update_data(price=message.text)
    await message.answer("Введите ваш номер телефона для связи:")
    await state.set_state(AdCreation.contact)

@router.message(AdCreation.contact)
async def handle_contact(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, введите контактные данные.")
        return
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
    channel_id = data.get('channel_id')
    
    if not channel_id:
        await callback.answer("Ошибка: Канал не выбран.", show_alert=True)
        return
        
    user = callback.from_user

    seller_link = f"tg://user?id={user.id}"
    if user.username:
        seller_link = f"https://t.me/{user.username}"
        
    post_text = await format_post(data, seller_link, (await bot.get_me()).username)

    try:
        # Clean channel_id (sometimes people put spaces)
        channel_id = str(channel_id).strip()
        
        # Ensure it starts with @ if it's a username and not an ID
        if not channel_id.startswith('@') and not channel_id.startswith('-'):
            channel_id = f"@{channel_id}"

        # Limit to 10 photos
        all_photos = data.get('photos', [])[:10]

        if len(all_photos) > 1:
            media = [types.InputMediaPhoto(media=all_photos[0], caption=post_text, parse_mode="HTML")]
            for photo_id in all_photos[1:]:
                media.append(types.InputMediaPhoto(media=photo_id))
            await bot.send_media_group(chat_id=channel_id, media=media)
        elif all_photos:
            await bot.send_photo(chat_id=channel_id, photo=all_photos[0], caption=post_text, parse_mode="HTML")
        else:
            await bot.send_message(chat_id=channel_id, text=post_text, parse_mode="HTML")

        await callback.message.edit_caption(
            caption=f"{callback.message.caption}\n\n✅ <b>Опубликовано!</b>",
            reply_markup=None,
            parse_mode="HTML"
        )
        await callback.answer("Объявление успешно опубликовано!", show_alert=True)
        
        # Save to DB
        from database.client import supabase
        try:
            supabase.table('listings').insert({
                "user_id": user.id,
                "channel_id": channel_id,
                "title": data['title'],
                "description": data['description'],
                "price": data['price'],
                "contact": data['contact'],
                "photos": data.get('photos', [])
            }).execute()
        except Exception as e:
            sys.stderr.write(f"ERROR: Failed to save listing to DB: {e}\n")
            
        await state.clear()
        
    except Exception as e:
        error_msg = str(e)
        detailed_error = f"Ошибка при публикации в {channel_id}: {error_msg}\n\nПожалуйста, убедитесь, что бот является АДМИНИСТРАТОРОМ этого канала."
        await callback.answer(detailed_error, show_alert=True)
        sys.stderr.write(f"ERROR: Publication failed for {channel_id}: {e}\n")

@router.callback_query(F.data == "cancel_ad")
async def cancel_ad_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.message.text:
        await callback.message.edit_text("🚫 Создание объявления отменено.")
    else:
        await callback.message.delete()
        await callback.message.answer("🚫 Создание объявления отменено.")
    await callback.answer()
