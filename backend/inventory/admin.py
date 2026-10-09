from django.contrib import admin

from .models import Branch, Copy


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ["name", "city"]


@admin.register(Copy)
class CopyAdmin(admin.ModelAdmin):
    list_display = ["barcode", "book", "branch", "shelf", "status"]
    list_filter = ["status", "branch"]
    search_fields = ["barcode", "book__title"]
    raw_id_fields = ["book"]
    show_full_result_count = False
