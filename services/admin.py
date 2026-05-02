from django.contrib import admin
from django.utils.html import format_html
from services.models import Service, DoctorService, NurseService, ProviderCustomService


# ---------------------------------------------------------------------------
# Inlines
# ---------------------------------------------------------------------------

class NurseServiceInline(admin.TabularInline):
    """Shows which nurses have added this service to their profile."""
    model = NurseService
    extra = 0
    readonly_fields = ['nurse', 'custom_price', 'effective_price', 'is_available', 'created_at']
    fields = ['nurse', 'custom_price', 'effective_price', 'is_available', 'created_at']
    can_delete = False
    show_change_link = True
    verbose_name = 'Nurse offering this service'
    verbose_name_plural = 'Nurses offering this service'


class DoctorServiceInline(admin.TabularInline):
    """Shows which doctors have added this service to their profile."""
    model = DoctorService
    extra = 0
    readonly_fields = ['doctor', 'custom_price', 'effective_price', 'is_available', 'created_at']
    fields = ['doctor', 'custom_price', 'effective_price', 'is_available', 'created_at']
    can_delete = False
    show_change_link = True
    verbose_name = 'Doctor offering this service'
    verbose_name_plural = 'Doctors offering this service'


# ---------------------------------------------------------------------------
# Service (global catalog)
# ---------------------------------------------------------------------------

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'service_type_badge', 'price_display', 'currency',
        'duration_minutes', 'specialty',
        'flag_home', 'flag_on_demand', 'flag_active',
        'nurse_count', 'doctor_count',
    ]
    list_filter = [
        'service_type', 'is_active', 'is_home_service', 'is_on_demand',
        'currency', 'specialty',
    ]
    search_fields = ['title', 'title_en', 'title_ar', 'title_fr', 'description', 'slug']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at', 'slug']
    list_per_page = 30
    date_hierarchy = 'created_at'
    actions = ['activate_services', 'deactivate_services', 'enable_on_demand', 'disable_on_demand']

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'service_type', 'specialty'),
        }),
        ('Translations', {
            'classes': ('collapse',),
            'description': (
                'Fill in all three languages. If a language field is empty, '
                'the primary title/description above is used as fallback.'
            ),
            'fields': (
                ('title_en', 'title_ar', 'title_fr'),
                'description',
                ('description_en', 'description_ar', 'description_fr'),
            ),
        }),
        ('Pricing', {
            'fields': (('price', 'currency'),),
        }),
        ('Service Details', {
            'fields': (('duration_minutes', 'icon'),),
        }),
        ('Visibility & Flags', {
            'description': (
                '<strong>is_active</strong>: hides the service everywhere when unchecked.<br>'
                '<strong>is_home_service</strong>: makes it filterable as a home-visit service.<br>'
                '<strong>is_on_demand</strong>: required for the Uber-like nurse request flow; '
                'service_type must also be NURSE.'
            ),
            'fields': ('is_active', 'is_home_service', 'is_on_demand'),
        }),
        ('Timestamps', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
    )

    inlines = [NurseServiceInline, DoctorServiceInline]

    # ------------------------------------------------------------------
    # Custom column renderers
    # ------------------------------------------------------------------

    @admin.display(description='Type', ordering='service_type')
    def service_type_badge(self, obj):
        colours = {
            'NURSE': '#0ea5e9',
            'DOCTOR': '#8b5cf6',
            'VTC': '#f59e0b',
            'GENERAL': '#6b7280',
        }
        colour = colours.get(obj.service_type, '#6b7280')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px">{}</span>',
            colour, obj.get_service_type_display()
        )

    @admin.display(description='Price', ordering='price')
    def price_display(self, obj):
        return f'{obj.price:,.2f} {obj.currency}'

    @admin.display(description='🏠', boolean=True, ordering='is_home_service')
    def flag_home(self, obj):
        return obj.is_home_service

    @admin.display(description='⚡ On-Demand', boolean=True, ordering='is_on_demand')
    def flag_on_demand(self, obj):
        return obj.is_on_demand

    @admin.display(description='Active', boolean=True, ordering='is_active')
    def flag_active(self, obj):
        return obj.is_active

    @admin.display(description='Nurses')
    def nurse_count(self, obj):
        count = obj.nurses.count()
        return format_html('<strong>{}</strong>', count) if count else '—'

    @admin.display(description='Doctors')
    def doctor_count(self, obj):
        count = obj.doctors.count()
        return format_html('<strong>{}</strong>', count) if count else '—'

    # ------------------------------------------------------------------
    # Bulk actions
    # ------------------------------------------------------------------

    @admin.action(description='✅ Activate selected services')
    def activate_services(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} service(s) activated.')

    @admin.action(description='🚫 Deactivate selected services')
    def deactivate_services(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} service(s) deactivated.')

    @admin.action(description='⚡ Enable on-demand for selected services')
    def enable_on_demand(self, request, queryset):
        updated = queryset.update(is_on_demand=True)
        self.message_user(request, f'{updated} service(s) marked as on-demand.')

    @admin.action(description='⏹ Disable on-demand for selected services')
    def disable_on_demand(self, request, queryset):
        updated = queryset.update(is_on_demand=False)
        self.message_user(request, f'{updated} service(s) removed from on-demand.')


# ---------------------------------------------------------------------------
# DoctorService
# ---------------------------------------------------------------------------

@admin.register(DoctorService)
class DoctorServiceAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'service', 'effective_price_display', 'custom_price', 'is_available', 'created_at']
    list_filter = ['is_available', 'service__service_type', 'service']
    search_fields = [
        'doctor__first_name', 'doctor__last_name',
        'service__title', 'service__title_en', 'service__title_ar',
    ]
    readonly_fields = ['created_at']
    autocomplete_fields = ['service']
    list_select_related = ['doctor', 'service']
    actions = ['mark_available', 'mark_unavailable']

    @admin.display(description='Effective Price', ordering='custom_price')
    def effective_price_display(self, obj):
        price = obj.effective_price
        label = 'custom' if obj.custom_price is not None else 'default'
        return format_html('{} <small style="color:#6b7280">({})</small>', f'{price:,.2f}', label)

    @admin.action(description='Mark selected as available')
    def mark_available(self, request, queryset):
        queryset.update(is_available=True)

    @admin.action(description='Mark selected as unavailable')
    def mark_unavailable(self, request, queryset):
        queryset.update(is_available=False)


# ---------------------------------------------------------------------------
# NurseService
# ---------------------------------------------------------------------------

@admin.register(NurseService)
class NurseServiceAdmin(admin.ModelAdmin):
    list_display = ['nurse', 'service', 'effective_price_display', 'custom_price', 'is_available', 'created_at']
    list_filter = ['is_available', 'service__service_type', 'service']
    search_fields = [
        'nurse__first_name', 'nurse__last_name',
        'service__title', 'service__title_en', 'service__title_ar',
    ]
    readonly_fields = ['created_at']
    autocomplete_fields = ['service']
    list_select_related = ['nurse', 'service']
    actions = ['mark_available', 'mark_unavailable']

    @admin.display(description='Effective Price', ordering='custom_price')
    def effective_price_display(self, obj):
        price = obj.effective_price
        label = 'custom' if obj.custom_price is not None else 'default'
        return format_html('{} <small style="color:#6b7280">({})</small>', f'{price:,.2f}', label)

    @admin.action(description='Mark selected as available')
    def mark_available(self, request, queryset):
        queryset.update(is_available=True)

    @admin.action(description='Mark selected as unavailable')
    def mark_unavailable(self, request, queryset):
        queryset.update(is_available=False)


# ---------------------------------------------------------------------------
# ProviderCustomService
# ---------------------------------------------------------------------------

@admin.register(ProviderCustomService)
class ProviderCustomServiceAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'provider', 'price', 'currency', 'duration_minutes',
        'specialty', 'flag_active', 'flag_home', 'flag_online', 'created_at',
    ]
    list_filter = ['is_active', 'is_home_service', 'is_online_available', 'currency', 'specialty']
    search_fields = [
        'title', 'title_en', 'title_ar', 'title_fr',
        'provider__user__email',
    ]
    readonly_fields = ['created_at', 'updated_at']
    list_select_related = ['provider', 'specialty']
    actions = ['activate_services', 'deactivate_services']

    fieldsets = (
        ('Basic Information', {
            'fields': ('provider', 'specialty'),
        }),
        ('Content', {
            'fields': ('title', ('title_en', 'title_ar', 'title_fr')),
        }),
        ('Description', {
            'classes': ('collapse',),
            'fields': ('description', ('description_en', 'description_ar', 'description_fr')),
        }),
        ('Pricing & Duration', {
            'fields': (('price', 'currency'), 'duration_minutes'),
        }),
        ('Availability', {
            'fields': ('is_active', 'is_home_service', 'is_online_available', 'image'),
        }),
        ('Timestamps', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
    )

    @admin.display(description='Active', boolean=True)
    def flag_active(self, obj):
        return obj.is_active

    @admin.display(description='🏠 Home', boolean=True)
    def flag_home(self, obj):
        return obj.is_home_service

    @admin.display(description='💻 Online', boolean=True)
    def flag_online(self, obj):
        return obj.is_online_available

    @admin.action(description='✅ Activate selected')
    def activate_services(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} custom service(s) activated.')

    @admin.action(description='🚫 Deactivate selected')
    def deactivate_services(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} custom service(s) deactivated.')
