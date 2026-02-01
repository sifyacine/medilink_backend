"""Admin configuration for reviews app."""
from django.contrib import admin
from django.utils.html import format_html

from reviews.models import Review, ReviewAggregate, ReviewHelpful


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Admin interface for Review model."""
    list_display = [
        'id', 'reviewer', 'reviewed_type', 'rating_display',
        'status', 'created_at'
    ]
    list_filter = ['status', 'rating', 'reviewed_content_type', 'created_at']
    search_fields = ['reviewer__email', 'text', 'title']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Review Info', {
            'fields': ('id', 'reviewer', 'status')
        }),
        ('Target', {
            'fields': ('reviewed_content_type', 'reviewed_object_id')
        }),
        ('Context', {
            'fields': ('context_content_type', 'context_object_id'),
            'classes': ('collapse',)
        }),
        ('Content', {
            'fields': ('rating', 'title', 'text', 'image')
        }),
        ('Response', {
            'fields': ('response', 'response_at', 'response_by'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def reviewed_type(self, obj):
        """Display the type of reviewed object."""
        return obj.reviewed_content_type.model.title()
    reviewed_type.short_description = 'Reviewed Type'
    
    def rating_display(self, obj):
        """Display rating with stars."""
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="color: gold;">{}</span>', stars)
    rating_display.short_description = 'Rating'
    
    actions = ['hide_reviews', 'activate_reviews', 'flag_reviews']
    
    def hide_reviews(self, request, queryset):
        """Hide selected reviews."""
        count = queryset.update(status='HIDDEN')
        self.message_user(request, f'{count} reviews hidden.')
    hide_reviews.short_description = 'Hide selected reviews'
    
    def activate_reviews(self, request, queryset):
        """Activate selected reviews."""
        count = queryset.update(status='ACTIVE')
        self.message_user(request, f'{count} reviews activated.')
    activate_reviews.short_description = 'Activate selected reviews'
    
    def flag_reviews(self, request, queryset):
        """Flag selected reviews for moderation."""
        count = queryset.update(status='FLAGGED')
        self.message_user(request, f'{count} reviews flagged.')
    flag_reviews.short_description = 'Flag selected reviews'


@admin.register(ReviewAggregate)
class ReviewAggregateAdmin(admin.ModelAdmin):
    """Admin interface for ReviewAggregate model."""
    list_display = [
        'id', 'content_type', 'object_id',
        'average_rating', 'review_count', 'updated_at'
    ]
    list_filter = ['content_type']
    search_fields = ['object_id']
    readonly_fields = ['id', 'updated_at']


@admin.register(ReviewHelpful)
class ReviewHelpfulAdmin(admin.ModelAdmin):
    """Admin interface for ReviewHelpful model."""
    list_display = ['id', 'review', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email']
    readonly_fields = ['id', 'created_at']
