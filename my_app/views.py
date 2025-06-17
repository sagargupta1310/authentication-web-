from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.utils import timezone
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login
from django.core.exceptions import ObjectDoesNotExist

from .models import User
from .utils import send_otp
import random
import datetime

# ----- Reusable OTP Logic -----
def generate_and_send_otp(user):
    otp = random.randint(1000, 9999)
    user.otp = otp
    user.otp_expiry = timezone.now() + datetime.timedelta(minutes=10)
    max_otp_try = int(user.max_otp_try) - 1

    if max_otp_try == 0:
        user.otp_max_out = timezone.now() + datetime.timedelta(hours=1)
    elif max_otp_try == -1:
        user.max_otp_try = 3
    else:
        user.otp_max_out = None
        user.max_otp_try = max_otp_try

    user.save()
    send_otp(user.phone, otp)
    return otp

# ----- API VIEWS -----
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone = request.data.get('phone')
        if not phone:
            return Response("Phone number is required", status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(phone=phone)
        except ObjectDoesNotExist:
            user = User.objects.create(phone=phone, is_passenger=True)

        if int(user.max_otp_try) == 0 and user.otp_max_out and timezone.now() < user.otp_max_out:
            return Response("Max OTP try reached, try after an hour", status=status.HTTP_400_BAD_REQUEST)

        generate_and_send_otp(user)
        return Response("Successfully generated OTP", status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        otp = request.data.get('otp')
        if not otp:
            return Response("OTP is required", status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(otp=otp)
        except User.DoesNotExist:
            return Response("Please enter the correct OTP", status=status.HTTP_400_BAD_REQUEST)

        login(request, user)
        user.otp = None
        user.otp_expiry = None
        user.max_otp_try = 3
        user.otp_max_out = None
        user.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }, status=status.HTTP_200_OK)

# ----- WEB VIEWS -----
class WebLoginView(View):
    def get(self, request):
        return render(request, 'my_app/login.html')

    def post(self, request):
        phone = request.POST.get('phone')
        user, _ = User.objects.get_or_create(phone=phone)
        generate_and_send_otp(user)
        request.session['phone'] = phone
        return redirect('verify_otp_web')


class WebVerifyOTPView(View):
    def get(self, request):
        return render(request, 'my_app/verify_otp.html')

    def post(self, request):
        phone = request.session.get('phone')
        otp = request.POST.get('otp')
        user = User.objects.get(phone=phone)
        if str(user.otp) == str(otp):
            user.otp = None
            user.save()
            return render(request, 'my_app/landing.html', {"user": user})
        else:
            return render(request, 'my_app/verify_otp.html', {"error": "Invalid OTP"})



# ----- HOME VIEW -----

def home_view(request):
    return render(request, 'my_app/home.html')

# ----- ALTERNATE VERIFY (probably unused) -----
def verify_otp(request):
    if request.method == "POST":
        otp_entered = request.POST.get("otp")
        phone_number = request.session.get("phone_number")
        correct_otp = request.session.get("otp")

        if otp_entered == correct_otp:
            request.session.flush()
            return render(request, "success.html")
        else:
            return render(request, "verify_otp.html", {"error": "Invalid OTP"})

    return render(request, "verify_otp.html")


from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_view(request):
    return render(request, 'my_app/dashboard.html')