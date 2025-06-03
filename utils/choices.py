ROOM_MAINTENANCE_STATUS_CHOICES = [
    ("default", "Default"),
    ("cleaned", "Cleaned"),
    ("under-maintenance", "Under-maintenance"),
    ("broken", "Broken"),
]

ROOM_BOOKING_STATUS_CHOICES = [
    ("default", "default"),
    ("booked", "booked"),
    ("empty", "empty"),
    ("unavailable", "unavailable"),
]

PASSWORD_RESET_CHANNEL_CHOICES = [("email", "Email"), ("sms", "SMS")]

GENDER_CHOICES = [("female", "Female"), ("male", "Male")]

RATE_TYPE_CHOICES = [("member", "Member"), ("non-member", "Non-Member")]

RECEIPT_STATUS_CHOICES = [("activated", "Activated"), ("deactivated", "Deactivated")]

ASSIGN_COMPLAINT_STATUS_CHOICES = [
    ("department", "Transfer to Department"),
    ("staff", "Transfer to Staff"),
    ("resolved", "Resolved"),
    (None, "Default"),
]
