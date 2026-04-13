import os
import sys
import logging

# Essential for Vercel: Add parent directory to sys.path so we can import from root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

# Try importing config, handle error for better Vercel logs
try:
    from config import config
except ImportError as e:
    logging.error(f"Failed to import config: {e}")
    config = None

try:
    from handlers import common, creation
except ImportError as e:
    logging.error(f"Failed to import handlers: {e}")
    common = None
    creation = None

app = FastAPI()

@app.get("/")
async def root():
    if not config:
        return {"error": "Config not loaded. Check Environment Variables."}
    
    if config.webhook_url:
        bot = Bot(token=config.bot_token, parse_mode=ParseMode.HTML)
        webhook_path = f"{config.webhook_url}/api/webhook"
        await bot.set_webhook(url=webhook_path)
        return {"message": f"Webhook set to {webhook_path}"}
    return {"message": "TGMarket Bot is running! Set WEBHOOK_URL in env to activate."}

@app.post("/api/webhook")
async def webhook(request: Request):
    if not config:
        return {"error": "Config not initialized"}
        
    bot = Bot(token=config.bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage())
    
    if common:
        dp.include_router(common.router)
    if creation:
        dp.include_router(creation.router)

    try:
        data = await request.json()
        update = types.Update.model_validate(data, context={"bot": bot})
        await dp.feed_update(bot, update)
    except Exception as e:
        logging.error(f"Error processing update: {e}")
        return {"ok": False, "error": str(e)}
        
    return {"ok": True}

