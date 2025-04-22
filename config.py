import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_CHAT_ID = os.getenv("OWNER_CHAT_ID")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
DATABASE_URL = os.getenv("DATABASE_URL")

# Проверка переменных
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set in environment variables")
if not OWNER_CHAT_ID:
    raise ValueError("OWNER_CHAT_ID not set in environment variables")
if not ADMIN_PASSWORD:
    raise ValueError("ADMIN_PASSWORD not set in environment variables")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set in environment variables")