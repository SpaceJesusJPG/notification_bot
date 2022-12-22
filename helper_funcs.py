def remove_all_before(items, border):
    try:
        return items[items.index(border) + 1:None:1]
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
                voltages.append([date, time, float(voltage.replace(",", "."))])
    return voltages
