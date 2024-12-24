from django.urls import path
from . import views
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = [
    path("accounts/", views.ProfileList.as_view(), name="profile"),
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
]

urlpatterns = format_suffix_patterns(urlpatterns)