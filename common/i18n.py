"""
Internationalization (i18n) utilities for multilingual content.

Provides:
- Language detection from requests
- Serializer mixins for automatic localization
- Model mixins for multilingual fields
- Utility functions for content localization
"""
from typing import Optional, List, Dict, Any
from rest_framework import serializers
from django.db import models


# Supported languages in the platform
SUPPORTED_LANGUAGES = ['en', 'ar', 'fr']
DEFAULT_LANGUAGE = 'en'

# Language display names
LANGUAGE_NAMES = {
    'en': 'English',
    'ar': 'العربية',  # Arabic
    'fr': 'Français',  # French
}


def get_language_from_request(request) -> str:
    """
    Extract preferred language from request.
    
    Checks in order:
    1. Query parameter: ?lang=ar
    2. HTTP Header: Accept-Language
    3. User preference (if authenticated)
    4. Default to English
    
    Args:
        request: DRF Request object
        
    Returns:
        Language code ('en', 'ar', 'fr')
    """
    # 1. Check query parameter
    if request:
        lang = request.query_params.get('lang', '').lower()
        if lang in SUPPORTED_LANGUAGES:
            return lang
        
        # 2. Check Accept-Language header
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        if accept_language:
            # Parse Accept-Language header (e.g., "ar,en;q=0.9,fr;q=0.8")
            for part in accept_language.split(','):
                lang_code = part.split(';')[0].strip().lower()
                # Handle language codes like 'en-US' -> 'en'
                lang_code = lang_code.split('-')[0]
                if lang_code in SUPPORTED_LANGUAGES:
                    return lang_code
        
        # 3. Check user preference (if authenticated and has language preference)
        if hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user
            # Try to get language from user profile
            if hasattr(user, 'preferred_language') and user.preferred_language:
                if user.preferred_language in SUPPORTED_LANGUAGES:
                    return user.preferred_language
    
    # 4. Default to English
    return DEFAULT_LANGUAGE


def get_localized_field(obj, field_name: str, language: str = 'en') -> str:
    """
    Get localized field value from an object.
    
    Looks for field_{language} (e.g., title_ar, description_fr).
    Falls back to the base field if localized version is empty.
    
    Args:
        obj: Model instance
        field_name: Base field name (e.g., 'title', 'description')
        language: Language code ('en', 'ar', 'fr')
        
    Returns:
        Localized field value or base field value as fallback
    """
    if language not in SUPPORTED_LANGUAGES:
        language = DEFAULT_LANGUAGE
    
    # Try localized field first
    localized_field = f'{field_name}_{language}'
    localized_value = getattr(obj, localized_field, None)
    
    if localized_value:
        return localized_value
    
    # Fall back to base field
    base_value = getattr(obj, field_name, '')
    return base_value or ''


def get_all_translations(obj, field_name: str) -> Dict[str, str]:
    """
    Get all translations for a field.
    
    Args:
        obj: Model instance
        field_name: Base field name (e.g., 'title', 'description')
        
    Returns:
        Dict with language codes as keys and translations as values
    """
    result = {}
    base_value = getattr(obj, field_name, '')
    
    for lang in SUPPORTED_LANGUAGES:
        localized_field = f'{field_name}_{lang}'
        localized_value = getattr(obj, localized_field, None)
        result[lang] = localized_value if localized_value else base_value
    
    return result


class MultilingualSerializerMixin:
    """
    Serializer mixin for automatic content localization.
    
    Usage:
        class ServiceSerializer(MultilingualSerializerMixin, serializers.ModelSerializer):
            class Meta:
                model = Service
                multilingual_fields = ['title', 'description']
                fields = ['id', 'title', 'description', ...]
    
    The mixin will:
    1. Replace 'title' and 'description' with localized versions
    2. Add 'localized_title' and 'localized_description' fields
    3. Include all translations if 'include_all_translations' query param is set
    """
    
    def get_request_language(self) -> str:
        """Get language from request context."""
        request = self.context.get('request')
        return get_language_from_request(request)
    
    def to_representation(self, instance):
        """Add localized fields to representation."""
        data = super().to_representation(instance)
        
        # Get multilingual fields from Meta
        multilingual_fields = getattr(self.Meta, 'multilingual_fields', [])
        if not multilingual_fields:
            return data
        
        language = self.get_request_language()
        request = self.context.get('request')
        include_all = request.query_params.get('include_all_translations', '').lower() == 'true' if request else False
        
        for field in multilingual_fields:
            if hasattr(instance, field):
                # Add localized value
                localized_value = get_localized_field(instance, field, language)
                data[f'localized_{field}'] = localized_value
                
                # Optionally include all translations
                if include_all:
                    data[f'{field}_translations'] = get_all_translations(instance, field)
        
        # Add current language to response
        data['_language'] = language
        
        return data


class LocalizedFieldsMixin:
    """
    Simplified mixin that replaces base fields with localized versions.
    
    Usage:
        class ServiceListSerializer(LocalizedFieldsMixin, serializers.ModelSerializer):
            class Meta:
                model = Service
                localize_fields = ['title', 'description']
                fields = ['id', 'title', 'description', 'price']
    
    This will replace 'title' and 'description' values with their
    localized versions based on the request language.
    """
    
    def to_representation(self, instance):
        """Replace base fields with localized versions."""
        data = super().to_representation(instance)
        
        localize_fields = getattr(self.Meta, 'localize_fields', [])
        if not localize_fields:
            return data
        
        request = self.context.get('request')
        language = get_language_from_request(request)
        
        for field in localize_fields:
            if field in data and hasattr(instance, field):
                data[field] = get_localized_field(instance, field, language)
        
        return data


class MultilingualModelMixin:
    """
    Model mixin providing helper methods for multilingual fields.
    
    Usage:
        class Service(MultilingualModelMixin, models.Model):
            title = models.CharField(max_length=200)
            title_en = models.CharField(max_length=200, blank=True)
            title_ar = models.CharField(max_length=200, blank=True)
            title_fr = models.CharField(max_length=200, blank=True)
            
            MULTILINGUAL_FIELDS = ['title', 'description']
    """
    
    MULTILINGUAL_FIELDS: List[str] = []
    
    def get_localized(self, field_name: str, language: str = 'en') -> str:
        """Get localized value for a field."""
        return get_localized_field(self, field_name, language)
    
    def get_all_localized(self, language: str = 'en') -> Dict[str, str]:
        """Get all multilingual fields in the specified language."""
        result = {}
        for field in self.MULTILINGUAL_FIELDS:
            result[field] = self.get_localized(field, language)
        return result
    
    def set_translation(self, field_name: str, language: str, value: str) -> None:
        """Set translation for a specific field and language."""
        if language not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {language}")
        
        localized_field = f'{field_name}_{language}'
        if hasattr(self, localized_field):
            setattr(self, localized_field, value)
        else:
            raise AttributeError(f"Field {localized_field} does not exist")


# Serializer field for explicit localization
class LocalizedCharField(serializers.SerializerMethodField):
    """
    Serializer field that returns localized content.
    
    Usage:
        class ServiceSerializer(serializers.ModelSerializer):
            title = LocalizedCharField(field_name='title')
            description = LocalizedCharField(field_name='description')
    """
    
    def __init__(self, field_name: str, **kwargs):
        self.localized_field_name = field_name
        super().__init__(**kwargs)
    
    def to_representation(self, instance):
        request = self.context.get('request')
        language = get_language_from_request(request)
        return get_localized_field(instance, self.localized_field_name, language)


class TranslationsField(serializers.SerializerMethodField):
    """
    Serializer field that returns all translations for a field.
    
    Usage:
        class ServiceSerializer(serializers.ModelSerializer):
            title_translations = TranslationsField(field_name='title')
    """
    
    def __init__(self, field_name: str, **kwargs):
        self.translation_field_name = field_name
        super().__init__(**kwargs)
    
    def to_representation(self, instance):
        return get_all_translations(instance, self.translation_field_name)
