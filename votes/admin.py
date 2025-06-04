from django.contrib import admin
from votes.models import Vote

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('position', 'election', 'candidate', 'timestamp', 'receipt')
    search_fields = ('receipt', 'candidate__student__full_name', 'position__title', 'election__title')
    list_filter = ('election', 'position', 'timestamp')
    readonly_fields = ('voter_did_hash', 'receipt', 'timestamp')

    def has_add_permission(self, request):
        return False  # Prevent adding votes manually

    def has_change_permission(self, request, obj=None):
        return False  # Prevent editing existing votes

    def has_delete_permission(self, request, obj=None):
        return False  # Prevent deleting votes
