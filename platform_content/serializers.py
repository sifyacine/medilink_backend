"""
Serializers for platform_content models.

Two sets:
  - Admin serializers  (full write access, IsAdmin required)
  - Public serializers (read-only, AllowAny, only active/published content)
"""
from rest_framework import serializers

from platform_content.models import (
    LandingPageSection,
    PlatformAnnouncement,
    FAQ,
    BlogPost,
    ContactInfo,
    PlatformSocialLink,
    LegalDocument,
)


# ---------------------------------------------------------------------------
# Admin serializers  (full CRUD)
# ---------------------------------------------------------------------------

class AdminLandingPageSectionSerializer(serializers.ModelSerializer):
    updated_by_email = serializers.EmailField(source='updated_by.email', read_only=True)
    image = serializers.ImageField(required=False, allow_null=True)

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

    def validate(self, attrs):
        starts_at = attrs.get('starts_at')
        ends_at = attrs.get('ends_at')
        if starts_at and ends_at and ends_at <= starts_at:
            raise serializers.ValidationError(
                {'ends_at': 'ends_at must be after starts_at.'}
            )
        return attrs


class AdminFAQSerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)

    class Meta:
        model = FAQ
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'updated_at')

    def validate_question_en(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('English question is required.')
        return value.strip()

    def validate_answer_en(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('English answer is required.')
        return value.strip()


class AdminBlogPostSerializer(serializers.ModelSerializer):
    author_email = serializers.EmailField(source='author.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

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

    def validate(self, attrs):
        platform = attrs.get('platform', getattr(self.instance, 'platform', None))
        custom_label = attrs.get('custom_label', getattr(self.instance, 'custom_label', ''))
        if platform == 'OTHER' and not custom_label:
            raise serializers.ValidationError(
                {'custom_label': 'custom_label is required when platform is OTHER.'}
            )
        return attrs


class AdminLegalDocumentSerializer(serializers.ModelSerializer):
    """Admin serializer for privacy policy / terms & conditions."""
    updated_by_email = serializers.EmailField(source='updated_by.email', read_only=True)
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)

    class Meta:
        model = LegalDocument
        fields = [
            'id',
            'document_type',
            'document_type_display',
            'title_en',
            'title_ar',
            'title_fr',
            'content_en',
            'content_ar',
            'content_fr',
            'version',
            'is_active',
            'updated_by',
            'updated_by_email',
            'updated_at',
            'created_at',
        ]
        read_only_fields = ('id', 'document_type', 'updated_by', 'updated_at', 'created_at')


# ---------------------------------------------------------------------------
# Public serializers  (read-only, only active/published content)
# ---------------------------------------------------------------------------

class PublicLandingPageSectionSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

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

    def get_image(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(obj.image.url) if request else obj.image.url


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
    cover_image = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = [
            'id', 'slug',
            'title_en', 'title_ar', 'title_fr',
            'excerpt_en', 'excerpt_ar', 'excerpt_fr',
            'content_en', 'content_ar', 'content_fr',
            'cover_image', 'author_name', 'tags',
            'published_at',
        ]

    def get_author_name(self, obj):
        if obj.author:
            return f"{obj.author.first_name} {obj.author.last_name}".strip() or obj.author.email
        return None

    def get_cover_image(self, obj):
        if not obj.cover_image:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(obj.cover_image.url) if request else obj.cover_image.url


class PublicContactInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactInfo
        fields = ['phone', 'email', 'support_email', 'whatsapp', 'address', 'office_hours']


class PublicPlatformSocialLinkSerializer(serializers.ModelSerializer):
    platform_display = serializers.CharField(source='get_platform_display', read_only=True)

    class Meta:
        model = PlatformSocialLink
        fields = ['id', 'platform', 'platform_display', 'url', 'custom_label', 'display_order']


class PublicLegalDocumentSerializer(serializers.ModelSerializer):
    """Public read-only serializer — exposes content and version, no audit fields."""
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)

    class Meta:
        model = LegalDocument
        fields = [
            'id',
            'document_type',
            'document_type_display',
            'title_en',
            'title_ar',
            'title_fr',
            'content_en',
            'content_ar',
            'content_fr',
            'version',
            'updated_at',
        ]
