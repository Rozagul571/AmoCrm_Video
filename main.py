from fastapi import FastAPI, Request, HTTPException
from telethon import TelegramClient
import os
import logging
import httpx
from dotenv import load_dotenv
import asyncio
from datetime import datetime

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Telegram Admin sozlamalari
ADMIN_PHONE = os.getenv("ADMIN_PHONE", "+998775771221")
ADMIN_API_ID = int(os.getenv("ADMIN_API_ID"))
ADMIN_API_HASH = os.getenv("ADMIN_API_HASH")
VIDEO_FILE_ID = os.getenv("VIDEO_FILE_ID")

# AmoCRM sozlamalari
AMOCRM_SUBDOMAIN = os.getenv("AMOCRM_SUBDOMAIN", "abrok")

# PACT.IM dan keladigan ma'lumotlar uchun
user_data_cache = {}

admin_client = None


async def get_admin_client():
    global admin_client
    if admin_client and admin_client.is_connected():
        return admin_client

    admin_client = TelegramClient("admin_session", ADMIN_API_ID, ADMIN_API_HASH)
    await admin_client.start(phone=ADMIN_PHONE)
    logger.info("✅ Admin client ishga tushdi!")
    return admin_client


async def send_video_to_user(chat_id: str):
    """Admin nomidan video yuborish"""
    try:
        client = await get_admin_client()
        await client.send_file(int(chat_id), VIDEO_FILE_ID, video_note=True)
        logger.info(f"✅ Dumaloq video yuborildi: {chat_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Video yuborilmadi {chat_id}: {e}")
        return False


@app.post("/pact_webhook")
async def pact_webhook(request: Request):
    """PACT.IM dan webhook - user yozganda ishlaydi"""
    try:
        data = await request.json()
        logger.info(f"📨 PACT webhook keldi: {data}")

        # PACT.IM dan user ID ni olish
        user_id = data.get("user_id") or data.get("chat_id") or data.get("telegram_id")

        if not user_id:
            # Agar to'g'ridan-to'g'ri ID bo'lmasa, boshqa maydonlardan izlash
            contact = data.get("contact", {})
            user_id = contact.get("telegram_id") or contact.get("chat_id")

        if not user_id:
            logger.error("❌ User ID topilmadi!")
            return {"status": "error", "message": "user_id not found"}

        # User ma'lumotlarini cache ga saqlash
        user_data_cache[str(user_id)] = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        # AVTOMATIK VIDEO YUBORISH
        video_sent = await send_video_to_user(str(user_id))

        logger.info(f"✅ User {user_id} ga video yuborildi: {video_sent}")

        return {
            "status": "success",
            "user_id": user_id,
            "video_sent": video_sent
        }

    except Exception as e:
        logger.error(f"❌ Webhook xato: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/send_video")
async def send_video(request: Request):
    """AmoCRM Salesbot dan trigger kelganda"""
    try:
        data = await request.json()
        logger.info(f"📨 AmoCRM trigger keldi: {data}")

        # Turli joylardan chat_id ni olish
        chat_id = (
                data.get("chat_id") or
                data.get("telegram_id") or
                data.get("user_id") or
                data.get("contact", {}).get("telegram_id") or
                data.get("contact", {}).get("custom_fields", {}).get("telegram_id")
        )

        if not chat_id:
            logger.error("❌ chat_id topilmadi!")
            return {"status": "error", "message": "chat_id required"}

        await send_video_to_user(str(chat_id))

        return {"status": "success", "chat_id": chat_id}

    except Exception as e:
        logger.error(f"❌ Xato: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "admin_phone": ADMIN_PHONE,
        "admin_connected": admin_client is not None if admin_client else False,
        "cached_users": len(user_data_cache)
    }


@app.get("/stats")
async def stats():
    return {
        "total_videos_sent": len(user_data_cache),
        "users": list(user_data_cache.keys())
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)