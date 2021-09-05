from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(PropellantWeb)
admin.site.register(BatesWeb)
admin.site.register(StructureWeb)
admin.site.register(RocketWeb)
admin.site.register(RecoveryWeb)
admin.site.register(MotorWeb)
admin.site.register(SimulationSettings)
admin.site.register(OperationSettings)
admin.site.register(Simulation)
