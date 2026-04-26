import os
import asyncio
from telethon import TelegramClient
from telethon.tl.types import Message
from datetime import datetime, timedelta, timezone

ROOT_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_PATH = os.path.join(ROOT_DIR, "telegram_session", "session")

API_ID   = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")


async def _fetch_channel(client: TelegramClient, channel: str, hours: int = 24) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    posts = []
    async for msg in client.iter_messages(channel, limit=200):
        if not isinstance(msg, Message):
            continue
        if msg.date < cutoff:
            break
        text = msg.text or msg.message or ""
        if text:
            posts.append({"date": msg.date, "text": text})
    return posts


async def scrape_channels_async(channels: list[str], hours: int = 24) -> dict[str, list[dict]]:
    os.makedirs(os.path.dirname(SESSION_PATH), exist_ok=True)
    async with TelegramClient(SESSION_PATH, API_ID, API_HASH) as client:
        results = {}
        for ch in channels:
            try:
                results[ch] = await _fetch_channel(client, ch, hours)
                print(f"Fetched {len(results[ch])} posts from {ch}")
            except Exception as e:
                print(f"Failed to fetch {ch}: {e}")
                results[ch] = []
    return results


def scrape_channels(channels: list[str], hours: int = 24) -> dict[str, list[dict]]:
    return asyncio.run(scrape_channels_async(channels, hours))
