import asyncio
from telethon import TelegramClient
import os

# O'ZINGIZNING ADMIN MA'LUMOTLARINGIZNI YOZING
API_ID = 30997088  # YANGI API ID ni qo'ying
API_HASH = "9e4c61409e9ab0df962df01883c2255d"  # YANGI API HASH ni qo'ying
ADMIN_PHONE = "+998775771221"  # Shu telefonga API olingan


async def main():
    # Client yaratish
    client = TelegramClient("admin_session", API_ID, API_HASH)

    # Telefonga ulanish
    await client.start(phone=ADMIN_PHONE)
    print("✅ Ulanish muvaffaqiyatli!")

    # O'zingizga video yuborish
    me = await client.get_me()

    # VIDEO YUBORISH - MP4 fayl nomini yozing
    # Masalan: video_note.mp4, dumaloq.mp4, video.mp4
    video_file_path = "video.mp4"  # SIZNING VIDEO FAYLINGIZ NOMI

    if not os.path.exists(video_file_path):
        print(f"❌ {video_file_path} topilmadi!")
        print("Iltimos, MP4 faylni shu papkaga qo'ying")
        return

    msg = await client.send_file(
        me.id,
        video_file_path,
        video_note=True  # BU dumaloq qiladi!
    )

    print(f"\n✅ Video muvaffaqiyatli yuborildi!")
    print(f"📹 VIDEO_FILE_ID: {msg.video_note.id}")
    print(f"📝 Shu ID ni .env fayliga qo'ying: VIDEO_FILE_ID_1={msg.video_note.id}")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())