import email
import imaplib
from functools import reduce

from helper_funcs import parse_message_list

FACILITIES = {"kedrdm033": "1303", "kedrdm032": "Е-1", "kedrdm030": "М-1"}


def mail_receiver(user, password, imap_server):
    imap = imaplib.IMAP4_SSL(imap_server)
    imap.login(user, password)
    imap.select("Inbox")
    unseen = imap.search(None, '(SUBJECT "kedrdm_data")', "UNSEEN")[1][0].split()
    messages = {msg: imap.fetch(msg, "(RFC822)")[1] for msg in unseen}
    result = {}
    for message_id, message in messages.items():
        msg = email.message_from_bytes(message[0][1])
        facility = msg["From"].split("@")[0]
        result.setdefault(facility, []).append(msg)
    return result


def get_most_recent_readings(kedr_messages):
    result = {}
    for facility, msg_lst in kedr_messages.items():
        voltages = parse_message_list(msg_lst)
        result.setdefault(FACILITIES[facility], []).extend(voltages)
    return result


def lowest_reading(most_recent_readings):
    result = {}
    for facility, readings in most_recent_readings.items():
        lowest = reduce(lambda x, y: x if x[2] < y[2] else y, readings)
        result[facility] = lowest
    return result
