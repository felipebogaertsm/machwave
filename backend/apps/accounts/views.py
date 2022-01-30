# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from django.contrib import auth
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm

from apps.accounts.decorators import unauthenticated_user
from apps.accounts.forms import UserCreationForm


@unauthenticated_user
def register_view(request):
    form = UserCreationForm()

    if request.method == "GET":
        return render(request, "accounts/register.html", {"form": form})
    elif request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            form.save()
            user = authenticate(
                username=form.cleaned_data["email"],
                password=form.cleaned_data["password1"],
            )
            login(request, user)
            return redirect("home")
        else:
            return render(
                request,
                "accounts/register.html",
                {"form": form, "error": "Could not authenticate"},
            )


@unauthenticated_user
def login_view(request):
    form = AuthenticationForm()

    if request.method == "GET":
        return render(request, "accounts/login.html", {"form": form})
    elif request.method == "POST":
        user = authenticate(
            request,
            username=request.POST["username"],
            password=request.POST["password"],
        )

        if user is None:
            return render(
                request,
                "accounts/login.html",
                {"form": form, "error": "User not authenticated."},
            )
        else:
            login(request, user)
            return redirect("home")


def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("home")
