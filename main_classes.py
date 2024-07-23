import time as tm

import requests

from mail_parser import get_most_recent_readings, lowest_reading, mail_receiver

CRITICAL_VALUE = {"1303": 11.0, "М-1": 10.8, "Е-1": 11.0}
ATTENTION_VALUE = {"1303": 11.2, "М-1": 11.2, "Е-1": 11.2}


class MailHandlerLoop:
    def __init__(self, bot, logger, user, password, imap_server, chat_ids):
        self.last_active_ns = 0
        self.last_reading = None
        self.bot = bot
        self.user = user
        self.password = password
        self.imap_server = imap_server
        self.chat_ids = chat_ids
        self.attention_sent = False
        self.critical_sent = False
        self.lowest_most_recent = None
        self.logger = logger
        self.not_active_sent = False
        self.fail_state = None

    def email_reader(self):
        while True:
            start = tm.perf_counter()
            most_recent_readings = get_most_recent_readings(
                mail_receiver(self.user, self.password, self.imap_server)
            )
            self.lowest_most_recent = lowest_reading(most_recent_readings)
            self.logger.info("Mail received.")
            delay = tm.perf_counter() - start
            tm.sleep(3600 - delay)

    def status_notification_sender(self, ssh):
        while True:
            if self.not_active_sent:
                con = ssh.connect()
                if con[0] is False:
                    tm.sleep(3600)
                    continue
                if self.fail_state == "status":
                    status, reading = ssh.get_status()
                    if (
                        status["ActiveState"] != "active"
                        or status["CPUUsageNSec"] == self.last_active_ns
                    ):
                        ssh.close()
                        tm.sleep(3600)
                        continue
                elif self.fail_state == "reading":
                    status, reading = ssh.get_status()
                    if reading == self.last_reading:
                        ssh.close()
                        tm.sleep(3600)
                        continue
                self.not_active_sent = False
                self.logger.info(
                    f"Connection to the {ssh.verbose_name} has been restored."
                )
                for chat_id in self.chat_ids:
                    self.bot.send_message(
                        chat_id, f"Связь с объектом {ssh.verbose_name} восстановилась."
                    )
                ssh.close()
            tm.sleep(5)
            start = tm.perf_counter()
            self.not_active_sent = False
            con = ssh.connect()
            if con[0] is True:
                status, reading = ssh.get_status()
                if (
                    status["ActiveState"] != "active"
                    or status["CPUUsageNSec"] == self.last_active_ns
                ):
                    self.logger.info(
                        f"Site {ssh.verbose_name} is in trouble, program is not active"
                    )
                    for chat_id in self.chat_ids:
                        self.bot.send_message(
                            chat_id,
                            f"Активность программы на объекте {ssh.verbose_name} не обнаружена.",
                        )
                    self.not_active_sent = True
                    self.fail_state = "status"
                elif reading == self.last_reading:
                    self.logger.info(
                        f"Site {ssh.verbose_name} is in trouble, program is not writing data"
                    )
                    for chat_id in self.chat_ids:
                        self.bot.send_message(
                            chat_id,
                            f"Данные на объкте {ssh.verbose_name} не менялись последние 10 минут",
                        )
                    self.not_active_sent = True
                    self.fail_state = "reading"
                else:
                    self.logger.info(
                        f"Site {ssh.verbose_name} is active, sleep 30 mins."
                    )
                    delay = tm.perf_counter() - start
                    tm.sleep(1795 - delay)
                ssh.close()
            else:
                self.logger.info(
                    f"No connection to {ssh.verbose_name}, reason: {con[1]}"
                )
                for chat_id in self.chat_ids:
                    self.bot.send_message(
                        chat_id, f"С объектом {ssh.verbose_name} нет связи, {con[1]}."
                    )
                self.not_active_sent = True

    def voltage_notification_sender(self):
        while True:
            tm.sleep(5)
            start = tm.perf_counter()
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
                delay = tm.perf_counter() - start
                tm.sleep(3595 - delay)
            else:
                self.logger.info("Critical voltage notification sent. Sleep 1 day.")
                self.attention_sent = False
                delay = tm.perf_counter() - start
                tm.sleep(86395 - delay)


class PollCommandClass:
    def __init__(self, bot, telegram_token):
        self.bot = bot
        self.offset = 0
        self.telegram_token = telegram_token

    def __call__(self, loop, ssh):
        while True:
            try:
                with requests.get(
                    f"https://api.telegram.org/bot{self.telegram_token}/getUpdates?timeout=240&offset={self.offset}"
                ) as response:
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
                                        date, time, voltage = lowest_most_recent[
                                            facility
                                        ]
                                        message += (
                                            f"{facility}: {date}, {time}, {voltage}\n"
                                        )
                                    self.bot.send_message(chat_id, message)
                                else:
                                    self.bot.send_message(
                                        chat_id, "За последний час нет данных."
                                    )
                            if "/1303" in text:
                                ssh["1303"].connect()
                                status, last_data = ssh["1303"].get_status()
                                ssh["1303"].close()
                                self.bot.send_message(
                                    chat_id,
                                    f'Состояние: {status["ActiveState"]}, последние данные: {last_data}',
                                )
            except Exception:
                tm.sleep(60)
