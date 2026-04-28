# send_first_message.py
import asyncio
from telethon import TelegramClient

async def main():
    client = TelegramClient("admin1_session", 30997088, "9e4c61409e9ab0df962df01883c2255d")
    await client.start(phone="+998775771221")
    await client.send_message(5448095473, "Test message")
    await client.disconnect()

asyncio.run(main())