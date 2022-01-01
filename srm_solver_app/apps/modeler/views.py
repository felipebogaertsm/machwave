# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view

from apps.modeler.models import Motor, Rocket
from apps.modeler.serializers import MotorSerializer, RocketSerializer


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


@login_required(login_url="login_user")
@api_view(["POST"])
def create_rocket(request):
    data = request.data
    user = request.user

    rocket_name = data["name"]
    mass_wo_motor = data["mass_wo_motor"]
    drag_coefficient = data["drag_coefficient"]
    rocket_diameter = data["rocket_diameter"]

    rocket = Rocket.objects.create(
        name=rocket_name,
        mass_wo_motor=mass_wo_motor,
        drag_coefficient=drag_coefficient,
        rocket_diameter=rocket_diameter,
        created_by=user,
    )

    serialized_data = RocketSerializer(rocket)
    return serialized_data
