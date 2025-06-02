from django.contrib import admin
from .models import Election, Position, Candidate


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'created_at')
    search_fields = ('title',)
    ordering = ('-start_date',)


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('title', 'election', 'get_eligible_levels')
    search_fields = ('title', 'election__title')
    list_filter = ('election',)

    def get_eligible_levels(self, obj):
        return ", ".join(f"Level {lvl * 100}" for lvl in obj.eligible_levels)
    get_eligible_levels.short_description = 'Eligible Levels'


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('student', 'position', 'get_election')
    search_fields = ('student__full_name', 'position__title')
    list_filter = ('position__election',)

    def get_election(self, obj):
        return obj.position.election
    get_election.short_description = 'Election'
