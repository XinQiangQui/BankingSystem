from django.urls import path

from .views import UserRegistrationView, LogoutView, UserLoginView, ProfileDisplayView, OTPReceiveView, OTPSubmitView


app_name = 'accounts'

urlpatterns = [
    path(
        "login/", UserLoginView.as_view(),
        name="user_login"
    ),
    path(
        "logout/", LogoutView.as_view(),
        name="user_logout"
    ),
    path(
        "register/", UserRegistrationView.as_view(),
        name="user_registration"
    ),
    path(
        "profile/", ProfileDisplayView.as_view(),
        name="profile"
    ),
    path(
        "otp_view/", OTPReceiveView.as_view(),
        name="otp_view"
    ),
    path(
        "otp_submit_view/", OTPSubmitView.as_view(),
        name="otp_submit_view"
    ),
]
