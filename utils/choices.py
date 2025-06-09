ROOM_MAINTENANCE_STATUS_CHOICES = [
    ("in-use", "In Use"),
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

USER_CATEGORY_CHOICES = [
    ("staff", "Staff"),
    ("guest", "Guest"),
]

BOOKING_SOURCE_CHOICES = [
    ("walk-in", "Walk-in"),
    ("online", "Online"),
    ("phone", "Phone"),
    ("email", "Email"),
    ("travel-agency", "Travel Agency"),
    ("corporate", "Corporate"),
    ("other", "Other"),
]

BOOKING_STATUS_CHOICES = [
    ("confirmed", "Confirmed"),
    ("cancelled", "Cancelled"),
    ("checked-in", "Checked In"),
    ("checked-out", "Checked Out"),
    ("no-show", "No Show"),
    ("pending", "Pending"),
]

PAYMENT_STATUS_CHOICES = [
    ("paid", "Paid"),
    ("unpaid", "Unpaid"),
    ("partially-paid", "Partially Paid"),
    ("refunded", "Refunded"),
]

BOOKING_CATEGORY_CHOICES = [
    ("individual", "Individual"),
    ("corporate", "Corporate"),
    ("ngo", "NGO"),
    ("group", "Group"),
    ("event", "Event"),
    ("long-term", "Long Term"),
]