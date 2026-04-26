"""One-time Telegram authentication helper.

Run once to create the session file:
    python scripts/auth_telegram.py

Requires TELEGRAM_API_ID, TELEGRAM_API_HASH, and TELEGRAM_PHONE in .env.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from telethon import TelegramClient

SESSION_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "telegram_session", "session",
)


async def main():
    api_id   = int(os.getenv("TELEGRAM_API_ID", "0"))
    api_hash = os.getenv("TELEGRAM_API_HASH", "")
    phone    = os.getenv("TELEGRAM_PHONE", "")

    if not api_id or not api_hash:
        print("Set TELEGRAM_API_ID and TELEGRAM_API_HASH in .env first.")
        return

    os.makedirs(os.path.dirname(SESSION_PATH), exist_ok=True)
    async with TelegramClient(SESSION_PATH, api_id, api_hash) as client:
        await client.start(phone=phone)
        print("Auth successful. Session saved to:", SESSION_PATH)


asyncio.run(main())
