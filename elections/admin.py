from django.contrib import admin, messages
from django import forms
from django.utils.html import format_html
from django.utils.timezone import now
from django.conf import settings

from elections.models.elections import Election
from elections.models.positions import Position
from elections.models.candidates import Candidate
from blockchain.helpers import add_position, add_candidate


# ---- Validation Form ----
class CandidateAdminForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get("student")
        position = cleaned_data.get("position")

        if student and student.current_level == 4:
            raise forms.ValidationError("Students in Level 400 are not eligible to contest.")
        if position and not position.is_user_eligible(student):
            raise forms.ValidationError(
                "This student does not belong to an eligible department for this position."
            )
        return cleaned_data


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = (
        'code', 'title', 'election',
        'get_eligible_levels', 'get_eligible_departments',
        'sync_status', 'last_synced_at'
    )
    search_fields = ('title', 'election__title', 'code')
    list_filter = ('election', 'eligible_departments', 'is_synced')
    actions = ['sync_to_blockchain']
    readonly_fields = ['code']

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        exclude = {'is_synced', 'last_synced_at'}
        return [f for f in fields if f not in exclude]

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_synced:
            return [f.name for f in self.model._meta.fields]
        return super().get_readonly_fields(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_synced:
            return False
        return super().has_delete_permission(request, obj)

    def get_eligible_levels(self, obj):
        return ", ".join(f"Level {lvl * 100}" for lvl in obj.eligible_levels)
    get_eligible_levels.short_description = 'Eligible Levels'

    def get_eligible_departments(self, obj):
        return ", ".join([d.name for d in obj.eligible_departments.all()])
    get_eligible_departments.short_description = 'Eligible Departments'

    def sync_status(self, obj):
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if obj.is_synced else 'red',
            '✔ Synced' if obj.is_synced else '✖ Not Synced'
        )
    sync_status.short_description = 'Blockchain Status'

    def sync_to_blockchain(self, request, queryset):
        success, failed = 0, 0
        for position in queryset:
            try:
                add_position(position.code, position.title, position.election.code)
                position.is_synced = True
                position.last_synced_at = now()
                position.save()
                messages.success(request, f"✅ Synced Position '{position.title}'")
                success += 1
            except Exception as e:
                messages.error(request, f"❌ Failed syncing '{position.title}': {e}")
                failed += 1
        messages.info(request, f"Sync complete: {success} success, {failed} failed")
    sync_to_blockchain.short_description = "🔁 Sync selected Positions to Blockchain"


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    form = CandidateAdminForm
    list_display = ('code', 'student', 'position', 'get_election', 'sync_status', 'last_synced', 'image_preview')
    search_fields = ('student__full_name', 'position__title', 'code')
    list_filter = ('position__election', 'student__department', 'is_synced')
    actions = ['sync_to_blockchain']
    readonly_fields = ['code', 'image_preview']

    fieldsets = (
        (None, {
            'fields': ('student', 'position', 'manifesto', 'campaign_keywords', 'promise', 'image', 'image_preview')
        }),
    )

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        exclude = {'is_synced', 'last_synced'}
        return [f for f in fields if f not in exclude]

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_synced:
            return [f.name for f in self.model._meta.fields]
        return list(super().get_readonly_fields(request, obj)) + ['code', 'image_preview']

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_synced:
            return False
        return super().has_delete_permission(request, obj)

    def get_election(self, obj):
        return obj.position.election
    get_election.short_description = 'Election'

    def sync_status(self, obj):
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if obj.is_synced else 'red',
            '✔ Synced' if obj.is_synced else '✖ Not Synced'
        )
    sync_status.short_description = 'Blockchain Status'

    def sync_to_blockchain(self, request, queryset):
        success, failed = 0, 0
        for candidate in queryset:
            try:
                add_candidate(candidate.position.code, candidate.code, candidate.student.full_name)
                candidate.is_synced = True
                candidate.last_synced_at = now()
                candidate.save()
                messages.success(request, f"✅ Synced Candidate '{candidate.student.full_name}'")
                success += 1
            except Exception as e:
                messages.error(request, f"❌ Failed syncing '{candidate.student.full_name}': {e}")
                failed += 1
        messages.info(request, f"Sync complete: {success} success, {failed} failed")
    sync_to_blockchain.short_description = "🔁 Sync selected Candidates to Blockchain"

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height:100px;"/>', obj.image.url)
        return "-"
    image_preview.short_description = "Image Preview"

    # --- Auto-refresh code display after save ---
    def response_add(self, request, obj, post_url_continue=None):
        return self._refresh_with_code(request, obj, super().response_add)

    def response_change(self, request, obj):
        return self._refresh_with_code(request, obj, super().response_change)

    def _refresh_with_code(self, request, obj, super_method):
        response = super_method(request, obj)
        if "_continue" in request.POST:
            messages.info(request, f"Candidate Code: {obj.code}")
        return response


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = (
        'code', 'title', 'department', 'start_date', 'end_date',
        'status', 'is_active', 'created_at'
    )
    search_fields = ('title', 'department__name', 'code')
    ordering = ('-start_date',)
    list_filter = ('department', 'start_date', 'status')
    readonly_fields = ('code', 'created_at')

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        return [f for f in fields if f != 'code']
