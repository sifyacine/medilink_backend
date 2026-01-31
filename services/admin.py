from django.contrib import admin
from services.models import Service, DoctorService, NurseService, ServiceType


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'slug', 'service_type', 'price', 'currency', 
        'duration_minutes', 'is_home_service', 'is_on_demand', 'is_active'
    ]
    list_filter = ['service_type', 'is_active', 'is_home_service', 'is_on_demand', 'currency', 'specialty']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'service_type')
        }),
        ('Pricing', {
            'fields': ('price', 'currency')
        }),
        ('Service Details', {
            'fields': ('duration_minutes', 'icon', 'specialty')
        }),
        ('Availability Options', {
            'fields': ('is_active', 'is_home_service', 'is_on_demand'),
            'description': 'For on-demand nursing services, check both "Is home service" and "Is on demand"'
        }),
    )


@admin.register(DoctorService)
class DoctorServiceAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'service', 'custom_price', 'is_available']
    list_filter = ['is_available', 'service']
    search_fields = ['doctor__first_name', 'doctor__last_name', 'service__title']


@admin.register(NurseService)
class NurseServiceAdmin(admin.ModelAdmin):
    list_display = ['nurse', 'service', 'custom_price', 'is_available']
    list_filter = ['is_available', 'service']
    search_fields = ['nurse__first_name', 'nurse__last_name', 'service__title']
