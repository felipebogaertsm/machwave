# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(
        self,
        email,
        password=None,
        is_active=True,
        is_staff=False,
        is_admin=False,
    ):
        if not password:
            raise ValueError("Users must have a valid password.")

        user = self.model(email=self.normalize_email(email))
        user.set_password(password)

        user.is_active = is_active
        user.is_staff = is_staff
        user.is_admin = is_admin

        user.save(using=self._db)

        return user

    def create_staffuser(self, email, password=None):
        user = self.create_user(email, password=password, is_staff=True)
        return user

    def create_superuser(self, email, password=None):
        user = self.create_user(
            email=email, password=password, is_staff=True, is_admin=True
        )
        return user
