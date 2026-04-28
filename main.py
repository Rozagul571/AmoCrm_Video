from fastapi import FastAPI, Request
from telethon import TelegramClient
import os
import logging
from dotenv import load_dotenv
import asyncio
from telethon.errors import FloodWaitError

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# ============ ADMIN MA'LUMOTLARI ============
ADMIN1_PHONE = "+998775771221"
ADMIN1_API_ID = int(os.getenv("ADMIN1_API_ID", "30997088"))
ADMIN1_API_HASH = os.getenv("ADMIN1_API_HASH", "9e4c61409e9ab0df962df01883c2255d")
ADMIN1_VIDEO_ID = os.getenv("VIDEO_FILE_ID_1", "5442760652605136069")

ADMIN2_PHONE = "+998935715043"
ADMIN2_API_ID = int(os.getenv("ADMIN2_API_ID", "39035419"))
ADMIN2_API_HASH = os.getenv("ADMIN2_API_HASH", "b4a93d29dd08b6d06bff2cf4c952f082")
ADMIN2_VIDEO_ID = os.getenv("VIDEO_FILE_ID_2", "5442760652605136069")

DEFAULT_ADMIN = ADMIN1_PHONE
clients = {}


# ============ ODDIY VIDEO YUBORISH (DIALOGLARSIZ) ============
async def send_video(chat_id: str, admin_phone: str = None):
    """Video yuborish - get_dialogs() ni CHAQIRMAYDI!"""
    try:
        admin_phone = admin_phone or DEFAULT_ADMIN

        # Client olish yoki yaratish
        if admin_phone in clients and clients[admin_phone].is_connected():
            client = clients[admin_phone]
        else:
            if admin_phone == ADMIN1_PHONE:
                api_id, api_hash = ADMIN1_API_ID, ADMIN1_API_HASH
            else:
                api_id, api_hash = ADMIN2_API_ID, ADMIN2_API_HASH

            client = TelegramClient(f"session_{admin_phone.replace('+', '')}", api_id, api_hash)
            await client.start(phone=admin_phone)
            clients[admin_phone] = client
            logger.info(f"✅ {admin_phone} ulandi!")

        # Video ID ni tanlash
        video_id = ADMIN1_VIDEO_ID if admin_phone == ADMIN1_PHONE else ADMIN2_VIDEO_ID

        if not video_id:
            logger.error(f"❌ Video ID yo'q: {admin_phone}")
            return False

        # VIDEO YUBORISH - get_dialogs() YO'Q!
        await client.send_file(int(chat_id), video_id, video_note=True)
        logger.info(f"✅ Video yuborildi: {admin_phone} → {chat_id}")
        return True

    except FloodWaitError as e:
        logger.warning(f"⚠️ Flood wait: {e.seconds} sekund kutish kerak")
        await asyncio.sleep(e.seconds)
        return await send_video(chat_id, admin_phone)
    except Exception as e:
        logger.error(f"❌ Xato: {e}")
        return False


# ============ ENDPOINTLAR ============
@app.post("/pact_webhook")
async def pact_webhook(request: Request):
    try:
        data = await request.json()
        logger.info(f"📨 Webhook: {data}")

        user_id = data.get("user_id") or data.get("chat_id")
        if not user_id:
            return {"status": "error", "message": "user_id kerak"}

        # Video yuborish (asinkron)
        asyncio.create_task(send_video(str(user_id)))

        return {"status": "processing", "user_id": user_id}
    except Exception as e:
        logger.error(f"Webhook xato: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/send_video")
async def send_video_endpoint(request: Request):
    try:
        data = await request.json()
        chat_id = data.get("chat_id") or data.get("telegram_id")

        if not chat_id:
            return {"status": "error", "message": "chat_id kerak"}

        admin_phone = data.get("admin_phone", DEFAULT_ADMIN)
        asyncio.create_task(send_video(str(chat_id), admin_phone))

        return {"status": "processing", "chat_id": chat_id}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "admins": [ADMIN1_PHONE, ADMIN2_PHONE],
        "connected": list(clients.keys())
    }


@app.get("/")
async def root():
    return {"message": "Dumaloq video bot ishlayapti", "health": "/health"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)