# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

USER_MODEL = settings.AUTH_USER_MODEL


class Propellant(models.Model):
    choices = (
        ("KNSB", "KNSB"),
        ("KNSB-NAKKA", "KNSB-NAKKA"),
        ("KNDX", "KNDX"),
        ("KNER", "KNER"),
    )

    # Propellant name:
    name = models.CharField(choices=choices)

    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_by = models.ForeignKey(
        USER_MODEL, on_delete=models.CASCADE, blank=True
    )


class BatesGrain(models.Model):
    """
    Each object derived from this model can contain multiple linked objects,
    derived from "BatesGrainSegment".
    """

    # Grain spacing [m]:
    grain_spacing = models.FloatField(default=0.010)

    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_by = models.ForeignKey(
        USER_MODEL, on_delete=models.CASCADE, blank=True
    )


class BatesGrainSegment(models.Model):
    """
    BATES grain segment model. This model is linked by a ForeignKey to
    "BatesGrain" model.
    """

    # Segment outer diameter [m]:
    segment_od = models.FloatField()
    # Segment inner diameter [m]:
    segment_id = models.FloatField()
    # Segment length [m]:
    segment_length = models.FloatField()

    # Link to "BatesGrain" model:
    grain = models.ForeignKey(BatesGrain, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_by = models.ForeignKey(
        USER_MODEL, on_delete=models.CASCADE, blank=True
    )


class Nozzle(models.Model):
    throat_diameter = models.FloatField()
    divergent_angle = models.FloatField()
    convergent_angle = models.FloatField()
    expansion_ratio = models.FloatField()
    yield_strength = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_by = models.ForeignKey(
        USER_MODEL, on_delete=models.CASCADE, blank=True
    )


class Structure(models.Model):

    # Casing internal diameter [m]:
    casing_id = models.FloatField()
    # Casing outer diameter [m]:
    casing_od = models.FloatField()
    # Liner thickness [m]:
    liner_thickness = models.FloatField()

    casing_c_1 = models.FloatField(default=0.00506)
    casing_c_2 = models.FloatField(default=0.00000)

    yield_casing = models.FloatField()
    yield_bulkhead = models.FloatField()

    screw_diameter = models.FloatField()
    screw_clearance_diameter = models.FloatField()
    screw_tensile_strength = models.FloatField()
    max_screw_count = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_by = models.ForeignKey(
        USER_MODEL, on_delete=models.CASCADE, blank=True
    )


class Rocket(models.Model):
    name = models.CharField(max_length=50)

    mass_wo_motor = models.FloatField()
    drag_coefficient = models.FloatField()
    rocket_diameter = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_by = models.ForeignKey(
        USER_MODEL, on_delete=models.CASCADE, blank=True
    )


class Recovery(models.Model):

    drogue_time = models.FloatField()
    drogue_drag_coeff = models.FloatField()
    drogue_diameter = models.FloatField()

    main_activation_height = models.FloatField()
    main_drag_coeff = models.FloatField()
    main_diameter = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_by = models.ForeignKey(
        USER_MODEL, on_delete=models.CASCADE, blank=True
    )


class Motor(models.Model):
    name = models.CharField(max_length=50)
    manufacturer = models.CharField(max_length=50)
    is_simulated = models.BooleanField(default=False, blank=True)

    # Foreign keys:
    propellant = models.ForeignKey(
        Propellant, on_delete=models.SET_NULL, blank=True, null=True
    )
    grain = models.ForeignKey(
        BatesGrain, on_delete=models.SET_NULL, blank=True, null=True
    )
    structure = models.ForeignKey(
        Structure, on_delete=models.SET_NULL, blank=True, null=True
    )
    rocket = models.ForeignKey(
        Rocket, on_delete=models.SET_NULL, blank=True, null=True
    )
    recovery = models.ForeignKey(
        Recovery, on_delete=models.SET_NULL, blank=True, null=True
    )

    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_by = models.ForeignKey(
        USER_MODEL, on_delete=models.CASCADE, blank=True
    )


class SimulationSettings(models.Model):
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


class OperationSettings(models.Model):
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
    motor = models.ForeignKey(Motor, on_delete=models.CASCADE, blank=True)
    sim_settings = models.ForeignKey(
        SimulationSettings, on_delete=models.CASCADE, blank=True
    )
    op_settings = models.ForeignKey(
        OperationSettings, on_delete=models.CASCADE, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_by = models.ForeignKey(
        USER_MODEL, on_delete=models.CASCADE, blank=True
    )
