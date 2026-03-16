"""
Serializers for platform_content models.

Two sets:
  - Admin serializers  (full write access)
  - Public serializers (read-only, minimal fields)
"""
from rest_framework import serializers

from platform_content.models import (
    LandingPageSection,
    PlatformAnnouncement,
    FAQ,
    BlogPost,
    ContactInfo,
    PlatformSocialLink,
)


# ---------------------------------------------------------------------------
# Admin serializers  (full CRUD)
# ---------------------------------------------------------------------------

class AdminLandingPageSectionSerializer(serializers.ModelSerializer):
    updated_by_email = serializers.EmailField(source='updated_by.email', read_only=True)

    class Meta:
        model = LandingPageSection
        fields = '__all__'
        read_only_fields = ('updated_by', 'updated_at')


class AdminPlatformAnnouncementSerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    is_currently_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = PlatformAnnouncement
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'updated_at')


class AdminFAQSerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)

    class Meta:
        model = FAQ
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'updated_at')


class AdminBlogPostSerializer(serializers.ModelSerializer):
    author_email = serializers.EmailField(source='author.email', read_only=True)

    class Meta:
        model = BlogPost
        fields = '__all__'
        read_only_fields = ('author', 'created_at', 'updated_at', 'published_at')


class AdminContactInfoSerializer(serializers.ModelSerializer):
    updated_by_email = serializers.EmailField(source='updated_by.email', read_only=True)

    class Meta:
        model = ContactInfo
        fields = '__all__'
        read_only_fields = ('updated_by', 'updated_at')


class AdminPlatformSocialLinkSerializer(serializers.ModelSerializer):
    platform_display = serializers.CharField(source='get_platform_display', read_only=True)

    class Meta:
        model = PlatformSocialLink
        fields = '__all__'


# ---------------------------------------------------------------------------
# Public serializers  (read-only, only active/published content)
# ---------------------------------------------------------------------------

class PublicLandingPageSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandingPageSection
        fields = [
            'id', 'section_key',
            'title_en', 'title_ar', 'title_fr',
            'subtitle_en', 'subtitle_ar', 'subtitle_fr',
            'body_en', 'body_ar', 'body_fr',
            'image',
            'cta_text_en', 'cta_text_ar', 'cta_text_fr', 'cta_url',
            'display_order',
        ]


class PublicPlatformAnnouncementSerializer(serializers.ModelSerializer):
    is_currently_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = PlatformAnnouncement
        fields = [
            'id',
            'title_en', 'title_ar', 'title_fr',
            'body_en', 'body_ar', 'body_fr',
            'announcement_type', 'target_audience',
            'starts_at', 'ends_at',
            'is_currently_active',
        ]


class PublicFAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = [
            'id', 'category',
            'question_en', 'question_ar', 'question_fr',
            'answer_en', 'answer_ar', 'answer_fr',
            'display_order',
        ]


class PublicBlogPostSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = [
            'id', 'slug',
            'title_en', 'title_ar', 'title_fr',
            'excerpt_en', 'excerpt_ar', 'excerpt_fr',
            'content_en', 'content_ar', 'content_fr',
            'cover_image', 'author_name', 'tags', 'published_at',
        ]

    def get_author_name(self, obj):
        if obj.author:
            return f"{obj.author.first_name} {obj.author.last_name}".strip()
        return None


class PublicContactInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactInfo
        fields = ['phone', 'email', 'support_email', 'whatsapp', 'address', 'office_hours']


class PublicPlatformSocialLinkSerializer(serializers.ModelSerializer):
    platform_display = serializers.CharField(source='get_platform_display', read_only=True)

    class Meta:
        model = PlatformSocialLink
        fields = ['id', 'platform', 'platform_display', 'url', 'custom_label', 'display_order']
