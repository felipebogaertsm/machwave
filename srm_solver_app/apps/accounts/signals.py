# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.template.loader import render_to_string

from utils.emails import send_email_to_user

USER_MODEL = settings.AUTH_USER_MODEL
DOMAIN = settings.DOMAIN_URL


@receiver(post_save, sender=USER_MODEL)
def user_post_save_receiver(sender, instance, created, *args, **kwargs):
    """
    Post user save signal.

    Sends an email to the new user.
    If email fails to be sent, user is deleted.
    """
    if created:
        try:
            mail_subject = "SRM Solver - Start designing your motors"
            mail_body = render_to_string(
                "accounts/signin_email.html",
                {
                    "user": instance,
                    "domain": DOMAIN,
                },
            )

            send_email_to_user(
                user=instance,
                subject=mail_subject,
                body_html=mail_body,
            )
        except:
            instance.delete()
