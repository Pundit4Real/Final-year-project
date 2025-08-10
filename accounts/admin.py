from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django import forms
from accounts.models import User, Department

class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('index_number', 'full_name', 'email', 'year_enrolled', 'level', 'department')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don’t match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class UserAdmin(BaseUserAdmin):
    add_form = UserCreationForm
    model = User
    list_display = ('index_number', 'full_name', 'email', 'department', 'current_level', 'did', 'status','is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'department')
    search_fields = ('index_number', 'full_name', 'email', 'did')
    ordering = ('index_number',)

    readonly_fields = ('did', 'wallet_address', 'private_key')

    fieldsets = (
        (None, {'fields': ('index_number', 'email', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'year_enrolled', 'level', 'department')}),
        ('Blockchain Info', {'fields': ('did', 'wallet_address', 'private_key')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('index_number', 'full_name', 'email', 'year_enrolled', 'level', 'department', 'password1', 'password2')}
        ),
    )

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name','id')

admin.site.register(User, UserAdmin)
admin.site.register(Department, DepartmentAdmin)
