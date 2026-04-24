from typing import Any, Dict, Optional
from aiogram.fsm.storage.base import BaseStorage, StorageKey, StateType
from database.client import supabase

class SupabaseStorage(BaseStorage):
    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        key_str = f"{key.bot_id}:{key.chat_id}:{key.user_id}"
        state_str = state.state if hasattr(state, 'state') else str(state) if state else None
        
        # Try updating first
        try:
            res = supabase.table("bot_fsm").update({"state": state_str}).eq("key", key_str).execute()
            if not res.data:
                supabase.table("bot_fsm").insert({"key": key_str, "state": state_str, "data": {}}).execute()
        except Exception as e:
            print(f"Supabase set_state error: {e}")

    async def get_state(self, key: StorageKey) -> Optional[str]:
        key_str = f"{key.bot_id}:{key.chat_id}:{key.user_id}"
        response = supabase.table("bot_fsm").select("state").eq("key", key_str).execute()
        if response.data:
            return response.data[0].get("state")
        return None

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        key_str = f"{key.bot_id}:{key.chat_id}:{key.user_id}"
        try:
            res = supabase.table("bot_fsm").update({"data": data}).eq("key", key_str).execute()
            if not res.data:
                supabase.table("bot_fsm").insert({"key": key_str, "state": None, "data": data}).execute()
        except Exception as e:
            print(f"Supabase set_data error: {e}")

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        key_str = f"{key.bot_id}:{key.chat_id}:{key.user_id}"
        response = supabase.table("bot_fsm").select("data").eq("key", key_str).execute()
        if response.data and response.data[0].get("data"):
            return response.data[0].get("data")
        return {}

    async def close(self) -> None:
        pass
