from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)

@receiver(user_logged_in)
def on_user_logged_in(sender, user, request, **kwargs):
    # Disabled to prevent running side-effects on every login.
    logger.info("on_user_logged_in called for %s but handler is disabled.", getattr(user, "username", user))
    return
