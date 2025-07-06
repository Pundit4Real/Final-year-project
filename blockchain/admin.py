# blockchain/admin.py
from django.contrib import admin, messages
from elections.models import Election
from blockchain.helpers import sync_election  # you will create this next

@admin.action(description="⛓ Sync selected elections to blockchain")
def sync_selected_elections(modeladmin, request, queryset):
    for election in queryset:
        try:
            sync_election(election)
            messages.success(request, f"✅ Synced election: {election.code}")
        except Exception as e:
            messages.error(request, f"❌ Failed to sync {election.code}: {str(e)}")

class ElectionSyncAdmin(admin.ModelAdmin):
    actions = [sync_selected_elections]

# Register separately
admin.site.unregister(Election)
admin.site.register(Election, ElectionSyncAdmin)
