import os
from dotenv import load_dotenv

load_dotenv()

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

ODOO_URL = os.getenv("ODOO_URL", "")
ODOO_API_TOKEN = os.getenv("ODOO_API_TOKEN", "")

MANAGER_LINE_USER_ID = os.getenv("MANAGER_LINE_USER_ID", "")
MANAGER_WORK_START = int(os.getenv("MANAGER_WORK_START", "10"))
MANAGER_WORK_END = int(os.getenv("MANAGER_WORK_END", "18"))

SOCIALS_URL = os.getenv("SOCIALS_URL", "https://example.com/socials")
