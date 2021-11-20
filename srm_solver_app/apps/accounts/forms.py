# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm

from django_countries.fields import CountryField

from apps.accounts.models import User


class UserCreationForm(UserCreationForm):
    """
    Form for creating new users, meant to replace the original one.
    """

    email = forms.EmailField(max_length=100)
    full_name = forms.CharField(max_length=100, required=False)
    country = CountryField(blank=True).formfield()
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(
        label="Confirm Password", widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ("email", "full_name", "country", "password1", "password2")
