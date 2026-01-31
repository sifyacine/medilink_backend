from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .serializers import (
    NurseServiceRequestDetailSerializer,
    NurseOfferSerializer,
    NurseAvailableRequestSerializer
)


def broadcast_new_request_to_nurses(request_obj):
    """
    Broadcast a new request to all nurses in the same city.
    Called when a patient creates a request.
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    
    # Serialize request data
    serializer = NurseAvailableRequestSerializer(request_obj)
    
    # Broadcast to city channel
    city_group = f'city_{request_obj.city}_requests'
    
    async_to_sync(channel_layer.group_send)(
        city_group,
        {
            'type': 'new_request',
            'request': serializer.data
        }
    )


def notify_patient_of_offer(request_obj, offer):
    """
    Notify patient when a nurse responds with an offer.
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    
    # Serialize offer data
    offer_serializer = NurseOfferSerializer(offer)
    request_serializer = NurseServiceRequestDetailSerializer(request_obj)
    
    # Send to patient's request channel
    request_group = f'request_{request_obj.id}_updates'
    
    async_to_sync(channel_layer.group_send)(
        request_group,
        {
            'type': 'new_offer',
            'offer': offer_serializer.data,
            'request': request_serializer.data
        }
    )


def notify_request_status_change(request_obj):
    """
    Notify relevant parties when request status changes.
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    
    # Serialize request
    serializer = NurseServiceRequestDetailSerializer(request_obj)
    
    # Notify patient
    request_group = f'request_{request_obj.id}_updates'
    async_to_sync(channel_layer.group_send)(
        request_group,
        {
            'type': 'request_updated',
            'request': serializer.data
        }
    )


def notify_nurse_offer_accepted(request_obj, nurse):
    """
    Notify nurse when their offer is accepted.
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    
    serializer = NurseServiceRequestDetailSerializer(request_obj)
    
    # Create a nurse-specific channel (requires nurse to be connected)
    # For production, you might want to use push notifications here
    request_group = f'request_{request_obj.id}_updates'
    
    async_to_sync(channel_layer.group_send)(
        request_group,
        {
            'type': 'offer_accepted',
            'request': serializer.data
        }
    )


def notify_request_cancelled(request_obj):
    """
    Notify all interested parties that request was cancelled.
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    
    request_group = f'request_{request_obj.id}_updates'
    
    async_to_sync(channel_layer.group_send)(
        request_group,
        {
            'type': 'request_cancelled',
            'request_id': request_obj.id,
            'reason': request_obj.cancellation_reason
        }
    )
