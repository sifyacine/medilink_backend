from django.contrib import admin
from services.models import Service, DoctorService, NurseService


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'price', 'currency', 'duration_minutes', 'is_home_service', 'is_active']
    list_filter = ['is_active', 'is_home_service', 'currency', 'specialty']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}


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
