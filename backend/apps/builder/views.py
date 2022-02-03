# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.builder.models import (
    Motor,
    Rocket,
    BatesGrainSegment,
    BatesGrain,
    Recovery,
)
from apps.builder.serializers import MotorSerializer, RocketSerializer


class RocketAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
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


class MotorAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
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


class BatesGrainAPI(APIView):
    permission_classes = [IsAuthenticated]


class BatesGrainSegmentAPI(APIView):
    permission_classes = [IsAuthenticated]


class NozzleAPI(APIView):
    permission_classes = [IsAuthenticated]


class StructureAPI(APIView):
    permission_classes = [IsAuthenticated]


class RecoveryAPI(APIView):
    permission_classes = [IsAuthenticated]


class StructureAPI(APIView):
    permission_classes = [IsAuthenticated]
