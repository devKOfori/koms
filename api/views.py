from django.shortcuts import render
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework import exceptions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from . import serializers as api_serializers
from . import models
from django.db.models import Q
from django.db import transaction
from utils import helpers
from rest_framework.decorators import api_view
from datetime import datetime
from django.utils import timezone
from rest_framework_simplejwt.views import TokenBlacklistView
from rest_framework.mixins import UpdateModelMixin, DestroyModelMixin
from . import custom_permissions
from .mixins import CreatedByMixin

# Create your views here.

class UpdateDeleteView(UpdateModelMixin, DestroyModelMixin, generics.GenericAPIView):
    def patch(self, request, *args, **kwargs):
        self.check_object_permissions(request, self.get_object())
        return self.partial_update(request, *args, **kwargs)
    
    def put(self, request, *args, **kwargs):
        self.check_object_permissions(request, self.get_object())
        return self.update(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        self.check_object_permissions(request, self.get_object())
        return self.destroy(request, *args, **kwargs)

class RegisterAccountView(generics.ListCreateAPIView):
    queryset = models.Profile.objects.all()
    serializer_class = api_serializers.CustomUserProfileSerializer

    def get_serializer_context(self):
        try:
            user_profile = models.Profile.objects.get(user=self.request.user)
        except models.Profile.DoesNotExist:
            return Response(
                {"error": "User not authenticated"}, status=status.HTTP_400_BAD_REQUEST
            )
        context = super().get_serializer_context()
        context["user_profile"] = user_profile
        return context

class AddUserProfileView(generics.CreateAPIView):
    queryset = models.Profile.objects.all()
    serializer_class = api_serializers.CustomUserProfileSerializer
    permission_classes = [IsAuthenticated, custom_permissions.IsAdmin | custom_permissions.IsDepartmentExec, custom_permissions.IsAddingProfileToOwnDepartment]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.user.is_authenticated:
            try:
                profile = models.Profile.objects.get(user=self.request.user)
                context["created_by"] = profile
            except models.Profile.DoesNotExist:
                raise serializers.ValidationError({"error": "user account has no profile"})
        return context

class UserRolesCreateView(generics.CreateAPIView):
    serializer_class = api_serializers.ProfileRolesSerializer
    permission_classes = [IsAuthenticated, custom_permissions.IsAdmin | custom_permissions.IsDepartmentExec]

    def get_queryset(self):
        profile_id = self.kwargs.get("pk")
        user_profile = get_object_or_404(models.Profile, id=profile_id)
        queryset = models.ProfileRole.objects.filter(profile=user_profile)
        return queryset
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["profile_id"] = self.kwargs.get("pk")  
        if self.request.user.is_authenticated:
            try:
                created_by = models.Profile.objects.get(user=self.request.user)
                context["created_by"] = created_by
            except models.Profile.DoesNotExist:
                raise serializers.ValidationError({"error": "user account has no profile"})
        return context
    
class UserRolesListView(generics.ListAPIView):
    serializer_class = api_serializers.ProfileRolesSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        profile_id = self.kwargs.get("pk")
        user_profile = get_object_or_404(models.Profile, id=profile_id)
        queryset = models.ProfileRole.objects.filter(profile=user_profile)
        return queryset

class UserProfileDetailView(generics.RetrieveAPIView):
    serializer_class = api_serializers.ProfileViewSerializer
    lookup_url_kwarg = "pk"

    def get_queryset(self):
        return models.Profile.objects.prefetch_related("roles")
    
class AccountChangeView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Profile.objects.all()
    print("Custom serializer is being used!")
    serializer_class = api_serializers.CustomUserProfileSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = api_serializers.CustomTokenObtainPairSerializer

class LogoutView(TokenBlacklistView):
    serializer_class = api_serializers.TokenBlacklistSerializer

class LogoutView2(APIView):
    def post(self, request):
        print("Raw request data:", request.body)  # Check raw request body
        print("Parsed request data:", request.data)  # Debugging

        try:
            refresh = request.data.get("refresh")
            token = RefreshToken(refresh)
            print(token)
            token.blacklist()
            return Response(
                {"detail": "refresh token blacklisted"},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": "an error occured while blacklisting the refresh token"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
class LogoutView3(APIView):
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if refresh_token:
            print(refresh_token)
            try:
                # token = RefreshToken(refresh_token)
                # token.blacklist()
                return Response(
                    {"detail": "refresh token blacklisted"},
                    status=status.HTTP_200_OK,
                )
            except Exception as e:
                return Response(
                    {"error": "an error occured while blacklisting the refresh token"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            user: models.CustomUser = request.user
            _ = request.user.profile

            old_password = request.data.get("old_password")
            new_password = request.data.get("new_password", None)
            confirm_new_password = request.data.get("confirm_new_password", None)

            if not user.check_password(old_password):
                return Response(
                        {"error": "The old password is incorrect"},
                        status=status.HTTP_400_BAD_REQUEST,
                )

            if not new_password or not confirm_new_password:
                return Response(
                    {"error": "new password and confirm new password are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if new_password != confirm_new_password:
                return Response(
                    {"error": "new password and confirm new password do not match"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not helpers.is_valid_password(new_password):
                return Response(
                    {
                        "error": "password not valid"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.set_password(new_password)
            user.save()
            return Response(
                {"detail": "password changed successfully"},
                status=status.HTTP_200_OK,
            )
        except models.Profile.DoesNotExist:
            return Response(
                {"error": "user profile does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )

class MyDepartmentStaffList(generics.ListAPIView):
    serializer_class = api_serializers.CustomUserProfileSerializer

    def get_queryset(self):
        try:
            user_profile = models.Profile.objects.get(user=self.request.user)
            department = user_profile.department
        except models.Profile.DoesNotExist:
            raise exceptions.ValidationError({"error": "user account not found"})
        return models.Profile.objects.filter(department=department)

class BedTypeCreateView(CreatedByMixin, generics.CreateAPIView):
    queryset = models.BedType.objects.all()
    serializer_class = api_serializers.BedTypeSerializer
    permission_classes = [custom_permissions.IsHouseKeepingStaff | custom_permissions.IsAdmin, custom_permissions.IsDepartmentExec]

class BedTypeListView(generics.ListAPIView):
    queryset = models.BedType.objects.all()
    serializer_class = api_serializers.BedTypeSerializer
    permission_classes = [IsAuthenticated]

class BedTypeUpdateDeleteView(UpdateDeleteView):
    queryset = models.BedType.objects.all()
    serializer_class = api_serializers.BedTypeSerializer
    lookup_url_kwarg = "pk"
    permission_classes = [custom_permissions.IsHouseKeepingStaff | custom_permissions.IsAdmin, custom_permissions.IsDepartmentExec]

class BedTypeDetail(generics.RetrieveAPIView):
    queryset = models.BedType.objects.all()
    serializer_class = api_serializers.BedTypeSerializer
    lookup_url_kwarg = "pk"
    permission_classes = [IsAuthenticated]

class PasswordResetView(generics.CreateAPIView):
    queryset = models.PasswordReset.objects.all()
    serializer_class = api_serializers.PasswordResetSerializer

class CompletePasswordResetView(APIView):
    def post(self, request, *args, **kwargs):
        """
        Complete the password reset process by validating the token and updating the user's password.
        """
        reset_id = request.data.get("reset_id")
        filter = Q(reset_code=reset_id) | Q(reset_token=reset_id)
        try:
            password_reset: models.PasswordReset = models.PasswordReset.objects.get(filter)
            if password_reset.is_used or password_reset.expiry_date < timezone.now():
                return Response(
                    {"error": "This reset link has expired or has already been used."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            new_password = request.data.get("new_password")
            confirm_new_password = request.data.get("confirm_new_password")
            if not new_password or not confirm_new_password:
                return Response(
                    {"error": "new password and confirm new password are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if new_password != confirm_new_password:
                return Response(
                    {"error": "new password and confirm new password do not match"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not helpers.is_valid_password(new_password):
                return Response(
                    {
                        "error": "password not valid"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            with transaction.atomic():
                user = password_reset.user
                user.set_password(new_password)
                user.save()
                password_reset.is_used = True
                password_reset.save()
                models.PasswordReset.objects.filter(user=user, is_used=False).update(is_used=True)
                return Response(
                    {"detail": "Password reset successful"},
                    status=status.HTTP_200_OK,
                )
        except models.PasswordReset.DoesNotExist:
            return Response(
                {"error": "Invalid reset ID"},
                status=status.HTTP_400_BAD_REQUEST,
            )

class ProfileList(generics.ListCreateAPIView):
    queryset = models.Profile.objects.all()
    serializer_class = api_serializers.CustomUserProfileSerializer

class ProfileDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Profile.objects.all()
    serializer_class = api_serializers.CustomUserProfileSerializer
    lookup_url_kwarg = "pk"

class RoleList(generics.ListCreateAPIView):
    queryset = models.Role.objects.all()
    serializer_class = api_serializers.RoleSerializer
    permission_classes = [custom_permissions.IsAdminProfileOrReadOnly]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.user.is_authenticated:
            profile = get_object_or_404(models.Profile, user=self.request.user)
            context["created_by"] = profile
        return context

class RoleDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Role.objects.all()
    serializer_class = api_serializers.RoleSerializer
    lookup_url_kwarg = "pk"
    permission_classes = [custom_permissions.IsAdminProfileOrReadOnly]

class DepartmentList(generics.ListCreateAPIView):
    queryset = models.Department.objects.all()
    serializer_class = api_serializers.DepartmentSerializer
    permission_classes = [custom_permissions.IsAdminProfileOrReadOnly]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.user.is_authenticated:
            try:
                profile = models.Profile.objects.get(user=self.request.user)
                context["created_by"] = profile
            except models.Profile.DoesNotExist:
                raise serializers.ValidationError({"error": "user account has no profile"})
        return context
    
class DepartmentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Department.objects.all()
    serializer_class = api_serializers.DepartmentSerializer
    lookup_url_kwarg = "pk"
    permission_classes = [custom_permissions.IsAdminProfileOrReadOnly]

class CountryList(generics.ListAPIView):
    queryset = models.Country.objects.all()
    serializer_class = api_serializers.CountrySerializer
    permission_classes = [IsAuthenticated]

class CountryCreateView(CreatedByMixin, generics.CreateAPIView):
    queryset = models.Country.objects.all()
    serializer_class = api_serializers.CountrySerializer
    permission_classes = [custom_permissions.IsAdmin | custom_permissions.IsFrontDeskStaff]
    
class CountryUpdateDeleteView(UpdateDeleteView):
    queryset = models.Country.objects.all()
    serializer_class = api_serializers.CountrySerializer
    lookup_url_kwarg = "pk"
    permission_classes = [custom_permissions.IsAdmin | custom_permissions.IsFrontDeskStaff]

class CountryRetrieveView(generics.RetrieveAPIView):
    queryset = models.Country.objects.all()
    serializer_class = api_serializers.CountrySerializer
    lookup_url_kwarg = "pk"
    permission_classes = [IsAuthenticated]

class CustomUpdateView(APIView):
    def put(self, request, *args, **kwargs):
        serializer = api_serializers.CustomUserProfileSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ShiftList(generics.ListCreateAPIView):
    queryset = models.Shift.objects.all()
    serializer_class = api_serializers.ShiftSerializer

class ShiftStatusList(generics.ListCreateAPIView):
    queryset = models.ShiftStatus.objects.all()
    serializer_class = api_serializers.ShiftStatusSerializer

class IdentificationTypeList(generics.ListCreateAPIView):
    queryset = models.IdentificationType.objects.all()
    serializer_class = api_serializers.IdentificationTypeSerializer

class ShiftNoteList(generics.ListCreateAPIView):
    serializer_class = api_serializers.ShiftNoteSerializer

    def get_queryset(self):
        shift_id = self.kwargs.get("pk")
        return models.ShiftNote.objects.filter(assigned_shift=shift_id)

    def get_serializer_context(self):
        try:
            user_profile = models.Profile.objects.get(user=self.request.user)
        except models.Profile.DoesNotExist:
            return Response(
                {"error": "User not authenticated"}, status=status.HTTP_400_BAD_REQUEST
            )
        context = super().get_serializer_context()
        context["created_by"] = user_profile
        context["last_modified_by"] = user_profile
        return context

class ShiftNoteDetail(generics.RetrieveUpdateDestroyAPIView):

    queryset = models.ShiftNote.objects.all()
    serializer_class = api_serializers.ShiftNoteSerializer
    lookup_url_kwarg = "note_id"

    def get_serializer_context(self):
        try:
            user_profile = models.Profile.objects.get(user=self.request.user)
        except models.Profile.DoesNotExist:
            return Response(
                {"error": "User not authenticated"}, status=status.HTTP_400_BAD_REQUEST
            )
        context = super().get_serializer_context()
        context["last_modified_by"] = user_profile
        return context

class ProfileShiftAssignList(generics.ListCreateAPIView):
    queryset = models.ProfileShiftAssign.objects.all()
    serializer_class = api_serializers.ProfileShiftAssignSerializer

    def get_queryset(self):
        user_profile = models.Profile.objects.get(user=self.request.user)
        queryset = models.ProfileShiftAssign.objects.filter(
            created_by__department=user_profile.department
        )
        shift_date = self.request.GET.get("shift_date", None)
        shift_name = self.request.GET.get("shift", None)
        # print(shift_name)
        exclude_inactive_shifts = self.request.GET.get("exclude_inactive_shifts", False)
        # print(f"Exclude Inactive Shifts: {type(exclude_inactive_shifts)}")
        # department = self.request.GET.get("department", None)
        # print(queryset.count())
        if shift_date:
            queryset = queryset.filter(date=shift_date)
            print(queryset.count())
        if shift_name:
            queryset = queryset.filter(shift__name=shift_name)
            # print(queryset.count())
        # if department:
        #     print(f"Department: {department}")
        #     queryset = queryset.filter(department__name=department)
        if exclude_inactive_shifts and exclude_inactive_shifts == "true":
            queryset = queryset.exclude(status__name__in=["Ended", "Cancelled"])
        # print(queryset.count())
        # print(queryset)
        return queryset

def clear_shift_assignments(request):
    print(request.GET)
    shift_date = request.GET.get("shift_date")
    shift = request.GET.get("shift")
    if not shift_date or not shift:
        return Response(
            {"error": "shift date and shift are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    models.ProfileShiftAssign.objects.filter(date=shift_date, shift=shift).delete()
    return Response({"detail": "shift assignments cleared"}, status=status.HTTP_200_OK)

class MyShiftList(generics.ListAPIView):
    serializer_class = api_serializers.MyShiftSerializer

    def get_queryset(self):
        user_profile = models.Profile.objects.get(user=self.request.user)
        return models.ProfileShiftAssign.objects.filter(profile=user_profile)

class ProfileShiftAssignCreateView(generics.ListCreateAPIView):
    queryset = models.ProfileShiftAssign.objects.all()
    serializer_class = api_serializers.ProfileShiftAssignSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        try:
            context["created_by"] = models.Profile.objects.get(user=self.request.user)
            return context
        except models.Profile.DoesNotExist:
            raise serializers.ValidationError({"error": "user account has no profile"})

class ProfileShiftAssignUpdateView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.ProfileShiftAssign.objects.all()
    serializer_class = api_serializers.ProfileShiftAssignSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        try:
            context["modified_by"] = models.Profile.objects.get(user=self.request.user)
            return context
        except models.Profile.DoesNotExist:
            raise serializers.ValidationError({"error": "user account has no profile"})

# add login required decorator
@api_view(["POST"])
def update_assigned_shift_status(request, pk):
    print(request.POST)
    req_status = request.POST.get("status")

    if not status:
        return Response(
            {"error": "status is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        assigned_shift = models.ProfileShiftAssign.objects.get(id=pk)
        shift_status = models.ShiftStatus.objects.get(name=req_status)
    except models.ProfileShiftAssign.DoesNotExist:
        return Response(
            {"error": "assigned shift not found"}, status=status.HTTP_400_BAD_REQUEST
        )
    except models.ShiftStatus.DoesNotExist:
        return Response(
            {"error": "shift status not found"}, status=status.HTTP_400_BAD_REQUEST
        )
    if not assigned_shift.profile == request.user.profile:
        return Response(
            {"error": "you are not authorized to update this shift status"},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    assigned_shift.status = shift_status
    assigned_shift.save()
    return Response(
        {"detail": "assigned shift status updated"}, status=status.HTTP_200_OK
    )

class UpdateAssignedShiftStatus(APIView):
    def post(self, request, pk):
        process_status = request.data.get("status")
        if not process_status:
            return Response(
                {"error": "status is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            assigned_shift = models.ProfileShiftAssign.objects.get(id=pk)
            shift_status = models.ShiftStatus.objects.get(name=process_status)
        except models.ProfileShiftAssign.DoesNotExist:
            return Response(
                {"error": "assigned shift not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except models.ShiftStatus.DoesNotExist:
            return Response(
                {"error": "shift status not found"}, status=status.HTTP_400_BAD_REQUEST
            )
        if not assigned_shift.profile == request.user.profile:
            return Response(
                {"error": "you are not authorized to update this shift status"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if assigned_shift.status.name == "Ended":
            return Response(
                {"error": "this shift has already ended"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if (
            assigned_shift.shift_end_time
            and assigned_shift.shift_end_time < timezone.now()
        ):
            return Response(
                {"error": "this shift has already ended"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        assigned_shift.status = shift_status
        assigned_shift.last_modified_by = request.user.profile
        if process_status == "Started":
            assigned_shift.time_started = datetime.now()
        elif process_status == "Ended":
            assigned_shift.time_ended = datetime.now()
        assigned_shift.save()
        return Response(
            {"detail": "assigned shift status updated"}, status=status.HTTP_200_OK
        )

class RoomKeepingAssignCreate(generics.ListCreateAPIView):
    queryset = models.RoomKeepingAssign.objects.all()
    serializer_class = api_serializers.RoomKeepingAssignSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        print(f"Queryset Total: {queryset.count()}")
        shift_id = self.request.GET.get("shiftId", None)
        employee_name = self.request.GET.get("employeeName", None)
        shift_name = self.request.GET.get("shiftName", None)
        room_number = self.request.GET.get("roomNumber", None)
        current_status = self.request.GET.get("status", None)
        priority = self.request.GET.get("priority", None)
        assigned_on = self.request.GET.get("assignedOn", None)
        user_tasks_only = self.request.GET.get("userTasksOnly", None)
        print(f"Shift ID: {shift_id}")
        print(f"Employee Name: {employee_name}")
        print(f"Room Number: {room_number}")
        print(f"Current Status: {current_status}")
        print(f"Priority: {priority}")
        print(f"Assigned On: {assigned_on}")
        if shift_id:
            queryset = queryset.filter(member_shift=shift_id)
            print(f"Queryset Total: {queryset.count()}")
        if employee_name:
            queryset = queryset.filter(
                Q(assigned_to__full_name__icontains=employee_name)
            )
        if shift_name:
            queryset = queryset.filter(shift__name=shift_name)
            print(f"Queryset Total after shift name: {queryset.count()}")
        if room_number:
            queryset = queryset.filter(room__room_number__iexact=room_number)
            print(f"Queryset Total after room #: {queryset.count()}")
        if current_status:
            queryset = queryset.filter(current_status=current_status)
            print(f"Queryset Total after current status: {queryset.count()}")
        if priority:
            queryset = queryset.filter(priority__name=priority)
            print(f"Queryset Total after priority: {queryset.count()}")
        if assigned_on:
            queryset = queryset.filter(assignment_date=assigned_on)
            print(f"Queryset Total after assigned on: {queryset.count()}")
        if user_tasks_only:
            queryset = queryset.filter(assigned_to=self.request.user.profile)
            print(f"Queryset Total after user tasks only: {queryset.count()}")
        return queryset

    def get_serializer_context(self):
        try:
            profile = models.Profile.objects.get(user=self.request.user)
        except models.Profile.DoesNotExist:
            return Response(
                {"error": "user profile does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        context = super().get_serializer_context()
        context["created_by"] = profile
        return context

class RoomKeepingAssignUpdate(generics.UpdateAPIView):
    queryset = models.RoomKeepingAssign.objects.all()
    serializer_class = api_serializers.RoomKeepingAssignSerializer

    def get_serializer_context(self):
        try:
            profile = models.Profile.objects.get(user=self.request.user)
        except models.Profile.DoesNotExist:
            return Response(
                {"error": "user profile does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        context = super().get_serializer_context()
        context["modified_by"] = profile
        return context

class UpdateRoomKeepingStatus(APIView):
    def post(self, request, pk):
        print(request.user.profile)
        process_status = request.data.get("status")
        print(f"process_status {process_status}")
        if not process_status:
            return Response(
                {"error": "status is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            room_keeping_assign = models.RoomKeepingAssign.objects.get(id=pk)
            print(f"Room Keeping Assign Profile: {room_keeping_assign.assigned_to}")
            print(f"current status {room_keeping_assign.current_status}")
            room_keeping_status = models.HouseKeepingState.objects.get(
                name=process_status
            )
        except models.RoomKeepingAssign.DoesNotExist:
            return Response(
                {"error": "room keeping assign not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except models.HouseKeepingState.DoesNotExist:
            return Response(
                {"error": "room keeping status not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not room_keeping_assign.assigned_to == request.user.profile:
            return Response(
                {"error": "you are not authorized to update this room keeping status"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if room_keeping_assign.current_status == process_status:
            return Response(
                {"error": "this room keeping task is already in this status"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if (
            room_keeping_assign.shift_period_ended
            or room_keeping_assign.member_shift.status.name == "Ended"
        ):
            return Response(
                {"error": "the shift period has expired or shift is ended"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if room_keeping_assign.member_shift.status.name == "Started":
            return Response(
                {"error": "the shift has not started yet"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not request.user.profile.has_role("Supervisor") and (
            process_status
            not in [
                "Ongoing",
                "Ended",
                "Request Help",
            ]
            # not in models.HouseKeepingState.objects.filter(
            #     allow_only_managers=False
            # ).values_list("name", flat=True)
        ):
            return Response(
                {
                    "error": "only Started, Ended or Requested-for-Help status is allowed"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        # if room_keeping_assign.current_status == "Ended" and (process_status in models.HouseKeepingState.objects.filter(allow_after_task_is_ended=False).values_list("name", flat=True)):
        if room_keeping_assign.current_status == "Ended" and (
            process_status
            in [
                "Request Help",
                "Ongoing",
            ]
        ):
            return Response(
                {"error": "this room keeping task has already ended"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        print(f"is started: {room_keeping_assign.is_started}")
        if not room_keeping_assign.is_started and not process_status == "Ongoing":
            # if not helpers.check_profile_role(
            #     profile=request.user.profile, role_name="Supervisor"
            # ):
            if not request.user.profile.has_role("Supervisor"):
                return Response(
                    {"error": "This task has not been started yet"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if request.user.profile.has_role("Supervisor") and (
                process_status
                not in [
                    "Reassigned",
                    "Cancelled",
                ]
            ):
                return Response(
                    {"error": "This task has not been started yet"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        room_keeping_assign.change_status(process_status, request.user.profile)
        room_keeping_assign.last_modified_by = request.user.profile
        room_keeping_assign.save()

        serializer = api_serializers.RoomKeepingAssignSerializer(room_keeping_assign)
        return Response(serializer.data, status=status.HTTP_200_OK)

class HouseKeepingTaskStaffList(APIView):
    def get(self, request):
        """
        Retrieve the list of room-keeping staff assigned to a specific room on a given date and shift.
        Args:
            request (Request): The HTTP request object containing query parameters.
        Query Parameters:
            date (str): The date for which to retrieve the room-keeping staff.
            shift (str, optional): The shift for which to retrieve the room-keeping staff.
            room_number (str): The room number for which to retrieve the room-keeping staff.
        Returns:
            Response: A Response object containing the list of assigned staff or an error message.
        Raises:
            Room.DoesNotExist: If the specified room does not exist.
            Shift.DoesNotExist: If the specified shift does not exist.
        """
        date = request.GET.get("date")
        shift = request.GET.get("shift")
        room_number = request.GET.get("room_number")
        if not date or not room_number:
            return Response(
                {"error": "date and room number are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            room = models.Room.objects.get(room_number=room_number)
            if shift:
                shift = models.Shift.objects.get(name=shift)
                room_keeping_staff_list = models.RoomKeepingAssign.objects.filter(
                    room=room, assignment_date=date, shift=shift
                )
            else:
                room_keeping_staff_list = models.RoomKeepingAssign.objects.filter(
                    room=room, assignment_date=date
                )
        except models.Room.DoesNotExist:
            return Response(
                {"error": "room not found"}, status=status.HTTP_400_BAD_REQUEST
            )
        except models.Shift.DoesNotExist:
            return Response(
                {"error": "shift not found"}, status=status.HTTP_400_BAD_REQUEST
            )
        room_keeping_staff_list = room_keeping_staff_list.values_list(
            "assigned_to", flat=True
        )

        # if not room_keeping_staff_list:
        #     return Response(
        #         {"message": "No staff assigned for this task on the selected date"},
        #         status=status.HTTP_404_NOT_FOUND,
        #     )

        print(room_keeping_staff_list)

        return Response(room_keeping_staff_list, status=status.HTTP_200_OK)
    
class GenderList(generics.ListCreateAPIView):
    queryset = models.Gender.objects.all()
    serializer_class = api_serializers.GenderSerializer
    permission_classes = [custom_permissions.IsAdminProfileOrReadOnly]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.user.is_authenticated:
            try:
                profile = models.Profile.objects.get(user=self.request.user)
                context["created_by"] = profile
            except models.Profile.DoesNotExist:
                raise serializers.ValidationError({"error": "user account has no profile"})
        return context
    
class GenderDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Gender.objects.all()
    serializer_class = api_serializers.GenderSerializer
    lookup_url_kwarg = "pk"
    permission_classes = [custom_permissions.IsAdminProfileOrReadOnly]

class BookingList(generics.ListCreateAPIView):
    queryset = models.Booking.objects.all()
    serializer_class = api_serializers.BookingSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        try:
            profile = models.Profile.objects.get(user=self.request.user)
        except models.Profile.DoesNotExist:
            return Response(
                {"error": "User not authenticated"}, status=status.HTTP_400_BAD_REQUEST
            )
        context["authored_by"] = profile
        return context

class BookingExtend(APIView):
    def post(self, request):
        booking_id = request.data.get("booking_id")
        num_days = request.data.get("num_days")
        if not booking_id:
            return Response(
                {"error": "booking id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            booking = models.Booking.objects.get(id=booking_id)
        except models.Booking.DoesNotExist:
            return Response(
                {"error": "booking not found"}, status=status.HTTP_400_BAD_REQUEST
            )
        booking.extend_booking(num_days=num_days)
        booking.save()
        return Response(
            {"detail": "booking extended successfully"}, status=status.HTTP_200_OK
        )

class BookingDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Booking.objects.all()
    serializer_class = api_serializers.BookingSerializer
    lookup_url_kwarg = "pk"

    def get_serializer_context(self):
        try:
            profile = models.Profile.objects.get(user=self.request.user)
        except models.Profile.DoesNotExist:
            return Response(
                {"error": "user profile does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        context = super().get_serializer_context()
        context["authored_by"] = profile
        return context

class BookingCheckout(APIView):
    def post(self, request):
        booking_id = request.data.get("booking_id")
        if not booking_id:
            return Response(
                {"error": "booking id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            checked_out_by = models.Profile.objects.get(user=request.user)
        except models.Profile.DoesNotExist:
            return Response(
                {"error": "user profile does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            booking = models.Booking.objects.get(id=booking_id)
        except models.Booking.DoesNotExist:
            return Response(
                {"error": "booking not found"}, status=status.HTTP_400_BAD_REQUEST
            )
        checkout_response = helpers.checkout_booking(booking, checked_out_by)
        if checkout_response.casefold() == "success":
            return Response(
                {"detail": "booking checked out successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": "an error occured while checking out the booking"},
            status=status.HTTP_400_BAD_REQUEST,
        )

class RoomCategoryCreateView(CreatedByMixin, generics.CreateAPIView):
    queryset = models.RoomCategory.objects.all()
    serializer_class = api_serializers.RoomCategorySerializer
    permission_classes = [custom_permissions.IsHouseKeepingStaff | custom_permissions.IsAdmin, custom_permissions.IsDepartmentExec]

class RoomCategoryUpdateDeleteView(UpdateDeleteView):
    queryset = models.RoomCategory.objects.all()
    serializer_class = api_serializers.RoomCategorySerializer
    lookup_url_kwarg = "pk"
    permission_classes = [custom_permissions.IsHouseKeepingStaff | custom_permissions.IsAdmin, custom_permissions.IsDepartmentExec]

class RoomCategoryList(generics.ListAPIView):
    queryset = models.RoomCategory.objects.all()
    serializer_class = api_serializers.RoomCategorySerializer
    permission_classes = [custom_permissions.IsHouseKeepingStaff | custom_permissions.IsAdmin, custom_permissions.IsDepartmentExec]

class RoomCategoryRetrieveView(generics.RetrieveAPIView):
    queryset = models.RoomCategory.objects.all()
    serializer_class = api_serializers.RoomCategorySerializer
    lookup_url_kwarg = "pk"
    permission_classes = [custom_permissions.IsHouseKeepingStaff | custom_permissions.IsAdmin, custom_permissions.IsDepartmentExec]


class FloorList(CreatedByMixin, generics.ListCreateAPIView):
    queryset = models.HotelFloor.objects.all()
    serializer_class = api_serializers.FloorSerializer

class FloorDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.HotelFloor.objects.all()
    serializer_class = api_serializers.FloorSerializer
    lookup_url_kwarg = "pk"

class HotelViewList(CreatedByMixin, generics.ListCreateAPIView):
    queryset = models.HotelView.objects.all()
    serializer_class = api_serializers.HotelViewSerializer

class HotelViewDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.HotelView.objects.all()
    serializer_class = api_serializers.HotelViewSerializer
    lookup_url_kwarg = "pk"

class RoomCategoryDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.RoomCategory.objects.all()
    serializer_class = api_serializers.RoomCategorySerializer
    lookup_url_kwarg = "pk"

    def get_serializer_context(self):
        try:
            profile = models.Profile.objects.get(user=self.request.user)
        except models.Profile.DoesNotExist:
            return Response(
                {"error": "user profile does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        context = super().get_serializer_context()
        context["authored_by"] = profile
        return context

class RoomTypeListView(generics.ListCreateAPIView):
    queryset = models.RoomType.objects.all()
    serializer_class = api_serializers.RoomTypeSerializer

    def get_serializer_context(self):
        try:
            profile = models.Profile.objects.get(user=self.request.user)
        except models.Profile.DoesNotExist:
            return Response(
                {"error": "user profile does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        context = super().get_serializer_context()
        context["authored_by"] = profile
        return context

class RoomTypeRetrieveView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.RoomType.objects.all()
    serializer_class = api_serializers.RoomTypeSerializer
    lookup_url_kwarg = "pk"
    permission_classes = [IsAuthenticated]

class RoomTypeCreateView(CreatedByMixin, generics.CreateAPIView):
    queryset = models.RoomType.objects.all()
    serializer_class = api_serializers.RoomTypeSerializer
    permission_classes = [custom_permissions.IsHouseKeepingStaff | custom_permissions.IsAdmin, custom_permissions.IsDepartmentExec]

class RoomTypeUpdateDeleteView(UpdateDeleteView):
    queryset = models.RoomType.objects.all()
    serializer_class = api_serializers.RoomTypeSerializer
    lookup_url_kwarg = "pk"
    permission_classes = [custom_permissions.IsHouseKeepingStaff | custom_permissions.IsAdmin, custom_permissions.IsDepartmentExec]

class RoomListView(generics.ListAPIView):
    queryset = models.Room.objects.all()
    serializer_class = api_serializers.RoomSerializer
    permission_classes = [IsAuthenticated]

class RoomCreateView(CreatedByMixin, generics.CreateAPIView):
    queryset = models.Room.objects.all()
    serializer_class = api_serializers.RoomSerializer
    permission_classes = [custom_permissions.IsHouseKeepingStaff | custom_permissions.IsAdmin, custom_permissions.IsDepartmentExec]

class RoomRetrieveView(generics.RetrieveAPIView):
    queryset = models.Room.objects.all()
    serializer_class = api_serializers.RoomSerializer
    lookup_url_kwarg = "pk"
    permission_classes = [IsAuthenticated]

class RoomUpdateDeleteView(UpdateDeleteView):
    queryset = models.Room.objects.all()
    serializer_class = api_serializers.RoomSerializer
    lookup_url_kwarg = "pk"
    permission_classes = [custom_permissions.IsHouseKeepingStaff | custom_permissions.IsAdmin, custom_permissions.IsDepartmentExec]

class ComplaintCreate(generics.ListCreateAPIView):
    queryset = models.Amenity.objects.all()
    serializer_class = api_serializers.AmenitySerializer
    permission_classes = [IsAuthenticated]
    queryset = models.Complaint.objects.all()
    serializer_class = api_serializers.ComplaintSerializer

class ComplaintList(generics.ListAPIView):
    # queryset = models.Complaint.objects.all()
    serializer_class = api_serializers.ComplaintSerializer

    def get_queryset(self):
        queryset = models.Complaint.objects.prefetch_related(
            Prefetch(
                "assigned_complaints",
                queryset=models.AssignComplaint.objects.select_related(
                    "assigned_to", "complaint_status", "priority", "assigned_by"
                ).prefetch_related("complaint_items", "hashtags"),
            ),
            Prefetch(
                "processed_complaints",
                queryset=models.ProcessComplaint.objects.select_related(
                    "processed_by", "complaint_status"
                ),
            ),
        )
        return queryset

    def get_serializer_context(self):
        try:
            profile = models.Profile.objects.get(user=self.request.user)
        except models.Profile.DoesNotExist:
            return Response(
                {"error": "user profile does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        context = super().get_serializer_context()
        context["authored_by"] = profile
        return context

class ComplaintDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Complaint.objects.all()
    serializer_class = api_serializers.ComplaintSerializer
    lookup_url_kwarg = "pk"

class AssignComplaintList(generics.ListCreateAPIView):
    queryset = models.AssignComplaint.objects.all()
    serializer_class = api_serializers.AssignComplaintSerializer

    def get_serializer_context(self):
        try:
            profile = models.Profile.objects.get(user=self.request.user)
        except models.Profile.DoesNotExist:
            return Response(
                {"error": "user profile does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        context = super().get_serializer_context()
        context["authored_by"] = profile
        return context

class AssignComplaintDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.AssignComplaint.objects.all()
    serializer_class = api_serializers.AssignComplaintSerializer
    lookup_url_kwarg = "pk"

    def get_serializer_context(self):
        try:
            profile = models.Profile.objects.get(user=self.request.user)
        except models.Profile.DoesNotExist:
            return Response(
                {"error": "user profile does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        context = super().get_serializer_context()
        context["authored_by"] = profile
        return context

class ProcessComplaintList(generics.ListCreateAPIView):
    queryset = models.ProcessComplaint.objects.all()
    serializer_class = api_serializers.ProcessComplaintSerializer

    def get_serializer_context(self):
        try:
            profile = models.Profile.objects.get(user=self.request.user)
        except models.Profile.DoesNotExist:
            return Response(
                {"error": "user profile does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        context = super().get_serializer_context()
        context["authored_by"] = profile
        return context

class ProcessComplaintDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.ProcessComplaint.objects.all()
    serializer_class = api_serializers.ProcessComplaintSerializer
    lookup_url_kwarg = "pk"

class AmenityUpdateDeleteView(CreatedByMixin, UpdateDeleteView):
    queryset = models.Amenity.objects.all()
    serializer_class = api_serializers.AmenitySerializer
    lookup_url_kwarg = "pk"

class AmenityRetrieveView(generics.RetrieveAPIView):
    def get_serializer_context(self):
        try:
            profile = models.Profile.objects.get(user=self.request.user)
        except models.Profile.DoesNotExist:
            return Response(
                {"error": "user profile does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        context = super().get_serializer_context()
        context["authored_by"] = profile
        return context

class AmenityListView(generics.ListAPIView):
    serializer_class = api_serializers.AmenitySerializer
    queryset = models.Amenity.objects.all()
    permission_classes = [IsAuthenticated]

class AmenityCreateView(CreatedByMixin, generics.CreateAPIView):
    serializer_class = api_serializers.AmenitySerializer
    queryset = models.Amenity.objects.all()
    permission_classes = [custom_permissions.IsHouseKeepingStaff | custom_permissions.IsAdmin, custom_permissions.IsDepartmentExec]

class RoomAmenityList(APIView):
    def get(self, request):
        try:
            # print(f"request object: {request.data}")
            room_number = request.GET.get("room_number")
            client = request.GET.get("client")
            print(f"room #: {room_number}")
            room = models.Room.objects.get(room_number=room_number)
            # if client:
            #     if room.client != client:
            #         return Response(
            #             {"error": "Room does not belong to client"},
            #             status=status.HTTP_400_BAD_REQUEST,
            #         )
        except models.Room.DoesNotExist:
            return Response(
                {"error": "Room not found"}, status=status.HTTP_400_BAD_REQUEST
            )
        amenities = room.amenities.all()
        print(f"room amenities: {amenities}")
        serializer = api_serializers.AmenitySerializer(amenities, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class PriorityList(generics.ListCreateAPIView):
    queryset = models.Priority.objects.all()
    serializer_class = api_serializers.PrioritySerializer

class GuestList(generics.ListCreateAPIView):
    queryset = models.Guest.objects.all()
    serializer_class = api_serializers.GuestSerializer

    def get_serializer_context(self):
        try:
            user_profile = self.request.user.profile
        except models.Profile.DoesNotExist:
            return Response(
                {"error": "User not authenticated"}, status=status.HTTP_400_BAD_REQUEST
            )
        context = super().get_serializer_context()
        context["created_by"] = user_profile
        return context

class GuestDetails(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Guest.objects.all()
    serializer_class = api_serializers.GuestSerializer
    lookup_url_kwarg = "guest_id"

    def get_object(self):
        obj = self.get_serializer().Meta.model.objects.get(
            guest_id=self.kwargs.get("guest_id")
        )
        return obj

class NameTitleListView(generics.ListAPIView):
    queryset = models.NameTitle.objects.all()
    serializer_class = api_serializers.NameTitleSerializer
    permission_classes = [IsAuthenticated]

class NameTitleCreateView(CreatedByMixin, generics.CreateAPIView):
    queryset = models.NameTitle.objects.all()
    serializer_class = api_serializers.NameTitleSerializer
    permission_classes = [custom_permissions.IsFrontDeskStaff | custom_permissions.IsAdmin]

class NameTitleUpdateDeleteView(UpdateDeleteView):
    queryset = models.NameTitle.objects.all()
    serializer_class = api_serializers.NameTitleSerializer
    lookup_url_kwarg = "pk"
    permission_classes = [custom_permissions.IsFrontDeskStaff | custom_permissions.IsAdmin]

class NameTitleRetrieveView(generics.RetrieveAPIView):
    queryset = models.NameTitle.objects.all()
    serializer_class = api_serializers.NameTitleSerializer
    lookup_url_kwarg = "pk"
    permission_classes = [IsAuthenticated]
