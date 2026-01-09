"""
Dev режим — polling
"""

import os
import asyncio
import json
from aiohttp import ClientSession
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

from app import handle_message, handle_callback


async def get_updates(offset: int = None) -> list:
    """Получить обновления"""
    async with ClientSession() as session:
        params = {"timeout": 30}
        if offset:
            params["offset"] = offset
        
        async with session.get(f"{TELEGRAM_API}/getUpdates", params=params) as resp:
            data = await resp.json()
            return data.get("result", [])


async def main():
    print("🚀 Realt Assistant V2 — Polling mode")
    print(f"Bot token: {TELEGRAM_BOT_TOKEN[:10]}...")
    
    # Удаляем webhook если был
    async with ClientSession() as session:
        await session.get(f"{TELEGRAM_API}/deleteWebhook")
    
    offset = None
    
    while True:
        try:
            updates = await get_updates(offset)
            
            for update in updates:
                offset = update["update_id"] + 1
                
                try:
                    if "message" in update:
                        await handle_message(update["message"])
                    elif "callback_query" in update:
                        await handle_callback(update["callback_query"])
                except Exception as e:
                    print(f"[ERROR] Handler: {e}")
        
        except asyncio.CancelledError:
            print("\n👋 Stopping...")
            break
        except Exception as e:
            print(f"[ERROR] Polling: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
