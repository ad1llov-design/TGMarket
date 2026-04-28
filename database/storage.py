from typing import Any, Dict, Optional
from aiogram.fsm.storage.base import BaseStorage, StorageKey, StateType
from database.client import supabase

import sys

class SupabaseStorage(BaseStorage):
    def _get_key(self, key: StorageKey) -> str:
        # Standardize key format
        return f"{key.bot_id}:{key.chat_id}:{key.user_id}"

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        key_str = self._get_key(key)
        state_str = state.state if hasattr(state, 'state') else str(state) if state else None
        
        sys.stderr.write(f"DEBUG: Setting state for {key_str} to {state_str}\n")
        
        try:
            res = supabase.table("bot_fsm").update({"state": state_str}).eq("key", key_str).execute()
            if not res.data:
                sys.stderr.write(f"DEBUG: Row not found, inserting new row for {key_str}\n")
                supabase.table("bot_fsm").insert({"key": key_str, "state": state_str, "data": {}}).execute()
        except Exception as e:
            sys.stderr.write(f"ERROR: Supabase set_state error: {e}\n")

    async def get_state(self, key: StorageKey) -> Optional[str]:
        key_str = self._get_key(key)
        try:
            response = supabase.table("bot_fsm").select("state").eq("key", key_str).execute()
            if response.data:
                val = response.data[0].get("state")
                sys.stderr.write(f"DEBUG: Got state for {key_str}: {val}\n")
                return val
            sys.stderr.write(f"DEBUG: No state found for {key_str}\n")
        except Exception as e:
            sys.stderr.write(f"ERROR: Supabase get_state error: {e}\n")
        return None

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        key_str = self._get_key(key)
        sys.stderr.write(f"DEBUG: Setting data for {key_str}: {data}\n")
        try:
            res = supabase.table("bot_fsm").update({"data": data}).eq("key", key_str).execute()
            if not res.data:
                supabase.table("bot_fsm").insert({"key": key_str, "state": None, "data": data}).execute()
        except Exception as e:
            sys.stderr.write(f"ERROR: Supabase set_data error: {e}\n")

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        key_str = self._get_key(key)
        try:
            response = supabase.table("bot_fsm").select("data").eq("key", key_str).execute()
            if response.data and response.data[0].get("data"):
                val = response.data[0].get("data")
                sys.stderr.write(f"DEBUG: Got data for {key_str}: {val}\n")
                return val
            sys.stderr.write(f"DEBUG: No data found for {key_str}\n")
        except Exception as e:
            sys.stderr.write(f"ERROR: Supabase get_data error: {e}\n")
        return {}

    async def append_media(self, key: StorageKey, media_id: str) -> None:
        key_str = self._get_key(key)
        try:
            # Call the custom postgres function via RPC
            supabase.rpc("append_fsm_media", {"user_key": key_str, "media_id": media_id}).execute()
            sys.stderr.write(f"DEBUG: Appended media {media_id} for {key_str}\n")
        except Exception as e:
            sys.stderr.write(f"ERROR: Supabase append_media error: {e}\n")

    async def close(self) -> None:
        pass
