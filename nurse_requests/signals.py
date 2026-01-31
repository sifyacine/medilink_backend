import django.dispatch

# Signal sent when a new request is created
request_created = django.dispatch.Signal()

# Signal sent when request status changes
request_status_changed = django.dispatch.Signal()

# Signal sent when a nurse submits an offer
nurse_offer_submitted = django.dispatch.Signal()
