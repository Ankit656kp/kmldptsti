import os

# --- Load from ENV ---
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://user:pass@host/db")
DB_NAME = os.getenv("DB_NAME", "komal_api")

# Telegram cache (channel must allow the bot as admin)
BOT_TOKEN = os.getenv("BOT_TOKEN", "123:ABC")
CHANNEL_ID = os.getenv("CHANNEL_ID", "-1001234567890")  # string ok

# Admin access
ADMIN_KEY = os.getenv("ADMIN_KEY", "ANKIT@656")

# Branding / plans
PROJECT_NAME = os.getenv("PROJECT_NAME", "Komal API")
HOMEPAGE_HEADING = os.getenv("HOMEPAGE_HEADING", "Super Fast Audio/Video API")
FREE_DAILY_LIMIT = int(os.getenv("FREE_DAILY_LIMIT", "1000"))
PAID_DAILY_LIMIT = int(os.getenv("PAID_DAILY_LIMIT", "5000"))
CURRENCY = os.getenv("CURRENCY", "₹")
PAID_PRICE = os.getenv("PAID_PRICE", "29")
SUPPORT_TG = os.getenv("SUPPORT_TG", "@your_support")