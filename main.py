from fastapi import FastAPI, Request
from telethon import TelegramClient
from telethon.tl.types import PeerUser
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Admin konfiguratsiyasi
ADMINS = {
    "+998935715043": {
        "api_id": int(os.getenv("ADMIN1_API_ID")),
        "api_hash": os.getenv("ADMIN1_API_HASH"),
        "video_id": os.getenv("VIDEO_FILE_ID_1")
    },
    "+998775771221": {
        "api_id": int(os.getenv("ADMIN2_API_ID")),
        "api_hash": os.getenv("ADMIN2_API_HASH"),
        "video_id": os.getenv("VIDEO_FILE_ID_2")
    }
}

DEFAULT_ADMIN = os.getenv("DEFAULT_ADMIN", "+998775771221")
admin_clients = {}


async def get_admin_client(phone: str):
    """Admin client olish va entity cache ni yuklash"""
    if phone in admin_clients and admin_clients[phone].is_connected():
        return admin_clients[phone]

    config = ADMINS[phone]
    client = TelegramClient(f"session_{phone}", config["api_id"], config["api_hash"])
    await client.start(phone=phone)

    # MUHIM: Dialoglarni yuklash - entity cache to'ldirish
    dialogs = await client.get_dialogs()
    logger.info(f"✅ {len(dialogs)} ta dialog yuklandi")

    admin_clients[phone] = client
    return client


async def get_input_entity(client, user_id: int):
    """User ID ni InputEntity ga aylantirish"""
    try:
        # Avval cache dan izlash
        entity = await client.get_input_entity(PeerUser(user_id))
        return entity
    except Exception as e:
        logger.warning(f"Entity topilmadi, qidirilmoqda... {e}")
        # Dialoglar ichidan qidirish
        async for dialog in client.iter_dialogs():
            if dialog.entity.id == user_id:
                return await client.get_input_entity(user_id)
        raise ValueError(f"User {user_id} topilmadi! Iltimos, avval admin shu user bilan chat ochsin.")


async def send_video_to_user(chat_id: str, admin_phone: str = None):
    """Videoni userga yuborish"""
    try:
        admin_phone = admin_phone or DEFAULT_ADMIN
        client = await get_admin_client(admin_phone)

        # User ID ni integerga o'tkazish
        user_id = int(chat_id)

        # Input entity olish
        entity = await get_input_entity(client, user_id)

        # Video yuborish
        video_id = ADMINS[admin_phone]["video_id"]
        await client.send_file(entity, video_id, video_note=True)

        logger.info(f"✅ Video sent: {admin_phone} → {user_id}")
        return True

    except Exception as e:
        logger.error(f"❌ Send error: {e}")
        return False


@app.post("/pact_webhook")
async def pact_webhook(request: Request):
    """PACT.IM webhook"""
    try:
        data = await request.json()
        user_id = data.get("user_id") or data.get("chat_id")

        if not user_id:
            return {"status": "error", "message": "user_id required"}

        success = await send_video_to_user(str(user_id))
        return {"status": "success" if success else "error", "user_id": user_id}

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/send_video")
async def send_video(request: Request):
    """AmoCRM send video endpoint"""
    try:
        data = await request.json()
        chat_id = data.get("chat_id") or data.get("telegram_id")

        if not chat_id:
            return {"status": "error", "message": "chat_id required"}

        success = await send_video_to_user(str(chat_id))
        return {"status": "success" if success else "error", "chat_id": chat_id}

    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "admins": list(ADMINS.keys()),
        "connected": list(admin_clients.keys())
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)