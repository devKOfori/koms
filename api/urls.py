from django.urls import path
from . import views
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = [
    path("accounts/", views.ProfileList.as_view(), name="profile"),
    path(
        "accounts/<uuid:pk>/", views.AccountChangeView.as_view(), name="change_profile"
    ),
    path("accounts/register/", views.RegisterAccountView.as_view(), name="register"),
    path("accounts/logout/", views.LogoutView.as_view(), name="logout"),
    path(
        "accounts/change-password/",
        views.PasswordChangeView.as_view(),
        name="change_password",
    ),
    path(
        "accounts/reset-password/",
        views.PasswordResetView.as_view(),
        name="reset_password",
    ),
    path("roles/", views.RoleList.as_view(), name="roles"),
    path("departments/", views.DepartmentList.as_view(), name="departments"),
    path(
        "shift-management/",
        views.ProfileShiftAssignCreateView.as_view(),
        name="assign_shift",
    ),
    path(
        "shift-management/<uuid:pk>/",
        views.ProfileShiftAssignUpdateView.as_view(),
        name="update_shift",
    ),
    path(
        "house-keeping/assign/",
        views.RoomKeepingAssignCreate.as_view(),
        name="assign_house_keeping",
    ),
    path(
        "house-keeping/<uuid:pk>/",
        views.RoomKeepingAssignUpdate.as_view(),
        name="edit_room_keeping_assign",
    ),
    path(
        "house-keeping/process/",
        views.ProcessRoomKeeping.as_view(),
        name="process_roomkeeping",
    ),
    path("bookings/", views.BookingList.as_view(), name="bookings"),
    path('bookings/extend/', views.BookingExtend.as_view(), name='extend_booking'),
    path('bookings/<uuid:pk>/', views.BookingDetail.as_view(), name='booking_details'),
    path('bookings/checkout/', views.BookingCheckout.as_view(), name='checkout_booking'),
]
urlpatterns = format_suffix_patterns(urlpatterns)
