# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from django.urls import path

import apps.accounts.views as views

urlpatterns = [
    path("login/", views.login_view, name="login_user"),
    path("logout/", views.logout_view, name="logout_user"),
    path("register/", views.register_view, name="register_user"),
]
