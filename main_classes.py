import time as tm

import requests

from mail_parser import get_most_recent_readings, lowest_reading, mail_receiver

CRITICAL_VALUE = {"1303": 11.0, "М-1": 10.8, "Е-1": 11.0}
ATTENTION_VALUE = {"1303": 11.2, "М-1": 11.2, "Е-1": 11.2}


class MailHandlerLoop:
    def __init__(self, bot, logger, user, password, imap_server, chat_ids):
        self.bot = bot
        self.user = user
        self.password = password
        self.imap_server = imap_server
        self.chat_ids = chat_ids
        self.attention_sent = False
        self.critical_sent = False
        self.lowest_most_recent = None
        self.logger = logger

    def email_reader(self):
        while True:
            most_recent_readings = get_most_recent_readings(
                mail_receiver(self.user, self.password, self.imap_server)
            )
            self.lowest_most_recent = lowest_reading(most_recent_readings)
            tm.sleep(3600)

    def notification_sender(self):
        while True:
            tm.sleep(5)
            self.critical_sent = False
            for facility, reading in self.lowest_most_recent.items():
                date, time, voltage = reading
                if voltage < CRITICAL_VALUE[facility]:
                    message = f"CRITICAL на {facility} критический заряд {voltage}V на момент {date} {time}"
                    for chat_id in self.chat_ids:
                        self.bot.send_message(chat_id, message)
                    self.critical_sent = True
                elif voltage < ATTENTION_VALUE[facility] and not self.attention_sent:
                    message = f"ATTENTION на {facility} заряд {voltage}V на момент {date} {time}"
                    for chat_id in self.chat_ids:
                        self.bot.send_message(chat_id, message)
                    self.logger.info("ATTENTION notification sent.")
                    self.attention_sent = True
            if not self.critical_sent:
                self.logger.info("No critical voltages. Sleep 1 hour.")
                tm.sleep(3595)
            else:
                self.logger.info(
                    "Critical voltage notification sent. Sleep 1 day."
                )
                self.attention_sent = False
                tm.sleep(86395)


class PollCommandClass:
    def __init__(self, bot, telegram_token):
        self.bot = bot
        self.offset = 0
        self.telegram_token = telegram_token

    def __call__(self, loop):
        while True:
            response = requests.get(
                f"https://api.telegram.org/bot{self.telegram_token}/getUpdates?timeout=60&offset={self.offset}?time"
            )
            result = response.json()["result"]
            if result:
                first_update = result[0]
                self.offset = first_update["update_id"] + 1
                if "message" in first_update:
                    text = first_update["message"]["text"].split()
                    chat_id = first_update["message"]["chat"]["id"]
                    if "/voltage" in text:
                        message = ""
                        if loop.lowest_most_recent:
                            lowest_most_recent = loop.lowest_most_recent
                            for facility in lowest_most_recent:
                                date, time, voltage = lowest_most_recent[facility]
                                message += f"{facility}: {date}, {time}, {voltage}\n"
                            self.bot.send_message(chat_id, message)
                        else:
                            self.bot.send_message(chat_id, 'За последний час нету данных.')
