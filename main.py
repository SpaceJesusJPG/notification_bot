import logging
import os
import sys
import threading

from dotenv import load_dotenv
from telegram import Bot

from main_classes import MailHandlerLoop, PollCommandClass
from ssh import SshHandler

load_dotenv()

USER = os.getenv("MAILBOX")
PASSWORD = os.getenv("PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID_1 = os.getenv("CHAT_ID_1")
# CHAT_ID_2 = os.getenv("CHAT_ID_2")
# CHAT_ID_3 = os.getenv("CHAT_ID_3")
# CHAT_ID_4 = os.getenv("CHAT_ID_4")
IMAP_SERVER = "mail.emsd.ru"
HOST_1303 = ("83.149.54.131", "rgdn", "para", "1303")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


bot = Bot(TELEGRAM_TOKEN)
loop = MailHandlerLoop(
    bot, logger, USER, PASSWORD, IMAP_SERVER, [CHAT_ID_1]
)  # ДОБАВЬ ОСТАЛЬНЫЕ ПОТОМ!!!
poll = PollCommandClass(bot, TELEGRAM_TOKEN)
handlers = {
    "1303": SshHandler(HOST_1303),
}

reader_thread = threading.Thread(target=loop.email_reader)
sender_thread = threading.Thread(target=loop.voltage_notification_sender)
poll_thread = threading.Thread(target=poll, args=(loop, handlers))
status_thread_1303 = threading.Thread(
    target=loop.status_notification_sender, args=(handlers["1303"],)
)
reader_thread.start()
sender_thread.start()
poll_thread.start()
status_thread_1303.start()
