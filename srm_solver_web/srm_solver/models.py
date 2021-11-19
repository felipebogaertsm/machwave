from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.


class Propellant(models.Model):
    _id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)

    # Propellant properties:
    ce = models.FloatField()
    pp = models.FloatField()
    k_mix_ch = models.FloatField()
    k_2ph_ex = models.FloatField()
    t_0_ideal = models.FloatField()
    m_ch = models.FloatField()
    m_ex = models.FloatField()
    i_sp_frozen = models.FloatField()
    i_sp_shifting = models.FloatField()
    qsi_ch = models.FloatField()
    qsi_ex = models.FloatField()

    # Automatic fields:
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True)

    class Meta:
        verbose_name = "Propellant"
        verbose_name_plural = "Propellants"

    def __str__(self):
        return f"{self._id:.0f}_{self.name}"


class Bates(models.Model):
    _id = models.AutoField(primary_key=True)

    n = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    od_grain = models.FloatField()
    id_grain = models.FloatField()
    l_grain = models.FloatField()

    # Automatic fields:
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True)

    def __str__(self):
        return f"{self._id}"


class Structure(models.Model):
    _id = models.AutoField(primary_key=True)

    grain_spacing = models.FloatField(default=0.010)
    casing_id = models.FloatField()
    casing_od = models.FloatField()
    liner_thickness = models.FloatField()
    throat_diameter = models.FloatField()
    divergent_angle = models.FloatField()
    convergent_angle = models.FloatField()
    expansion_ratio = models.FloatField()
    casing_c_1 = models.FloatField(default=0.00506)
    casing_c_2 = models.FloatField(default=0.00000)

    yield_casing = models.FloatField()
    yield_bulkhead = models.FloatField()
    yield_nozzle = models.FloatField()

    screw_diameter = models.FloatField()
    screw_clearance_diameter = models.FloatField()
    screw_tensile_strength = models.FloatField()
    max_screw_count = models.IntegerField()

    # Automatic fields:
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True)


class Rocket(models.Model):
    _id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)

    mass_wo_motor = models.FloatField()
    drag_coefficient = models.FloatField()
    rocket_diameter = models.FloatField()

    # Automatic fields:
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True)


class Recovery(models.Model):
    _id = models.AutoField(primary_key=True)

    drogue_time = models.FloatField()
    drogue_drag_coeff = models.FloatField()
    drogue_diameter = models.FloatField()

    main_activation_height = models.FloatField()
    main_drag_coeff = models.FloatField()
    main_diameter = models.FloatField()

    # Automatic fields:
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True)


class Motor(models.Model):
    _id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    manufacturer = models.CharField(max_length=50)
    is_simulated = models.BooleanField(default=False, blank=True)

    # Foreign keys:
    propellant = models.ForeignKey(
        Propellant, on_delete=models.SET_NULL, blank=True, null=True
    )
    grain = models.ForeignKey(
        Bates, on_delete=models.SET_NULL, blank=True, null=True
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

    # Automatic fields:
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True)

    def __str__(self):
        return f"{self._id:.0f}_{self.name}_{self.user.username}"


class SimulationSettings(models.Model):
    eng_res = models.IntegerField(
        validators=[MinValueValidator(5), MaxValueValidator(1000)]
    )
    dt = models.FloatField(
        validators=[MinValueValidator(0.0001), MaxValueValidator(1)]
    )
    ddt = models.FloatField(default=10.0, blank=True)

    # Automatic fields:
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True)


class OperationSettings(models.Model):
    h_0 = models.FloatField(default=0.0, blank=True)
    igniter_pressure = models.FloatField(default=1.5, blank=True)
    rail_length = models.FloatField(default=5, blank=True)
    safety_factor = models.FloatField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )

    # Automatic fields:
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True)


class Simulation(models.Model):
    motor = models.ForeignKey(Motor, on_delete=models.CASCADE, blank=True)
    sim_settings = models.ForeignKey(
        SimulationSettings, on_delete=models.CASCADE, blank=True
    )
    op_settings = models.ForeignKey(
        OperationSettings, on_delete=models.CASCADE, blank=True
    )

    # Automatic fields:
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True)
