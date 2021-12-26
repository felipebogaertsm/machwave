# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view

from apps.modeler.models import Motor
from apps.modeler.serializers import MotorSerializer


@login_required(login_url="login_user")
def rocket_modeler(request):
    return render(request, "modeler/rocket.html")


@login_required(login_url="login_user")
def ib_modeler(request):
    return render(request, "modeler/ib.html")


@login_required(login_url="login_user")
def structure_modeler(request):
    return render(request, "modeler/structure.html")


@login_required(login_url="login_user")
def recovery_modeler(request):
    return render(request, "modeler/recovery.html")


@login_required(login_url="login_user")
@api_view(["POST"])
def create_rocket_motor(request):
    data = request.data
    user = request.user

    motor_name = data["name"]
    motor_manufacturer = data["manufacturer"]

    motor = Motor.objects.create(
        name=motor_name,
        manufacturer=motor_manufacturer,
        created_by=user,
    )

    serialized_data = MotorSerializer(motor)
    return serialized_data
