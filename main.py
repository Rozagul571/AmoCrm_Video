from fastapi import FastAPI, Request, HTTPException
from telethon import TelegramClient
import os
import logging
from dotenv import load_dotenv
import asyncio

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# 2 TA ADMIN UCHUN 998935715043
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

# Client cache
clients = {}


async def get_client(phone: str):
    if phone in clients:
        return clients[phone]

    admin = ADMINS.get(phone)
    if not admin:
        raise ValueError(f"Admin {phone} topilmadi!")

    client = TelegramClient(f"session_{phone}", admin["api_id"], admin["api_hash"])
    await client.start(phone=phone)
    clients[phone] = client
    logger.info(f"✅ Admin {phone} ulandi!")
    return client


@app.post("/send_dumaloq")
async def send_video(request: Request):
    try:
        data = await request.json()
        logger.info(f"📨 Webhook: {data}")

        chat_id = data.get("chat_id")
        admin_phone = data.get("admin_phone", "+998775771221")

        if not chat_id:
            raise HTTPException(400, "chat_id kerak!")

        # Video yuborish
        client = await get_client(admin_phone)
        video_id = ADMINS[admin_phone]["video_id"]

        await client.send_file(int(chat_id), video_id, video_note=True)
        logger.info(f"✅ Video yuborildi {admin_phone} → {chat_id}")

        return {"status": "success"}

    except Exception as e:
        logger.error(f"❌ Xato: {e}")
        raise HTTPException(500, str(e))


@app.get("/")
def root():
    return {"status": "running", "admins": list(ADMINS.keys())}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)