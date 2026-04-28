from fastapi import FastAPI, Request
from telethon import TelegramClient
from telethon.errors import FloodWaitError
import os
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# ========== TO‘G‘RI MA'LUMOTLAR ==========
ADMIN1_PHONE = "+998775771221"
ADMIN1_API_ID = 30997088
ADMIN1_API_HASH = "9e4c61409e9ab0df962df01883c2255d"
ADMIN1_VIDEO_ID = "5442760652605136204"

ADMIN2_PHONE = "+998935715043"
ADMIN2_API_ID = 39035419
ADMIN2_API_HASH = "b4a93d29dd08b6d06bff2cf4c952f082"
ADMIN2_VIDEO_ID = "5440862513283504749"

DEFAULT_ADMIN = ADMIN1_PHONE
clients = {}


# ========== VIDEO YUBORISH (ENTITY AVTOMATIK) ==========
async def send_video(chat_id: str, admin_phone: str = None):
    try:
        admin_phone = admin_phone or DEFAULT_ADMIN

        if admin_phone in clients and clients[admin_phone].is_connected():
            client = clients[admin_phone]
        else:
            if admin_phone == ADMIN1_PHONE:
                api_id, api_hash = ADMIN1_API_ID, ADMIN1_API_HASH
            else:
                api_id, api_hash = ADMIN2_API_ID, ADMIN2_API_HASH

            client = TelegramClient(f"session_{admin_phone.replace('+', '')}", api_id, api_hash)
            await client.start(phone=admin_phone)
            # Bir marta dialoglarni yuklash (entity cache uchun)
            await client.get_dialogs()
            clients[admin_phone] = client
            logger.info(f"✅ {admin_phone} ulandi!")

        video_id = ADMIN1_VIDEO_ID  # Ikkala admin ham bitta ID dan foydalansin

        # Entity ni avtomatik topish uchun client.get_entity ishlatiladi
        await client.send_file(int(chat_id), video_id, video_note=True)
        logger.info(f"✅ Video yuborildi: {admin_phone} → {chat_id}")
        return True

    except FloodWaitError as e:
        logger.warning(f"Flood wait {e.seconds}s, kutish...")
        await asyncio.sleep(e.seconds)
        return await send_video(chat_id, admin_phone)
    except Exception as e:
        logger.error(f"❌ Xato: {e}")
        return False


# ========== ENDPOINTLAR ==========
@app.post("/pact_webhook")
async def pact_webhook(request: Request):
    try:
        data = await request.json()
        user_id = data.get("user_id") or data.get("chat_id")
        if not user_id:
            return {"status": "error", "message": "user_id kerak"}
        asyncio.create_task(send_video(str(user_id)))
        return {"status": "processing", "user_id": user_id}
    except Exception as e:
        logger.error(f"Webhook xato: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/health")
async def health():
    return {"status": "ok", "admins": [ADMIN1_PHONE, ADMIN2_PHONE]}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)