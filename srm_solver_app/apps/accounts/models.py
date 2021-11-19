# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.template.loader import render_to_string

from django_countries.fields import CountryField

from utils.emails import send_email


class UserManager(BaseUserManager):
    def create_user(
        self,
        email,
        password=None,
        is_active=True,
        is_staff=False,
        is_admin=False,
    ):
        if not email:
            raise ValueError("Users must have an email address.")
        if not password:
            raise ValueError("Users must have a valid password.")

        user = self.model(email=self.normalize_email(email))
        user.set_password(password)

        user.is_active = is_active
        user.is_staff = is_staff
        user.is_admin = is_admin

        user.save(using=self._db)

        try:
            user.send_signin_email()  # sending activation email
        except:  # if email does not get sent
            user.delete()

        return user

    def create_staffuser(self, email, password=None):
        user = self.create_user(email, password=password, is_staff=True)
        return user

    def create_superuser(self, email, password=None):
        user = self.create_user(
            email=email, password=password, is_staff=True, is_admin=True
        )
        return user


class User(AbstractBaseUser):
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    email = models.EmailField(max_length=200, unique=True)
    full_name = models.CharField(max_length=200, blank=True, null=True)
    country = CountryField()

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.email

    def get_short_name(self):
        try:
            return self.email.split("@")[0]
        except:
            return self.email

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    def send_signin_email(self):
        domain = settings.DOMAIN_URL
        mail_subject = "SRM Solver - Start designing your motors!"
        mail_body = render_to_string(
            "accounts/signin_email.html",
            {
                "user": self,
                "domain": domain,
            },
        )

        send_email(user=self, subject=mail_subject, body_template=mail_body)
