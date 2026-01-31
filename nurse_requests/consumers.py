import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()


class NurseRequestConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time nurse request updates.
    
    Channels/Rooms:
    - city_{city_name}_requests: Broadcasts to all nurses in a city
    - request_{request_id}_updates: Updates for a specific request (patient & accepted nurse)
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Determine user type and setup appropriate channels
        if await self.is_patient():
            # Patients subscribe to their specific request updates
            self.request_id = self.scope['url_route']['kwargs'].get('request_id')
            if self.request_id:
                self.room_group_name = f'request_{self.request_id}_updates'
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
        
        elif await self.is_nurse():
            # Nurses subscribe to their city's request broadcasts
            nurse = await self.get_nurse()
            if nurse:
                # TODO: Get nurse's city from their profile/location
                # For now, use a default city
                city = 'default_city'  # Replace with actual city logic
                self.room_group_name = f'city_{city}_requests'
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """
        Handle incoming messages from WebSocket.
        Not heavily used in this implementation as updates are server-driven.
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON'
            }))
    
    # Message handlers for different event types
    async def new_request(self, event):
        """
        Broadcast new request to nurses in the area.
        Triggered when a patient creates a request.
        """
        await self.send(text_data=json.dumps({
            'type': 'new_request',
            'request': event['request']
        }))
    
    async def request_updated(self, event):
        """
        Send request update to patient.
        Triggered when nurses respond or status changes.
        """
        await self.send(text_data=json.dumps({
            'type': 'request_updated',
            'request': event['request']
        }))
    
    async def new_offer(self, event):
        """
        Notify patient of a new nurse offer.
        """
        await self.send(text_data=json.dumps({
            'type': 'new_offer',
            'offer': event['offer']
        }))
    
    async def offer_accepted(self, event):
        """
        Notify nurse that their offer was accepted.
        """
        await self.send(text_data=json.dumps({
            'type': 'offer_accepted',
            'request': event['request']
        }))
    
    async def request_cancelled(self, event):
        """
        Notify nurse that request was cancelled.
        """
        await self.send(text_data=json.dumps({
            'type': 'request_cancelled',
            'request_id': event['request_id'],
            'reason': event.get('reason', '')
        }))
    
    # Database query helpers
    @database_sync_to_async
    def is_patient(self):
        """Check if user is a patient"""
        return hasattr(self.user, 'patient')
    
    @database_sync_to_async
    def is_nurse(self):
        """Check if user is a nurse provider"""
        return (
            hasattr(self.user, 'provider') and
            self.user.provider.provider_type == 'NURSE'
        )
    
    @database_sync_to_async
    def get_nurse(self):
        """Get nurse provider object"""
        try:
            return self.user.provider
        except:
            return None
