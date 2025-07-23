import requests
from myproject import settings
from django.core.mail import send_mail

def send_otp(email, otp):
    subject = "Your OTP Code"
    message = f"Your OTP code is: {otp}"
    from_email = None  # Uses DEFAULT_FROM_EMAIL
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list)
    print(f"[EMAIL SENT] OTP {otp} sent to {email}")
    return True
