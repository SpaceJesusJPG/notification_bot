import os

from dotenv import load_dotenv

from mail_parser import get_most_recent_readings, lowest_reading, mail_receiver

load_dotenv()
USER = os.getenv("MAILBOX")
PASSWORD = os.getenv("PASSWORD")
IMAP_SERVER = "mail.emsd.ru"
CRITICAL_VALUE = {"1303": 11.0, "М-1": 11.0, "Е-1": 11.0}


if __name__ == "__main__":
    most_recent_readings = get_most_recent_readings(
        mail_receiver(USER, PASSWORD, IMAP_SERVER)
    )
    lowest_most_recent = lowest_reading(most_recent_readings)
