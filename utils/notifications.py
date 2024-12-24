from django.core.mail import EmailMessage
from rest_framework import serializers

def send_email(*args, **kwargs):
    email = EmailMessage(
        subject=kwargs.get("subject"),
        body=kwargs.get("body"),
        from_email=kwargs.get("from_email"),
        to=kwargs.get("to_email"),
    )
    try:
        email.send()
    except Exception as e:
        raise serializers.ValidationError("email could not be sent")


def send_SMS(*args, **kwargs):
    pass
