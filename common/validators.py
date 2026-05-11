from django.core.exceptions import ValidationError


def validate_latitude(value):
    if not (-90 <= float(value) <= 90):
        raise ValidationError('Latitude must be between -90 and 90.')


def validate_longitude(value):
    if not (-180 <= float(value) <= 180):
        raise ValidationError('Longitude must be between -180 and 180.')
