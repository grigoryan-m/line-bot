import os
from dotenv import load_dotenv

load_dotenv()

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBRR_WRhDRlVLKhgeA8Wfe-EjdQlO1MU5s")

ODOO_URL = os.getenv("ODOO_URL", "")
ODOO_API_TOKEN = os.getenv("ODOO_API_TOKEN", "")
ODOO_HEADER = os.getenv("ODOO_HEADER", "")
MANAGER_LINE_USER_ID = os.getenv("MANAGER_LINE_USER_ID", "")
MANAGER_LINE_ID = os.getenv("MANAGER_LINE_ID", "")  # LINE ID менеджера (отображается пользователю)
MANAGER_WORK_START = int(os.getenv("MANAGER_WORK_START", "10"))
MANAGER_WORK_END = int(os.getenv("MANAGER_WORK_END", "18"))

SOCIALS_URL = os.getenv("SOCIALS_URL", "https://example.com/socials")

# ── BotsAPI connection ────────────────────────────────────────────────────────
BOTS_API_URL = os.getenv("BOTS_API_URL", "http://localhost:8000")
BOTS_API_KEY = os.getenv("BOTS_API_KEY", "")

# ── Odoo Purchase Webhook ─────────────────────────────────────────────────────
# Секрет для защиты POST /odoo/purchase (передаётся в X-API-Key заголовке)
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

# Задержка перед отправкой благодарственного сообщения (секунды, по умолчанию 1 час)
THANK_YOU_DELAY_SECONDS = int(os.getenv("THANK_YOU_DELAY_SECONDS", str(60 * 60)))

# ── Twilio (OTP SMS) ──────────────────────────────────────────────────────────
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_PHONE", "")
TWILIO_MESSAGING_SERVICE_SID = os.getenv("TWILIO_MESSAGING_SERVICE_SID", "")

# ── Meta Ads Manager ──────────────────────────────────────────────────────────
PIXEL_ID = os.getenv("META_ADS_PIXEL_ID", "")
ACCESS_TOKEN = os.getenv("META_ADS_ACCESS_TOKEN", "")
