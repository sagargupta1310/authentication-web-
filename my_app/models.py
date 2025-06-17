from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

class User(AbstractUser):
 phone = models.CharField(max_length=10,unique=True, blank=True, null=True, validators=[RegexValidator(
 regex=r"^\d{10}", message="Phone number must be 10 digits only.")])
 address = models.TextField(max_length=50, null=True, blank=True)
 dob = models.DateField(null=True, blank=True)
 otp = models.CharField(max_length=6, null=True, blank=True)
 otp_expiry = models.DateTimeField(blank=True, null=True)
 max_otp_try = models.CharField(max_length=2, default=3)
 otp_max_out = models.DateTimeField(blank=True, null=True)

from django.db import models

class Plan(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration = models.CharField(max_length=50)
    description = models.TextField()

    def __str__(self):
        return self.name

class Workout(models.Model):
    name = models.CharField(max_length=100)
    trainer = models.CharField(max_length=100)
    time = models.CharField(max_length=20)
    day = models.CharField(max_length=20)
    description = models.TextField()

    def __str__(self):
        return self.name
