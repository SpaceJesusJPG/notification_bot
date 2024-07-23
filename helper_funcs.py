import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


def remove_all_before(items, border):
    try:
        return items[items.index(border) + 1 : None : 1]
    except ValueError:
        return items


def read_message(msg):
    for payload in msg.walk():
        if payload.get_content_type().lower() == "text/plain":
            result = remove_all_before(payload.get_payload().split("\r\n"), "DATA:")
            return result


def parse_message_list(msg_lst):
    voltages = []
    for msg in msg_lst:
        for reading in read_message(msg):
            if reading:
                split_reading = reading.split()
                date, time, voltage = (
                    split_reading[1],
                    split_reading[2],
                    split_reading[10],
                )
                voltages.append(
                    [date, time, round(Decimal(voltage.replace(",", ".")), 2)]
                )
    return voltages


# def check_response(response):
#    result = response.json()["result"]
#        if "message" in first_update:
#            text = first_update["message"]["text"].split()
#            chat_id = first_update["message"]["chat"]["id"]
#            if "/voltage" in text:


# class ServiceUnavailable(Exception):
#    def __init__(self, message: str):
#        self.message = message


# async def make_request(url: str, method: str, data: dict[str, Any] = None) -> Any:
#    retries = 0
#    while retries < 3:
#        retries += 1
#        async with AsyncClient() as client:
#            try:
#                response = await client.request(url=url, method=method, data=data)
#            except Exception as exc:
#                logger.error(f"Error: {type(exc)}: {exc}\nattempt: {retries}...")
#                await asyncio.sleep(5.0)
#            return response
#
#    raise ServiceUnavailable(f"{method.upper()} request failed")
