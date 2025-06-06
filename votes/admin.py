from django.contrib import admin
from votes.models import Vote

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('receipt', 'get_election_code', 'get_position_code', 'get_candidate_code', 'timestamp')
    search_fields = ('receipt', 'position__code', 'candidate__code', 'election__code')
    list_filter = ('position__election__title', 'position__title', 'timestamp')
    readonly_fields = ('voter_did_hash', 'receipt', 'timestamp')

    def has_add_permission(self, request):
        return False  # Prevent manual vote addition

    def get_election_code(self, obj):
        return obj.election.code
    get_election_code.short_description = 'Election Code'

    def get_position_code(self, obj):
        return obj.position.code
    get_position_code.short_description = 'Position Code'

    def get_candidate_code(self, obj):
        return obj.candidate.code
    get_candidate_code.short_description = 'Candidate Code'
