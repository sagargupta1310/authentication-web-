from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('', lambda request: redirect('login_web')),  # Redirect root to web login
    path('admin/', admin.site.urls),
    path('api/auth/', include('my_app.api_urls')),
    path('auth/', include('my_app.web_urls')),
]
