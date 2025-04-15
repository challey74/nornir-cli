import logging
import re


def is_not_empty_string(value: str) -> bool:
    """Validate that a string is not empty after stripping whitespace."""
    return isinstance(value, str) and bool(value.strip())


def is_positive_integer(value: int) -> bool:
    """Validate that an integer is greater than 0."""
    return isinstance(value, int) and value > 0


def validate_reload_date(reload_date: str) -> bool:
    """Validate that the reload time is in the correct format"""
    reload_date = reload_date.strip().lower()
    reload_regex = re.compile(
        r"^(?P<hour>[01]\d|2[0-3]):(?P<minutes>[0-5]\d)\s(?P<day>[0-2]\d|3[01])\s(?P<month>jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)$"
    )

    match = reload_regex.match(reload_date)

    if match:
        if day := match.group("day"):
            day = int(day)
            month = match.group("month")
            if not month:
                logging.error(
                    "Invalid reload command."
                    "Please specify month with 3 letter month abbreviation."
                )
                return False
            if day > 31:
                logging.error("Invalid reload command. %s exceeded days in month", day)
                return False
            if month in ["apr", "jun", "sep", "nov"] and day > 30:
                logging.error("Invalid reload command. %s exceeded days in month", day)
                return False
            elif month == "feb" and day > 29:
                logging.error("Invalid reload command. %s exceeded days in month", day)
                return False

        return True
    else:
        logging.error("Invalid reload command. Format should be HH:MM DD MMM")
        return False
