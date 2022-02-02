# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from django.urls import path

import apps.accounts.views as views

urlpatterns = [
    path("user/me/", views.MyUserAPI, name="my_user_api"),
    path("user/<str:pk>/", views.UserAPI, name="user_api"),
]
