from django.contrib import admin

from platform_content.models import (
    LandingPageSection,
    PlatformAnnouncement,
    FAQ,
    BlogPost,
    ContactInfo,
    PlatformSocialLink,
)


@admin.register(LandingPageSection)
class LandingPageSectionAdmin(admin.ModelAdmin):
    list_display = ['section_key', 'title_en', 'is_active', 'display_order', 'updated_at']
    list_filter = ['is_active']
    search_fields = ['section_key', 'title_en']
    ordering = ['display_order']
    readonly_fields = ['updated_at', 'updated_by']


@admin.register(PlatformAnnouncement)
class PlatformAnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title_en', 'announcement_type', 'target_audience', 'is_active', 'starts_at', 'ends_at', 'created_at']
    list_filter = ['announcement_type', 'target_audience', 'is_active']
    search_fields = ['title_en']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'created_by']


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question_en', 'category', 'is_active', 'display_order']
    list_filter = ['category', 'is_active']
    search_fields = ['question_en', 'answer_en']
    ordering = ['display_order']
    readonly_fields = ['created_at', 'updated_at', 'created_by']


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title_en', 'slug', 'status', 'author', 'published_at', 'created_at']
    list_filter = ['status']
    search_fields = ['title_en', 'slug', 'tags']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'published_at', 'author']
    prepopulated_fields = {'slug': ('title_en',)}


@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    list_display = ['email', 'support_email', 'phone', 'updated_at']
    readonly_fields = ['updated_at', 'updated_by']

    def has_add_permission(self, request):
        # Singleton — disallow adding a second row via Django admin
        return not ContactInfo.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PlatformSocialLink)
class PlatformSocialLinkAdmin(admin.ModelAdmin):
    list_display = ['platform', 'url', 'is_active', 'display_order']
    list_filter = ['platform', 'is_active']
    ordering = ['display_order', 'platform']
