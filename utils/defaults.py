from django.apps import apps

def get_room_status_default():
    RoomStatus = apps.get_model('api', 'RoomStatus')
    default_room_status, _ = RoomStatus.objects.get_or_create(name='Default Room Status')
    return default_room_status

def get_sponsor_type_default():
    SponsorType = apps.get_model('api', 'SponsorType')
    default_sponsor_type, _ = SponsorType.objects.get_or_create(name='Default Sponsor Type')
    return default_sponsor_type

def get_sponsor_default():
    Sponsor = apps.get_model('api', 'Sponsor')
    default_sponsor, _ = Sponsor.objects.get_or_create(name='Self')
    return default_sponsor

def get_payment_type_default():
    PaymentType = apps.get_model('api', 'PaymentType')
    default_payment_type, _ = PaymentType.objects.get_or_create(name='Self')
    return default_payment_type

def get_table_default(table:str):
    match table.casefold():
        case 'roomstatus':
            return get_room_status_default()
        case 'sponsortype':
            return get_sponsor_type_default()
        case 'paymenttype':
            return get_payment_type_default()
       