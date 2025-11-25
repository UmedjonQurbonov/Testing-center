from django.urls import path
from accounts.views import *
from django.conf.urls.static import static
from django.conf import settings



urlpatterns = [
    path("register/", register_view, name="register"),
    path("login", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("profile/", profile_view, name="profile"),        
    path("profile/edit/", profile_edit, name="profile_edit"), 
]