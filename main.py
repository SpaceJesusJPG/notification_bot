import os
import sys
import logging
import time as tm

from telegram import Bot
from dotenv import load_dotenv

from mail_parser import get_most_recent_readings, lowest_reading, mail_receiver

load_dotenv()
USER = os.getenv("MAILBOX")
PASSWORD = os.getenv("PASSWORD")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
IMAP_SERVER = "mail.emsd.ru"
CRITICAL_VALUE = {"1303": 11.3, "М-1": 11.0, "Е-1": 11.0}
ATTENTION_VALUE = {"1303": 11.5, "М-1": 11.5, "Е-1": 11.5}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


if __name__ == "__main__":
    bot = Bot(token=TELEGRAM_TOKEN)
    attention_sent = False
    while True:
        critical_sent = False
        most_recent_readings = get_most_recent_readings(
            mail_receiver(USER, PASSWORD, IMAP_SERVER)
        )
        lowest_most_recent = lowest_reading(most_recent_readings)
        for facility, reading in lowest_most_recent.items():
            date, time, voltage = reading
            if voltage < CRITICAL_VALUE[facility]:
                message = f'CRITICAL на {facility} критический заряд {voltage}V на момент {date} {time}'
                bot.send_message(CHAT_ID, message)
                critical_sent = True
            elif voltage < ATTENTION_VALUE[facility] and not attention_sent:
                message = f'ATTENTION на {facility} заряд {voltage}V на момент {date} {time}'
                bot.send_message(CHAT_ID, message)
                logger.info('ATTENTION notification sent.')
                attention_sent = True
        if not critical_sent:
            logger.info('Mail received. No critical voltages. Sleep 1 hour.')
            tm.sleep(3600)
        else:
            logger.info('Mail receive. Critical voltage notification sent. Sleep 1 day.')
            tm.sleep(86400)
            attention_sent = False
