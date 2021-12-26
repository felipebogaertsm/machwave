# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from rest_framework import serializers

from apps.modeler.models import Motor


class MotorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Motor
        fields = "__all__"
