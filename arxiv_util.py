# builtin
from datetime import date
from typing import Iterator


def get_max_number(year):
    if year < 15:
        return (9999, 4)

    return(99999, 5)


def arxiv_ids() -> Iterator[str]:
    today = date.today()
    today_year = today.year % 100  # will produce 19, 20, etc.

    year = 7
    month = 4
    number = 1

    max_number, digits = get_max_number(year)

    while year <= today_year:
        while month <= 12:
            while number < max_number:
                yield f'{year:02}{month:02}.{number:0{digits}}'
                number += 1
            month += 1
            number = 1
            max_number, digits = get_max_number(year)
        year += 1
        month = 1
