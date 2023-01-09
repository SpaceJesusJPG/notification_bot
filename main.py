import logging
import os
import sys
import threading

from dotenv import load_dotenv
from telegram import Bot

from main_classes import MailHandlerLoop, PollCommandClass

load_dotenv()

USER = os.getenv("MAILBOX")
PASSWORD = os.getenv("PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID_1 = os.getenv("CHAT_ID_1")
CHAT_ID_2 = os.getenv("CHAT_ID_2")
CHAT_ID_3 = os.getenv("CHAT_ID_3")
IMAP_SERVER = "mail.emsd.ru"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


bot = Bot(TELEGRAM_TOKEN)
loop = MailHandlerLoop(bot, logger, USER, PASSWORD, IMAP_SERVER, [CHAT_ID_1, CHAT_ID_2, CHAT_ID_3])
poll = PollCommandClass(bot, TELEGRAM_TOKEN)

reader_thread = threading.Thread(target=loop.email_reader)
sender_thread = threading.Thread(target=loop.notification_sender)
poll_thread = threading.Thread(target=poll, args=(loop,))
reader_thread.start()
sender_thread.start()
poll_thread.start()
