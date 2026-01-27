from django.contrib import admin

from specialties.models import Specialty, DoctorSpecialty


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "medical_domain",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "medical_domain")
    search_fields = (
        "title",
        "title_ar",
        "title_fr",
        "title_en",
        "description",
        "description_ar",
        "description_fr",
        "description_en",
    )
    prepopulated_fields = {"slug": ("title",)}


@admin.register(DoctorSpecialty)
class DoctorSpecialtyAdmin(admin.ModelAdmin):
    list_display = (
        "doctor",
        "specialty",
        "is_primary",
        "years_of_experience",
        "created_at",
    )
    list_filter = ("is_primary", "specialty")
    search_fields = ("doctor__first_name", "doctor__last_name", "specialty__title")
