import uuid
import random
from datetime import datetime, date
from . import system_variables as sv



def generate_admission_application_id(length=10) -> str:
    return str(uuid.uuid4().hex)[:length]


def generate_password_reset_token(length=10) -> str:
    return str(uuid.uuid4().hex)[:length]

def generate_password_reset_code() -> str:
    return str(random.randint(100000, 999999))


def generate_booking_code() -> str:
    date_str = date.today().strftime("%Y%m%d")
    return f"{sv.SYSTEM_PREFIX.get('booking', 'B')}{date_str}{str(uuid.uuid4().hex)[:5]}"


def generate_guest_id() -> str:
    date_str = date.today().strftime("%Y%m%d")
    return f"{sv.SYSTEM_PREFIX.get('guest', 'G')}{date_str}{str(uuid.uuid4().hex)[:5].capitalize()}"
