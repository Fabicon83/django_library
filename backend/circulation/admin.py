from django.contrib import admin

from .models import Loan, Member


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ["card_number", "user", "home_branch", "max_loans"]
    search_fields = ["card_number", "user__username", "user__last_name"]
    raw_id_fields = ["user"]
    list_select_related = ["user", "home_branch"]


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ["copy", "member", "loaned_at", "due_at", "returned_at"]
    list_filter = ["returned_at"]
    date_hierarchy = "loaned_at"
    raw_id_fields = ["copy", "member"]
    list_select_related = ["copy", "member__user"]
