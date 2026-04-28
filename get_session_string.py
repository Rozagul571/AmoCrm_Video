# get_session_string.py
import asyncio
from telethon import TelegramClient

async def main():
    client = TelegramClient('temp', 30997088, '9e4c61409e9ab0df962df01883c2255d')
    await client.start(phone='+998775771221')
    session_string = client.session.save()
    print(f"SESSION_STRING={session_string}")
    await client.disconnect()

asyncio.run(main())