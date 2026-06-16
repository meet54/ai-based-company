"""Virtual office schedule — kept in sync with static/office.js."""

from datetime import datetime

OFFICE_OPEN = 10 * 60
OFFICE_CLOSE = 18 * 60 + 15
ENTRY_WINDOW_START = 9 * 60 + 55
ENTRY_WINDOW_END = 10 * 60 + 15
EXIT_WINDOW_START = 18 * 60 + 5
EXIT_WINDOW_END = 18 * 60 + 25
OFFICE_HOURS_LABEL = "10:00 AM – 6:15 PM"


def mins_now() -> int:
    now = datetime.now()
    return now.hour * 60 + now.minute


def is_office_open() -> bool:
    now = mins_now()
    return ENTRY_WINDOW_START <= now < OFFICE_CLOSE


def office_phase() -> str:
    now = mins_now()
    if now < ENTRY_WINDOW_START or now >= OFFICE_CLOSE:
        return "closed"
    if now < ENTRY_WINDOW_END:
        return "login"
    if now >= EXIT_WINDOW_START:
        return "logout"
    return "workday"


def closed_status_message() -> str:
    return f"Office closed — team logged out. Hours: {OFFICE_HOURS_LABEL}."
