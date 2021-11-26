# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required(login_url="login_user")
def rocket_modeler(request):
    return render(request, "modeler/rocket.html")
