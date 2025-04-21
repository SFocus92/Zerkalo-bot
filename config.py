import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_CHAT_ID = os.getenv("OWNER_CHAT_ID")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
DATABASE_URL = os.getenv("DATABASE_URL")  # Railway предоставляет эту переменную