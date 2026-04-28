import asyncio
from telethon import TelegramClient
import os

# ADMIN 1 MA'LUMOTLARI
API_ID = 30997088
API_HASH = "9e4c61409e9ab0df962df01883c2255d"
ADMIN_PHONE = "+998775771221"


async def main():
    client = TelegramClient("admin_session", API_ID, API_HASH)
    await client.start(phone=ADMIN_PHONE)
    print("✅ Ulanish muvaffaqiyatli!")

    video_file = "video.mp4"
    if not os.path.exists(video_file):
        print(f"❌ {video_file} topilmadi!")
        return

    me = await client.get_me()
    msg = await client.send_file(me.id, video_file, video_note=True)

    print(f"\n✅ Yangi VIDEO_ID: {msg.video_note.id}")
    print(f"\n📝 Shu ID ni main.py ga qo'ying:")
    print(f"ADMIN1_VIDEO_ID = \"{msg.video_note.id}\"")
    print(f"ADMIN2_VIDEO_ID = \"{msg.video_note.id}\"")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())