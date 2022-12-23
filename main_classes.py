import requests

from mail_parser import get_most_recent_readings, lowest_reading, mail_receiver

CRITICAL_VALUE = {"1303": 11.3, "М-1": 11.0, "Е-1": 11.0}
ATTENTION_VALUE = {"1303": 11.5, "М-1": 11.5, "Е-1": 11.5}


class MailReaderLoop:
    def __init__(self, bot, user, password, imap_server, chat_id):
        self.bot = bot
        self.user = user
        self.password = password
        self.imap_server = imap_server
        self.chat_id = chat_id
        self.attention_sent = False
        self.critical_sent = False
        self.lowest_most_recent = None

    def __call__(self, logger):
        self.critical_sent = False
        most_recent_readings = get_most_recent_readings(
            mail_receiver(self.user, self.password, self.imap_server)
        )
        self.lowest_most_recent = lowest_reading(most_recent_readings)
        for facility, reading in self.lowest_most_recent.items():
            date, time, voltage = reading
            if voltage < CRITICAL_VALUE[facility]:
                message = f"CRITICAL на {facility} критический заряд {voltage}V на момент {date} {time}"
                self.bot.send_message(self.chat_id, message)
                self.critical_sent = True
            elif voltage < ATTENTION_VALUE[facility] and not self.attention_sent:
                message = (
                    f"ATTENTION на {facility} заряд {voltage}V на момент {date} {time}"
                )
                self.bot.send_message(self.chat_id, message)
                logger.info("ATTENTION notification sent.")
                self.attention_sent = True
        if not self.critical_sent:
            logger.info("Mail received. No critical voltages. Sleep 1 hour.")
        else:
            logger.info(
                "Mail receive. Critical voltage notification sent. Sleep 1 day."
            )
            self.attention_sent = False


class PollCommandClass:
    def __init__(self, bot, telegram_token):
        self.bot = bot
        self.offset = 0
        self.telegram_token = telegram_token

    def __call__(self, lowest_most_recent):
        response = requests.get(
            f"https://api.telegram.org/bot{self.telegram_token}/getUpdates?offset={self.offset}"
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
                    for facility in lowest_most_recent:
                        date, time, voltage = lowest_most_recent[facility]
                        message += f"{facility}: {date}, {time}, {voltage}\n"
                    self.bot.send_message(chat_id, message)
