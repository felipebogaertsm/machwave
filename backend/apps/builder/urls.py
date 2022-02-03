# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from django.urls import path

import apps.builder.views as views

urlpatterns = [
    path("rocket/", views.RocketAPI.as_view(), name="rocket_modeler"),
    path("motor/", views.MotorAPI.as_view(), name="motor_modeler"),
]
