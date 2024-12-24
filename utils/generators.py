import uuid


def generate_admission_application_id(length=10) -> str:
    return str(uuid.uuid4().hex)[length]


def generate_password_reset_token(length=10) -> str:
    return str(uuid.uuid4().hex)[length]
