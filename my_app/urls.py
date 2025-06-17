from django.urls import path
from .views import WebLoginView, WebVerifyOTPView

urlpatterns = [
    path('login/', WebLoginView.as_view(), name='login_web'),
    path('verify-otp/', WebVerifyOTPView.as_view(), name='verify_otp_web'),
]
