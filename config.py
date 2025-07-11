from dotenv import load_dotenv
load_dotenv()
import os

TOKEN = os.getenv("TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "257524397"))
ADMINS = [int(x) for x in os.getenv("ADMINS", "406149871,257524397").split(",")]

DB_PATH = os.getenv("DB_PATH", "orders.db")
PAGE_SIZE = int(os.getenv("PAGE_SIZE", "1"))

YOOKASSA_PROVIDER_TOKEN = os.getenv("YOOKASSA_PROVIDER_TOKEN")
YOOMONEY_PROVIDER_TOKEN = os.getenv("YOOMONEY_PROVIDER_TOKEN")
YOOMONEY_CLIENT_CARDID = os.getenv("YOOMONEY_CLIENT_CARDID")

AUTO_SERVICE_PRICE = int(os.getenv("AUTO_SERVICE_PRICE", "88000"))
DETAILS_TO_SERVICE_PRICE = int(os.getenv("DETAILS_TO_SERVICE_PRICE", "0"))
DETAILS_ORDER_SERVICE_PRICE = int(os.getenv("DETAILS_ORDER_SERVICE_PRICE", "0"))

AUTO_SERVICE_PRICE, DETAILS_TO_SERVICE_PRICE, DETAILS_ORDER_SERVICE_PRICE
