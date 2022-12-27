import logging
import os
import sys
import threading

from dotenv import load_dotenv
from telegram import Bot

from main_classes import MailReaderLoop, PollCommandClass

load_dotenv()

USER = os.getenv("MAILBOX")
PASSWORD = os.getenv("PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
IMAP_SERVER = "mail.emsd.ru"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


bot = Bot(TELEGRAM_TOKEN)
loop = MailReaderLoop(bot, USER, PASSWORD, IMAP_SERVER, CHAT_ID)
poll = PollCommandClass(bot, TELEGRAM_TOKEN)
