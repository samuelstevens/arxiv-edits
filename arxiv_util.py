# builtin
from datetime import date
from typing import Iterator


class ArxivIDs:
    def __iter__(self):
        self.today = date.today()
        self.today_year = self.today.year % 100  # will produce 19, 20, etc.

        self.year = 7
        self.month = 4
        self.number = 1

        self.get_max_number()

        return self

    def get_max_number(self):
        if self.year < 15:
            self.max_number = 9999
            self.digits = 4
        else:
            self.max_number = 99999
            self.digits = 5

    def __next__(self):
        if self.number < self.max_number:
            self.number += 1
            return f'{self.year:02}{self.month:02}.{self.number:0{self.digits}}'
        elif self.month < 12:
            self.number = 1
            self.month += 1
            return f'{self.year:02}{self.month:02}.{self.number:0{self.digits}}'
        elif self.year < self.today_year:
            self.number = 1
            self.month = 1
            self.year += 1
            self.get_max_number()
            return f'{self.year:02}{self.month:02}.{self.number:0{self.digits}}'
        else:
            raise StopIteration

    def increment_month(self):
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1
            self.get_max_number()

        self.number = 1
