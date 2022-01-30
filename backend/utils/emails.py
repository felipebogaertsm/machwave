# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from django.core.mail import EmailMessage


def send_email_to_user(user, subject, body_html):
    """
    Sends email to a user, given a subject and an HTML body template.
    """
    mail_to = user.email

    email = EmailMessage(subject, body_html, to=[mail_to])
    email.content_subtype = "html"
    email.send()
