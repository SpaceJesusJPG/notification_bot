import logging
import os
import sys
import time

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


if __name__ == "__main__":
    bot = Bot(TELEGRAM_TOKEN)
    loop = MailReaderLoop(bot, USER, PASSWORD, IMAP_SERVER, CHAT_ID)
    poll = PollCommandClass(bot, TELEGRAM_TOKEN)
    tasks = [
        {"func": loop, "args": logger, "schedule": 3600, "next_run": 0},
        {"func": poll, "args": None, "schedule": 10, "next_run": 0},
    ]
    while True:
        for task in tasks:
            if time.time() >= task["next_run"]:
                try:
                    task["func"](task["args"])
                except Exception as err:
                    logger.error(f"{type(err), str(err)}")
                finally:
                    if task["func"] == loop:
                        tasks[1]["args"] = loop.lowest_most_recent
                    task["next_run"] = time.time() + task["schedule"]
        time.sleep(10)
