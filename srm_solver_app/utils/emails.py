# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from django.core.mail import EmailMessage


def send_email(user, subject, body_template):
    """
    Sends email to a user, given a subject and an HTML body template.
    """
    mail_to = user.email

    email = EmailMessage(subject, body_template, to=[mail_to])
    email.content_subtype = "html"
    email.send()
