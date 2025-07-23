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
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from .models import User, Plan, Workout
from .utils import send_otp
import random
import datetime
from collections import defaultdict

# In-memory rate limiting (for demo; use cache/redis in prod)
otp_request_times = defaultdict(list)
RATE_LIMIT = 5  # max 5 requests
RATE_PERIOD = 60  # per 60 seconds

# ----- Reusable OTP Logic -----
def generate_and_send_otp(user):
    otp = random.SystemRandom().randint(100000, 999999)
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
    send_otp(user.email, otp)
    return otp

# ----- API VIEWS -----
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response("Email is required", status=status.HTTP_400_BAD_REQUEST)
        try:
            validate_email(email)
        except ValidationError:
            return Response("Invalid email format", status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email=email).exists():
            return Response("Email already registered", status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.create_user(username=email, email=email)
        return Response("User registered successfully", status=status.HTTP_201_CREATED)

class RequestOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response("Email is required", status=status.HTTP_400_BAD_REQUEST)
        try:
            validate_email(email)
        except ValidationError:
            return Response("Invalid email format", status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email=email)
        except ObjectDoesNotExist:
            return Response("User not found. Please register first.", status=status.HTTP_404_NOT_FOUND)
        # Rate limiting
        now = timezone.now().timestamp()
        times = [t for t in otp_request_times[email] if now - t < RATE_PERIOD]
        if len(times) >= RATE_LIMIT:
            return Response("Too many OTP requests. Please try again later.", status=status.HTTP_429_TOO_MANY_REQUESTS)
        times.append(now)
        otp_request_times[email] = times
        if int(user.max_otp_try) == 0 and user.otp_max_out and timezone.now() < user.otp_max_out:
            return Response("Max OTP try reached, try after an hour", status=status.HTTP_400_BAD_REQUEST)
        generate_and_send_otp(user)
        return Response("OTP sent to your email (mock)", status=status.HTTP_200_OK)

class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        if not email or not otp:
            return Response("Email and OTP are required", status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response("User not found", status=status.HTTP_404_NOT_FOUND)
        if not user.otp or str(user.otp) != str(otp):
            return Response("Invalid OTP", status=status.HTTP_400_BAD_REQUEST)
        if user.otp_expiry and timezone.now() > user.otp_expiry:
            return Response("OTP expired", status=status.HTTP_400_BAD_REQUEST)
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

# ----- WEB VIEWS (Optional, for demo) -----
class WebLoginView(View):
    def get(self, request):
        return render(request, 'my_app/login.html')

    def post(self, request):
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
        if not user:
            return render(request, 'my_app/login.html', {"error": "User not found. Please register first."})
        generate_and_send_otp(user)
        request.session['email'] = email
        return redirect('verify_otp_web')

class WebRegisterView(View):
    def get(self, request):
        return render(request, 'my_app/register.html')

    def post(self, request):
        email = request.POST.get('email')
        if not email:
            return render(request, 'my_app/register.html', {"error": "Email is required."})
        try:
            validate_email(email)
        except ValidationError:
            return render(request, 'my_app/register.html', {"error": "Invalid email format."})
        if User.objects.filter(email=email).exists():
            return render(request, 'my_app/register.html', {"error": "Email already registered."})
        User.objects.create_user(username=email, email=email)
        return render(request, 'my_app/register.html', {"success": "Registration successful! You can now log in."})

class WebVerifyOTPView(View):
    def get(self, request):
        return render(request, 'my_app/verify_otp.html')

    def post(self, request):
        email = request.session.get('email')
        otp = request.POST.get('otp')
        user = User.objects.get(email=email)
        if str(user.otp) == str(otp):
            from django.contrib.auth import login
            login(request, user)  # Log the user in for session auth
            user.otp = None
            user.save()
            return redirect('dashboard')
        else:
            return render(request, 'my_app/verify_otp.html', {"error": "Invalid OTP"})

# ----- HOME VIEW -----
def home_view(request):
    return render(request, 'my_app/home.html')

# ----- ALTERNATE VERIFY (probably unused) -----
def verify_otp(request):
    if request.method == "POST":
        otp_entered = request.POST.get("otp")
        email = request.session.get("email")
        correct_otp = request.session.get("otp")
        if otp_entered == correct_otp:
            request.session.flush()
            return render(request, "success.html")
        else:
            return render(request, "verify_otp.html", {"error": "Invalid OTP"})
    return render(request, "verify_otp.html")

@login_required
def dashboard_view(request):
    plans = Plan.objects.all()
    workouts = Workout.objects.all()
    return render(request, 'my_app/dashboard.html', {
        'plans': plans,
        'workouts': workouts
    })