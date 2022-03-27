# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import uuid

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.builder.models import Motor, Rocket

USER_MODEL = settings.AUTH_USER_MODEL


class SimulationSettings(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    eng_res = models.IntegerField(
        validators=[MinValueValidator(5), MaxValueValidator(1000)]
    )
    dt = models.FloatField(
        validators=[MinValueValidator(0.0001), MaxValueValidator(1)]
    )
    ddt = models.FloatField(default=10.0, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_by = models.ForeignKey(
        USER_MODEL, on_delete=models.CASCADE, blank=True
    )


class OperationalSettings(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    h_0 = models.FloatField(default=0.0, blank=True)
    igniter_pressure = models.FloatField(default=1.5, blank=True)
    rail_length = models.FloatField(default=5, blank=True)
    safety_factor = models.FloatField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )

    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_by = models.ForeignKey(
        USER_MODEL, on_delete=models.CASCADE, blank=True
    )


class Simulation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    motor = models.ForeignKey(Motor, on_delete=models.CASCADE, blank=True)
    rocket = models.ForeignKey(Rocket, on_delete=models.CASCADE, blank=True)

    sim_settings = models.ForeignKey(
        SimulationSettings, on_delete=models.CASCADE, blank=True
    )
    op_settings = models.ForeignKey(
        OperationalSettings, on_delete=models.CASCADE, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_by = models.ForeignKey(
        USER_MODEL, on_delete=models.CASCADE, blank=True
    )
