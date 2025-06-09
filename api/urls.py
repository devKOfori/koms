from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework_simplejwt.views import (
    TokenRefreshView
)
from . import views

urlpatterns = [
    path("accounts/add-user/", views.AddUserProfileView.as_view(), name="add_user_profile"),
    path("accounts/<uuid:pk>/add-role/", views.UserRolesCreateView.as_view(), name="add_user_role"),
    path("accounts/<uuid:pk>/roles/", views.UserRolesListView.as_view(), name="user_roles"),
    path("accounts/login/", views.CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("accounts/", views.ProfileList.as_view(), name="profile"),
    path(
        "accounts/<uuid:pk>/", views.UserProfileDetailView.as_view(), name="change_profile"
    ),
    path("accounts/logout/", views.LogoutView3.as_view(), name="logout"),
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
    path("accounts/reset-password/complete/",
        views.CompletePasswordResetView.as_view(),
        name="complete_password_reset"
    ),
    path(
        "accounts/my-department-staff/",
        views.MyDepartmentStaffList.as_view(),
        name="my_department_staff",
    ),

    path("roles/", views.RoleList.as_view(), name="roles"),
    path("roles/<uuid:pk>/", views.RoleDetail.as_view(), name="role_details"),
    
    path("departments/", views.DepartmentList.as_view(), name="departments"),
    path(
        "departments/<uuid:pk>/", views.DepartmentDetail.as_view(), name="department_details"
    ),

    path("countries/", views.CountryList.as_view(), name="countries"),
    path("countries/add/", views.CountryCreateView.as_view(), name="add_country"),
    path("countries/<uuid:pk>/edit/", views.CountryUpdateDeleteView.as_view(), name="edit_country"),
    path("countries/<uuid:pk>/", views.CountryRetrieveView.as_view(), name="country_details"),
    
    path("genders/", views.GenderList.as_view(), name='genders'),
    path("genders/<uuid:pk>/", views.GenderDetail.as_view(), name="gender_details"),

    path("titles/", views.NameTitleListView.as_view(), name="titles"),
    path("titles/add/", views.NameTitleCreateView.as_view(), name="add_title"),
    path("titles/<uuid:pk>/edit/", views.NameTitleUpdateDeleteView.as_view(), name="edit_title"),
    path("titles/<uuid:pk>/", views.NameTitleRetrieveView.as_view(), name="title_details"),

    path("shifts/", views.ShiftList.as_view(), name="shifts"),
    path("my-shifts/", views.MyShiftList.as_view(), name="my_shifts"),
    path(
        "shift-management/",
        views.ProfileShiftAssignCreateView.as_view(),
        name="assign_shift",
    ),
    path("shift-statuses/", views.ShiftStatusList.as_view(), name="shift_statuses"),
    path(
        "shift-management/<uuid:pk>/",
        views.ProfileShiftAssignUpdateView.as_view(),
        name="update_shift",
    ),
    path(
        "shift-management/<uuid:pk>/change-status/",
        views.UpdateAssignedShiftStatus.as_view(),
        name="change_shift_status",
    ),
    path("shifts/<uuid:pk>/notes/", views.ShiftNoteList.as_view(), name="shift_notes"),
    path(
        "shifts/notes/<uuid:note_id>/",
        views.ShiftNoteDetail.as_view(),
        name="shift_note",
    ),
    path(
        "shift-assignments/",
        views.ProfileShiftAssignList.as_view(),
        name="shift_assignments",
    ),
    path("shift-assignments/clear/", views.clear_shift_assignments, name="clear_shift"),
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
        "house-keeping/<uuid:pk>/change-status/",
        views.UpdateRoomKeepingStatus.as_view(),
        name="change_room_keeping_status",
    ),
    path(
        "house-keeping/staff",
        views.HouseKeepingTaskStaffList.as_view(),
        name="house_keeping_staff",
    ),
    path("amenities/", views.AmenityListView.as_view(), name="amenities_list"),
    path("amenities/add/", views.AmenityCreateView.as_view(), name="add_amenity"),
    path("amenities/<uuid:pk>/edit/", views.AmenityUpdateDeleteView.as_view(), name="edit_amenity"),
    path("amenities/<uuid:pk>/", views.AmenityRetrieveView.as_view(), name="amenity_details"),
    # urls for room category management
    path("room-categories/", views.RoomCategoryList.as_view(), name="room_categories"),
    path("room-categories/add/", views.RoomCategoryCreateView.as_view(), name="add_room_category"),
    path(
    "room-categories/<uuid:pk>/edit", views.RoomCategoryRetrieveView.as_view(), name="edit_room_category"
    ),
    path(
        "room-categories/<uuid:pk>/",
        views.RoomCategoryDetail.as_view(),
        name="room_category_details",
    ),
    # urls for room type management
    path("room-types/", views.RoomTypeListView.as_view(), name="room_types"),
    path("room-types/add/", views.RoomTypeCreateView.as_view(), name="add_room_type"),
    path(
        "room-types/<uuid:pk>/edit/", views.RoomTypeUpdateDeleteView.as_view(), name="edit_room_type"
    ),
    path(
        "room-types/<uuid:pk>/",
        views.RoomTypeRetrieveView.as_view(),
        name="room_type_details",
    ),
    # urls for room management
    path("rooms/", views.RoomListView.as_view(), name="rooms"),
    path("rooms/add/", views.RoomCreateView.as_view(), name="add_room"),
    path("rooms/<uuid:pk>/", views.RoomRetrieveView.as_view(), name="room_details"),
    path("rooms/<uuid:pk>/edit/", views.RoomUpdateDeleteView.as_view(), name="edit_room"),
    path("room-amenities/", views.RoomAmenityList.as_view(), name="room_amenities"),
    
    # urls for complaint management
    path("complaints/", views.ComplaintList.as_view(), name="complaints"),
    path("complaints/add/", views.ComplaintCreate.as_view(), name="add_complaint"),
    path(
        "complaints/<uuid:pk>/",
        views.ComplaintDetail.as_view(),
        name="complaint_details",
    ),
    # urls for assign complaint management
    path(
        "complaints/assign/",
        views.AssignComplaintList.as_view(),
        name="assign_complaint",
    ),
    path(
        "complaints/assign/<uuid:pk>/",
        views.AssignComplaintDetail.as_view(),
        name="assign_complaint_details",
    ),
    # urls for complaint process management
    path(
        "complaints/process/",
        views.ProcessComplaintList.as_view(),
        name="process_complaint",
    ),
    path(
        "complaints/process/<uuid:pk>/",
        views.ProcessComplaintDetail.as_view(),
        name="process_complaint_details",
    ),
    # urls for bed management
    path("bedtypes/", views.BedTypeListView.as_view(), name="bed_types"),
    path("bedtypes/add/", views.BedTypeCreateView.as_view(), name="add_bed_type"),
    path("bedtypes/<uuid:pk>/edit/", views.BedTypeUpdateDeleteView.as_view(), name="edit_bed_type"),
    path("bedtypes/<uuid:pk>/", views.BedTypeDetail.as_view(), name="bed_type_details"),
    # urls for floor management
    path("floors/", views.FloorList.as_view(), name="floors"),
    path("floors/<uuid:pk>/", views.FloorDetail.as_view(), name="floor_details"),
    # urls form views management
    path("hotel-views/", views.HotelViewList.as_view(), name="hotel_views"),
    path(
        "hotel-views/<uuid:pk>/",
        views.HotelViewDetail.as_view(),
        name="hotel_view_details",
    ),
    path("priorities/", views.PriorityList.as_view(), name="priorities"),

    # urls for guests management
    
    path("guests/", views.GuestListView.as_view(), name="guests"),
    path("guests/add/", views.GuestCreateView.as_view(), name="add_guest"),
    path("guests/<uuid:pk>/edit/", views.GuestUpdateDeleteView.as_view(), name="edit_guest"),
    path("guests/<uuid:pk>/", views.GuestRetrieveView.as_view(), name="guest_details"),
    
    path("identification-types/", views.IdentificationTypeListView.as_view(), name='identification_types'),
    path("identification-types/add/", views.IdentificationTypeCreateView.as_view(), name='add_identification_type'),
    path("identification-types/<uuid:pk>/edit/", views.IdentificationTypeUpdateDeleteView.as_view(), name='edit_identification_type'),
    path("identification-types/<uuid:pk>/", views.IdentificationTypeRetrieveView.as_view(), name='identification_type_details'),

    # urls for booking management
    path("bookings/", views.BookingList.as_view(), name="bookings"),
    path("bookings/add/", views.BookingCreateView.as_view(), name="add_booking"),
    path("bookings/<uuid:pk>/edit/", views.BookingUpdateDeleteView.as_view(), name="edit_booking"),
    path("bookings/<uuid:pk>/", views.BookingRetrieveView.as_view(), name="booking_details"),
    path("bookings/extend/", views.BookingExtend.as_view(), name="extend_booking"),
    path("bookings/<uuid:pk>/", views.BookingDetail.as_view(), name="booking_details"),
    path(
        "bookings/checkout/", views.BookingCheckout.as_view(), name="checkout_booking"
    ),
]
urlpatterns = format_suffix_patterns(urlpatterns)
