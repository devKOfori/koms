from celery.app import shared_task
from django.utils import timezone
from .models import ProfileShiftAssign, ShiftStatus, RoomKeepingAssign
from datetime import timedelta
from django.db import transaction
from celery import Celery


@shared_task
def update_shift_status():
    """
    Updates the status of shifts that have passed.
    """
    print("in update_shift_status")
    past_shifts = ProfileShiftAssign.objects.filter(shift_end_time__lte=timezone.now())
    for shift in past_shifts:
        with transaction.atomic():
            shift.change_status("Expired")
            shift.save()
            unfinished_assignments = []
            for assignment in shift.room_keeping_assignments.all():
                if assignment.current_status not in [
                    "Ended",
                    "Completed",
                    "Confirmed",
                    "Faulty",
                    "Cancelled",
                ]:
                    assignment.change_status("Unfinished")
                    unfinished_assignments.append(assignment)
            if unfinished_assignments:
                RoomKeepingAssign.objects.bulk_update(
                    unfinished_assignments, ["current_status"]
                )
