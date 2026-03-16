"""
Platform content models — CMS for landing page, blog, FAQs, announcements,
contact info, and platform-level social links.

All content that appears on the public-facing Medilink website is managed
through these models and exposed via read-only public endpoints as well as
write endpoints restricted to admin users with the CONTENT_EDITOR sub-role.
"""
from django.db import models
from django.utils import timezone

from social_media.models import SocialMediaPlatform


# ---------------------------------------------------------------------------
# Landing Page Sections
# ---------------------------------------------------------------------------

class LandingPageSection(models.Model):
    """
    A named section on the Medilink landing/home page.

    Each section has a unique ``section_key`` (e.g. 'hero', 'features',
    'testimonials', 'stats', 'cta') that the frontend uses to locate and
    render the correct section.  Content is stored in three languages.
    """
    section_key = models.SlugField(
        max_length=100,
        unique=True,
        help_text="Unique key used by the frontend to identify this section (e.g. 'hero', 'features')",
    )
    title_en = models.CharField(max_length=300, blank=True)
    title_ar = models.CharField(max_length=300, blank=True)
    title_fr = models.CharField(max_length=300, blank=True)
    subtitle_en = models.TextField(blank=True)
    subtitle_ar = models.TextField(blank=True)
    subtitle_fr = models.TextField(blank=True)
    body_en = models.TextField(blank=True)
    body_ar = models.TextField(blank=True)
    body_fr = models.TextField(blank=True)
    image = models.ImageField(
        upload_to='platform/sections/',
        null=True,
        blank=True,
        help_text='Hero or section illustration image',
    )
    cta_text_en = models.CharField(max_length=100, blank=True)
    cta_text_ar = models.CharField(max_length=100, blank=True)
    cta_text_fr = models.CharField(max_length=100, blank=True)
    cta_url = models.URLField(blank=True)
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text='Whether this section is visible on the public site',
    )
    display_order = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text='Sort order on the landing page (lower = higher on page)',
    )
    updated_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_landing_sections',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'landing_page_sections'
        verbose_name = 'Landing Page Section'
        verbose_name_plural = 'Landing Page Sections'
        ordering = ['display_order']

    def __str__(self):
        return f'Section: {self.section_key}'


# ---------------------------------------------------------------------------
# Platform Announcements
# ---------------------------------------------------------------------------

class PlatformAnnouncement(models.Model):
    """
    Timed platform-wide announcements shown to users (e.g. maintenance windows,
    new features, policy changes).

    The ``is_active`` flag combined with optional ``starts_at`` / ``ends_at``
    controls visibility.  The public endpoint filters to only active,
    in-range announcements.
    """

    class AnnouncementType(models.TextChoices):
        INFO    = 'INFO',    'Info'
        WARNING = 'WARNING', 'Warning'
        SUCCESS = 'SUCCESS', 'Success'
        DANGER  = 'DANGER',  'Danger'

    class TargetAudience(models.TextChoices):
        ALL       = 'ALL',       'All Users'
        PATIENTS  = 'PATIENTS',  'Patients Only'
        PROVIDERS = 'PROVIDERS', 'Providers Only'

    title_en = models.CharField(max_length=300)
    title_ar = models.CharField(max_length=300, blank=True)
    title_fr = models.CharField(max_length=300, blank=True)
    body_en = models.TextField()
    body_ar = models.TextField(blank=True)
    body_fr = models.TextField(blank=True)
    announcement_type = models.CharField(
        max_length=20,
        choices=AnnouncementType.choices,
        default=AnnouncementType.INFO,
        db_index=True,
    )
    target_audience = models.CharField(
        max_length=20,
        choices=TargetAudience.choices,
        default=TargetAudience.ALL,
        db_index=True,
    )
    is_active = models.BooleanField(default=True, db_index=True)
    starts_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When to start showing this announcement (null = always)',
    )
    ends_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When to stop showing this announcement (null = never)',
    )
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_announcements',
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'platform_announcements'
        verbose_name = 'Platform Announcement'
        verbose_name_plural = 'Platform Announcements'
        ordering = ['-created_at']

    def __str__(self):
        return self.title_en or f'Announcement #{self.pk}'

    @property
    def is_currently_active(self):
        """True if active and within optional date range."""
        if not self.is_active:
            return False
        now = timezone.now()
        if self.starts_at and now < self.starts_at:
            return False
        if self.ends_at and now > self.ends_at:
            return False
        return True


# ---------------------------------------------------------------------------
# FAQs
# ---------------------------------------------------------------------------

class FAQ(models.Model):
    """Frequently asked question with answer in up to three languages."""

    question_en = models.CharField(max_length=500)
    question_ar = models.CharField(max_length=500, blank=True)
    question_fr = models.CharField(max_length=500, blank=True)
    answer_en = models.TextField()
    answer_ar = models.TextField(blank=True)
    answer_fr = models.TextField(blank=True)
    category = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text='Grouping label (e.g. "Patients", "Providers", "Billing")',
    )
    display_order = models.PositiveIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_faqs',
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'faqs'
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
        ordering = ['display_order']

    def __str__(self):
        return self.question_en[:80]


# ---------------------------------------------------------------------------
# Blog Posts
# ---------------------------------------------------------------------------

class BlogPost(models.Model):
    """
    News / blog post entry.

    Supports three languages.  A post starts as DRAFT; admins publish it
    explicitly via the ``publish/`` action endpoint.
    """

    class PostStatus(models.TextChoices):
        DRAFT     = 'DRAFT',     'Draft'
        PUBLISHED = 'PUBLISHED', 'Published'
        ARCHIVED  = 'ARCHIVED',  'Archived'

    title_en = models.CharField(max_length=300)
    title_ar = models.CharField(max_length=300, blank=True)
    title_fr = models.CharField(max_length=300, blank=True)
    slug = models.SlugField(
        max_length=350,
        unique=True,
        db_index=True,
        help_text='URL-friendly identifier, auto-generated from English title',
    )
    content_en = models.TextField()
    content_ar = models.TextField(blank=True)
    content_fr = models.TextField(blank=True)
    excerpt_en = models.TextField(blank=True, max_length=500)
    excerpt_ar = models.TextField(blank=True, max_length=500)
    excerpt_fr = models.TextField(blank=True, max_length=500)
    cover_image = models.ImageField(
        upload_to='platform/blog/',
        null=True,
        blank=True,
    )
    author = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='blog_posts',
    )
    status = models.CharField(
        max_length=20,
        choices=PostStatus.choices,
        default=PostStatus.DRAFT,
        db_index=True,
    )
    tags = models.CharField(
        max_length=500,
        blank=True,
        help_text='Comma-separated tags (e.g. "health,news,providers")',
    )
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'blog_posts'
        verbose_name = 'Blog Post'
        verbose_name_plural = 'Blog Posts'
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.title_en or f'Post #{self.pk}'

    def publish(self):
        """Mark post as published with current timestamp."""
        self.status = self.PostStatus.PUBLISHED
        if not self.published_at:
            self.published_at = timezone.now()
        self.save(update_fields=['status', 'published_at', 'updated_at'])


# ---------------------------------------------------------------------------
# Contact Information  (singleton)
# ---------------------------------------------------------------------------

class ContactInfo(models.Model):
    """
    Platform contact information — only ONE row should ever exist (singleton).

    The ``save()`` override always forces pk=1 to enforce the singleton pattern.
    Use ``ContactInfo.objects.get_or_create(pk=1)`` to retrieve or initialise.
    """
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    support_email = models.EmailField(blank=True)
    whatsapp = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    office_hours = models.CharField(max_length=200, blank=True)
    updated_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_contact_info',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'contact_info'
        verbose_name = 'Contact Info'
        verbose_name_plural = 'Contact Info'

    def __str__(self):
        return f'Contact Info (email: {self.email})'

    def save(self, *args, **kwargs):
        """Enforce singleton: always save with pk=1."""
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Prevent deletion of the singleton row."""
        pass


# ---------------------------------------------------------------------------
# Platform Social Links
# ---------------------------------------------------------------------------

class PlatformSocialLink(models.Model):
    """
    Platform-level social media links (Facebook, Instagram, etc.) shown
    in the site footer and contact page.

    Distinct from the ``SocialMediaLink`` model which uses Generic FK to
    attach links to individual provider/user profiles.
    """
    platform = models.CharField(
        max_length=50,
        choices=SocialMediaPlatform.choices,
        help_text='Social media platform',
    )
    url = models.URLField(help_text='Full profile URL')
    custom_label = models.CharField(
        max_length=100,
        blank=True,
        help_text='Custom label (required when platform == OTHER)',
    )
    display_order = models.PositiveIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = 'platform_social_links'
        verbose_name = 'Platform Social Link'
        verbose_name_plural = 'Platform Social Links'
        ordering = ['display_order', 'platform']

    def __str__(self):
        return f'{self.get_platform_display()}: {self.url}'
