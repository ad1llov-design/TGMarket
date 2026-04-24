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
from aiogram.client.default import DefaultBotProperties
from database.storage import SupabaseStorage

# Try importing everything and catch all errors
try:
    from config import config
    from handlers import common, creation
    STARTUP_ERROR = None
    # Initialize storage and dispatcher once
    storage = SupabaseStorage()
    dp = Dispatcher(storage=storage)
    if common:
        dp.include_router(common.router)
    if creation:
        dp.include_router(creation.router)
except Exception as e:
    import traceback
    STARTUP_ERROR = f"Startup Error: {str(e)}\n{traceback.format_exc()}"
    config = None
    common = None
    creation = None

app = FastAPI()

@app.get("/")
async def root():
    if STARTUP_ERROR:
        return {"ok": False, "error": STARTUP_ERROR}
    
    if not config:
        return {"error": "Config not loaded."}
    
    try:
        bot = Bot(
            token=config.bot_token, 
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        # Normalize webhook URL (remove trailing slash)
        base_url = config.webhook_url.rstrip("/")
        webhook_path = f"{base_url}/api/webhook"
        
        await bot.set_webhook(url=webhook_path)
        return {"message": f"Webhook successfully set to {webhook_path}"}
    except Exception as e:
        return {"ok": False, "error": f"Failed to set webhook: {str(e)}"}

@app.post("/api/webhook")
async def webhook(request: Request):
    if STARTUP_ERROR:
        return {"error": "Startup error, cannot process webhook"}
    
    if not config:
        return {"error": "Config not initialized"}
        
    try:
        bot = Bot(
            token=config.bot_token, 
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )

        data = await request.json()
        update = types.Update.model_validate(data, context={"bot": bot})
        await dp.feed_update(bot, update)
    except Exception as e:
        logging.error(f"Error processing update: {e}")
        return {"ok": False, "error": str(e)}
        
    return {"ok": True}


