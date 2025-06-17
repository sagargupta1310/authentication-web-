import requests
from myproject import settings

def send_otp(mobile, otp):
    """
    Send OTP via SMS using 2Factor.in API.
    """
    url = f"https://2factor.in/API/V1/{settings.SMS_API_KEY}/SMS/{mobile}/{otp}/OTP1"
    headers = {'content-type': 'application/x-www-form-urlencoded'}

    response = requests.get(url, headers=headers)
    print("DEBUG:", response.content)
    return response.ok
