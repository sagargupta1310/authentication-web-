# from django.contrib import admin
# from django.urls import path, include
# from django.shortcuts import redirect

# urlpatterns = [
#     path('', lambda request: redirect('login_web')),  # Redirect root to web login
#     path('admin/', admin.site.urls),
#     path('api/auth/', include('my_app.api_urls')),
#     path('auth/', include('my_app.web_urls')),
# ]

from django.urls import path, include
from django.contrib import admin  # ✅ Required for admin.site.urls
from django.shortcuts import redirect
from django.conf.urls.static import static
from django.conf import settings 
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('my_app.urls')),  # <-- this includes your dashboard route
    path('auth/', include('my_app.web_urls')),  # if you're using web_urls
    path('api/auth/', include('my_app.api_urls')),  # if using DRF for APIs
    path('', lambda request: redirect('auth/login/')),  # Redirect root to web login

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
