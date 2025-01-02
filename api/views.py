from django.shortcuts import render
from django.db.models import Prefetch
from rest_framework import generics, status
from rest_framework import exceptions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from . import serializers as api_serializers
from . import models
from utils import helpers


# Create your views here.
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


class AccountChangeView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Profile.objects.all()
    serializer_class = api_serializers.CustomUserProfileSerializer


class LogoutView(APIView):
    def post(self, request):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response(
                {"error": "Refresh token is required for logout."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"detail": "Logout Successfull."}, status=status.HTTP_205_RESET_CONTENT
            )
        except Exception as e:
            return Response(
                {"error": "Invalid or malformed refresh token"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class PasswordChangeView(APIView):
    def post(self, request):
        try:
            print(request.user)
            user_profile = models.Profile.objects.get(user=request.user)
            user = user_profile.user
            # password match verification to be done at the frontend

            new_password = request.data.get("new_password", None)
            if not new_password:
                return Response(
                    {"error": "new password not specified"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.set_password(new_password)
            user.save()
            return Response(
                {"detail": "password changed successfull"},
                status=status.HTTP_200_OK,
            )
        except models.Profile.DoesNotExist:
            return Response(
                {"error": "user account not found"}, status=status.HTTP_400_BAD_REQUEST
            )


class PasswordResetView(generics.CreateAPIView):
    queryset = models.PasswordReset.objects.all()
    serializer_class = api_serializers.PasswordResetSerializer


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


class DepartmentList(generics.ListCreateAPIView):
    queryset = models.Department.objects.all()
    serializer_class = api_serializers.DepartmentSerializer


class CustomUpdateView(APIView):
    def put(self, request, *args, **kwargs):
        serializer = api_serializers.CustomUserProfileSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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


class RoomKeepingAssignCreate(generics.ListCreateAPIView):
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


class ProcessRoomKeeping(generics.CreateAPIView):
    queryset = models.ProcessRoomKeeping.objects.all()
    serializer_class = api_serializers.ProcessRoomKeepingSerializer

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


class BookingList(generics.ListCreateAPIView):
    queryset = models.Booking.objects.all()
    serializer_class = api_serializers.BookingSerializer

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


class RoomCategoryList(generics.ListCreateAPIView):
    queryset = models.RoomCategory.objects.all()
    serializer_class = api_serializers.RoomCategorySerializer

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


class RoomTypeList(generics.ListCreateAPIView):
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


class RoomTypeDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.RoomType.objects.all()
    serializer_class = api_serializers.RoomTypeSerializer
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


class RoomList(generics.ListCreateAPIView):
    queryset = models.Room.objects.all()
    serializer_class = api_serializers.RoomSerializer

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


class RoomDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Room.objects.all()
    serializer_class = api_serializers.RoomSerializer
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


class AmenityList(generics.ListCreateAPIView):
    queryset = models.Amenity.objects.all()
    serializer_class = api_serializers.AmenitySerializer

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


class AmenityDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Amenity.objects.all()
    serializer_class = api_serializers.AmenitySerializer
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


class ComplaintCreate(generics.ListCreateAPIView):
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
