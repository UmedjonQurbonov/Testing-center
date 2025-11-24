from django.shortcuts import render,redirect,HttpResponse
from .models import *
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import login,logout,authenticate
from django.http import HttpResponseRedirect,HttpResponseForbidden
from django.contrib.auth.decorators import login_required

def register_view(request):
    if request.method == "GET":
        return render(request, "register.html")

    elif request.method == "POST":
        username = request.POST.get("username", None)
        email = request.POST.get("email", None)
        password = request.POST.get("password", None)
        confirm = request.POST.get("confirm", None)

        if not username or not email or not password:
            return render(request, "register.html", {
                "username": username,
                "email": email,
                "Error": "Write all fields"
            })

        if password != confirm:
            return render(request, "register.html", {
                "username": username,
                "email": email,
                "Error": "Passwords do not match"
            })

        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        return redirect("login")

    
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("home")
        else:
            return render(request, "login.html", {"Error": "Invalid credentials"})
    return render(request, "login.html")

@login_required
def user_list_view(request):
    users = CustomUser.objects.all()
    return render(request, "user_list.html", {"users": users})



def logout_view(request):
    logout(request)
    return redirect("login")

from django.contrib import messages
from django.core.files.storage import default_storage
from .models import UserProfile

@login_required
def profile_edit(request):
    # Получаем или создаём профиль
    profile, created = UserProfile.objects.get_or_create(usern=request.user)

    if request.method == "POST":
        # Сохраняем bio
        profile.bio = request.POST.get("bio", "").strip() or None

        # Сохраняем аватар
        if "avatar" in request.FILES:
            # Удаляем старый, если был
            if profile.avatar:
                default_storage.delete(profile.avatar.path)
            profile.avatar = request.FILES["avatar"]
        # Удаление аватара по галочке
        elif request.POST.get("remove_avatar") == "on" and profile.avatar:
            default_storage.delete(profile.avatar.path)
            profile.avatar = None

        profile.save()
        messages.success(request, "Профиль сохранён!")
        return redirect("accounts:profile")

    return render(request, "profile_edit.html", {"profile": profile})


@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(usern=request.user)
    return render(request, "profile_view.html", {"profile": profile})