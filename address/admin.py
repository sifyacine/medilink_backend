from django.contrib import admin

from address.models import Address


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "content_type",
        "object_id",
        "street",
        "city",
        "country",
        "is_primary",
        "address_type",
        "created_at",
    )
    list_filter = ("address_type", "city", "country", "is_primary")
    search_fields = ("street", "city", "state", "zip_code", "notes")
