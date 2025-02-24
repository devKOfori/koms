from celery.app import shared_task
from django.utils import timezone
from .models import ProfileShiftAssign, RoomKeepingAssign
from django.db import transaction
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@shared_task
def update_shift_status():
    """
    Updates the status of shifts that have passed.
    """
    logger.info("Task update_shift_status started")
    print("in update_shift_status")
    past_shifts = ProfileShiftAssign.objects.filter(
        # shift_end_time__lte=timezone.now(),
        date=timezone.now().date()
    )
    for shift in past_shifts:
        with transaction.atomic():
            if shift.status.change_after_expiry:
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
                    "Unfinished",
                ]:
                    assignment.change_status("Unfinished")
                    unfinished_assignments.append(assignment)
            if unfinished_assignments:
                RoomKeepingAssign.objects.bulk_update(
                    unfinished_assignments, ["current_status"]
                )
