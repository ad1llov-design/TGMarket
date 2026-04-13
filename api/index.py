import os
import logging
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import config
from handlers import common, creation

# Basic logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=config.bot_token, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# Register routers
dp.include_router(common.router)
dp.include_router(creation.router)

app = FastAPI()

@app.get("/")
async def root():
    if config.webhook_url:
        webhook_path = f"{config.webhook_url}/api/webhook"
        await bot.set_webhook(url=webhook_path)
        return {"message": f"Webhook set to {webhook_path}"}
    return {"message": "TGMarket Bot is running on Vercel! Set WEBHOOK_URL in env to activate."}


@app.post("/api/webhook")
async def webhook(request: Request):
    update = types.Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}

# Vercel needs "app" to be the export
# No need for main polling loop here as Vercel calls the webhook
