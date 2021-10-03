# -*- coding: utf-8 -*-

# redirect function redirects the user to another URL after log in has been successful
from django.shortcuts import render, redirect

# Importa o formulário de criação e autenticação de usuário:
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

# Imports the decorator for the login required views:
from django.contrib.auth.decorators import login_required

# Imports functions from django that log in, log out and authenticate users
from django.contrib.auth import login, logout, authenticate

# Importing HTTP responses and File response (the last one for downloading files):
from django.http import HttpResponse, FileResponse
from django.db import IntegrityError
import pathlib
import os

# from .forms import *
from .models import *


# Create your views here.


def home(request):
    return render(request, "srm_solver/home.html")


def about(request):
    return render(request, "srm_solver/about.html")


def signupuser(request):
    """
    Logs in the user and redirects to the automation home page.
    :param request:
    :return:
    """
    if request.method == "GET":
        # In case the user has just entered the page:
        return render(
            request,
            "srm_solver/signupuser.html",
            {"sign_form": UserCreationForm()},
        )
    else:  # in case the user has already posted the request
        if request.POST["password1"] == request.POST["password2"]:
            # Creating a new user:
            try:
                user = User.objects.create_user(
                    request.POST["username"],
                    password=request.POST["password1"],
                )
                user.save()
                login(request, user)
                return redirect("home")
            except IntegrityError:
                return render(
                    request,
                    "srm_solver/signupuser.html",
                    {
                        "sign_form": UserCreationForm(),
                        "error": "That username has already been taken.",
                    },
                )
        else:
            return render(
                request,
                "srm_solver/signupuser.html",
                {
                    "sign_form": UserCreationForm(),
                    "error": "Passwords did not match.",
                },
            )


def loginuser(request):
    """
    Logs in the user and redirects to the automation home page.
    :param request:
    :return:
    """
    if request.method == "GET":
        # In case the user has just entered the page:
        return render(
            request,
            "srm_solver/loginuser.html",
            {"log_form": AuthenticationForm()},
        )
    else:  # in case the user has already posted the request
        # Checking if the user credentials are correct:
        user = authenticate(
            request,
            username=request.POST["username"],
            password=request.POST["password"],
        )
        if (
            user is None
        ):  # in case the user does not exist, seng him back to log in page with an error
            return render(
                request,
                "srm_solver/loginuser.html",
                {
                    "form": AuthenticationForm(),
                    "error": "Username and password do not exist",
                },
            )
        else:  # in case the user has been successfully authenticated
            # Redirects the user to the main automation page after log in has been concluded successfully.
            login(request, user)
            return redirect("home")


def logoutuser(request):
    # Method is 'POST' since some browsers will not work with 'GET'. Some browsers automatically load 'GET' requests.
    # This automatic loading of some items would log out the user as soon as the page loads.
    if request.method == "POST":
        logout(request)
        # In case the user logs out, he is redirected to the home page.
        return redirect("home")


def create_srm(request):
    return redirect("create_srm_propellant")


def create_srm_propellant(request):
    return render(request, "srm_solver/create_srm_propellant.html")


def create_srm_grain(request):
    return render(request, "srm_solver/create_srm_grain.html")


def create_srm_structure(request):
    return render(request, "srm_solver/create_srm_structure.html")


def create_srm_rocket(request):
    return render(request, "srm_solver/create_srm_rocket.html")


def create_srm_recovery(request):
    return render(request, "srm_solver/create_srm_recovery.html")
