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
    # urls for amenities management
    path("amenities/", views.AmenityList.as_view(), name="amenities"),
    path("amenities/<uuid:pk>/", views.AmenityDetail.as_view(), name="amenity_details"),

    # urls for room category management
    path("room-categories/", views.RoomCategoryList.as_view(), name="room_categories"),
    path(
        "room-categories/<uuid:pk>/",
        views.RoomCategoryDetail.as_view(),
        name="room_category_details",
    ),

    # urls for room type management
    path("room-types/", views.RoomTypeList.as_view(), name="room_types"),
    path("room-types/<uuid:pk>/", views.RoomTypeDetail.as_view(), name="room_type_details"),

    # urls for room management
    path("rooms/", views.RoomList.as_view(), name="rooms"),
    path("rooms/<uuid:pk>/", views.RoomDetail.as_view(), name="room_details"),

    # urls for booking management
    path("bookings/", views.BookingList.as_view(), name="bookings"),
    path('bookings/extend/', views.BookingExtend.as_view(), name='extend_booking'),
    path('bookings/<uuid:pk>/', views.BookingDetail.as_view(), name='booking_details'),
    path('bookings/checkout/', views.BookingCheckout.as_view(), name='checkout_booking'),

    # urls for complaint management
    path("complaints/", views.ComplaintList.as_view(), name="complaints"),
    path("complaints/add/", views.ComplaintCreate.as_view(), name="add_complaint"),
    path("complaints/<uuid:pk>/", views.ComplaintDetail.as_view(), name="complaint_details"),
]
urlpatterns = format_suffix_patterns(urlpatterns)



