# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from django.shortcuts import redirect


def unauthenticated_user(view_func):
    """
    Redirects unauthenticated user to a specific URL.
    """
    redirect_url = "home"

    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(redirect_url)
        else:
            return view_func(request, *args, **kwargs)

    return wrapper_func
