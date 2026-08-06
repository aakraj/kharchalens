from datetime import date


def format_date(value: date) -> str:
    return value.strftime("%d-%b-%Y")