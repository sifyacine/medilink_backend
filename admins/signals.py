"""
Admin signals — wire the ``admin_action_performed`` custom signal.

Currently this module exists primarily to be imported by ``AdminsConfig.ready()``
and to define the custom signal that views can fire.  The actual log creation
is done directly in admin services (``admins/services.py``), so this module
is kept minimal and only exposes the signal for code that needs to fire it
manually without going through a service function.
"""
import django.dispatch

# Custom signal fired by admin views/services after every state-changing action.
# Receivers can attach here for notifications, cache invalidation, etc.
admin_action_performed = django.dispatch.Signal()
# Provides kwargs: action (str), target_obj, admin (User), ip (str), extra (dict)
