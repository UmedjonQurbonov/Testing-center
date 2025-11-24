from django.urls import path
from accounts.views import *
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path("register/", register_view, name="register"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("users/", user_list_view, name="user_list"),
]