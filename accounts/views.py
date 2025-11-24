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
    if request.method=="GET":
        return render(request,"login.html")
    elif request.method=="POST":
        username = request.POST.get("username", None)
        password = request.POST.get("password", None)
        user = authenticate(request, username=username, password=password)
        if user is None:
            return render(request,"login.html", context={"username":username, "Error":"Invalid credentials"})
        
        login(request, user)
        return redirect("user_list")  

@login_required
def user_list_view(request):
    users = CustomUser.objects.all()
    return render(request, "user_list.html", {"users": users})



def logout_view(request):
    logout(request)
    return redirect("login")

