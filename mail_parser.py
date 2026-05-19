import email
import imaplib
from functools import reduce

from helper_funcs import parse_message_list, read_message

FACILITIES = {"kedrdm033": "1303", "kedrdm032": "Е-1", "kedrdm030": "М-1"}


def mail_receiver(user, password, imap_server):
    imap = imaplib.IMAP4_SSL(imap_server)
    imap.login(user, password)
    imap.select("Inbox")
    result = {}
    for facility in FACILITIES.keys():
        _, message_numbers = imap.sort(
            'REVERSE DATE',
            "UTF-8",
            f'(FROM "{facility}@kedrdm.khv.ru")'
        )
        _, msg_data = imap.fetch(message_numbers[0].split()[0], "(RFC822)")
        email_message = email.message_from_bytes(msg_data[0][1])
        result[FACILITIES[facility]] = email_message
    return result


def get_most_recent_readings(kedr_messages):
    result = {}
    for facility, msg_lst in kedr_messages.items():
        voltages = parse_message_list(msg_lst)
        result.setdefault(facility, []).extend(voltages)
    return result


def lowest_reading(most_recent_readings):
    result = {}
    for facility, readings in most_recent_readings.items():
        lowest = reduce(lambda x, y: x if x[2] < y[2] else y, readings)
        result[facility] = lowest
    return result
