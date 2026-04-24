from fastapi import FastAPI, Request, HTTPException
from telethon import TelegramClient
import os
import logging
import httpx
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI()

# Telegram Admin configuration
ADMIN_PHONE = os.getenv("ADMIN_PHONE", "+998775771221")
ADMIN_API_ID = int(os.getenv("ADMIN_API_ID", "0"))
ADMIN_API_HASH = os.getenv("ADMIN_API_HASH", "")
VIDEO_FILE_ID = os.getenv("VIDEO_FILE_ID", "")

# Check required variables
if not ADMIN_API_ID or not ADMIN_API_HASH or not VIDEO_FILE_ID:
    logger.error("❌ .env da ADMIN_API_ID, ADMIN_API_HASH yoki VIDEO_FILE_ID yo'q!")
    raise ValueError("Missing required environment variables")

# Global client
admin_client = None


async def get_admin_client():
    """Get or create admin Telegram client"""
    global admin_client
    try:
        if admin_client and admin_client.is_connected():
            return admin_client

        logger.info(f"🔄 Connecting admin: {ADMIN_PHONE}")
        admin_client = TelegramClient("admin_session", ADMIN_API_ID, ADMIN_API_HASH)
        await admin_client.start(phone=ADMIN_PHONE)
        logger.info("✅ Admin client connected successfully!")
        return admin_client
    except Exception as e:
        logger.error(f"❌ Failed to connect admin: {e}")
        return None


@app.on_event("startup")
async def startup_event():
    """Startup event - connect to Telegram"""
    logger.info("🚀 Server starting up...")
    await get_admin_client()
    logger.info("✅ Server ready!")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "status": "running",
        "service": "AmoCRM Video Bot",
        "admin_phone": ADMIN_PHONE,
        "endpoints": {
            "health": "/health",
            "send_video": "/send_video (POST)",
            "pact_webhook": "/pact_webhook (POST)"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    is_connected = admin_client is not None and admin_client.is_connected() if admin_client else False
    return {
        "status": "ok" if is_connected else "disconnected",
        "admin_phone": ADMIN_PHONE,
        "admin_connected": is_connected,
        "video_file_id": VIDEO_FILE_ID[:20] + "..." if VIDEO_FILE_ID else None
    }


@app.post("/pact_webhook")
async def pact_webhook(request: Request):
    """PACT.IM webhook endpoint"""
    try:
        # Get request body
        body = await request.json()
        logger.info(f"📨 PACT webhook received: {body}")

        # Extract user ID
        user_id = body.get("user_id") or body.get("chat_id") or body.get("telegram_id")

        if not user_id:
            logger.error("❌ No user_id found in request")
            return {"status": "error", "message": "user_id required"}

        # Send video
        client = await get_admin_client()
        if not client:
            logger.error("❌ Admin client not connected")
            return {"status": "error", "message": "admin not connected"}

        await client.send_file(int(user_id), VIDEO_FILE_ID, video_note=True)
        logger.info(f"✅ Video sent to user: {user_id}")

        return {
            "status": "success",
            "user_id": user_id,
            "video_sent": True
        }

    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/send_video")
async def send_video(request: Request):
    """Send video endpoint for AmoCRM"""
    try:
        body = await request.json()
        logger.info(f"📨 Send video request: {body}")

        chat_id = body.get("chat_id") or body.get("telegram_id") or body.get("user_id")

        if not chat_id:
            return {"status": "error", "message": "chat_id required"}

        client = await get_admin_client()
        if not client:
            return {"status": "error", "message": "admin not connected"}

        await client.send_file(int(chat_id), VIDEO_FILE_ID, video_note=True)
        logger.info(f"✅ Video sent to: {chat_id}")

        return {"status": "success", "chat_id": chat_id}

    except Exception as e:
        logger.error(f"❌ Send video error: {e}")
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)