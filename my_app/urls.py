from django.urls import path
from .views import WebLoginView, WebVerifyOTPView, dashboard_view
from .views import WebRegisterView

urlpatterns = [
    path('login/', WebLoginView.as_view(), name='login_web'),
    path('verify-otp/', WebVerifyOTPView.as_view(), name='verify_otp_web'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('register/', WebRegisterView.as_view(), name='register_web'),
    # Add this for @login_required redirects
    path('accounts/login/', WebLoginView.as_view(), name='account_login'),
]
