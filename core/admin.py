from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Organizer, Event, Session, Registration


# =============================================================================
# ORGANIZER ADMIN
# Customises how the Organizer list appears in the Django Admin panel.
# Superusers can view, search, filter, archive and restore organiser accounts.
# =============================================================================
class OrganizerAdmin(admin.ModelAdmin):
    # Columns shown in the organiser list
    list_display = ['get_name', 'get_email', 'get_is_active', 'get_date_joined']
    # Filter sidebar: filter by active/inactive status
    list_filter = ['user__is_active']
    # Search bar: search by email, first name, or last name
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    # Show 10 organisers per page
    list_per_page = 10
    # Custom bulk actions available in the Action dropdown
    actions = ['archive_organisers', 'restore_organisers']

    # Display the organiser's full name in the list
    def get_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_name.short_description = 'Name'

    # Display the organiser's email in the list
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'

    # Display a green/red dot showing whether the account is active
    def get_is_active(self, obj):
        return obj.user.is_active
    get_is_active.short_description = 'Active'
    get_is_active.boolean = True  # Renders as a tick/cross icon

    # Display the date the organiser registered
    def get_date_joined(self, obj):
        return obj.user.date_joined
    get_date_joined.short_description = 'Joined'

    # Archive action: sets is_active=False so the user cannot log in
    # Data is kept in the database (soft delete)
    def archive_organisers(self, request, queryset):
        for organizer in queryset:
            organizer.user.is_active = False
            organizer.user.save()
        self.message_user(request, f"{queryset.count()} organiser(s) archived.")
    archive_organisers.short_description = "Archive selected organisers"

    # Restore action: sets is_active=True so the user can log in again
    def restore_organisers(self, request, queryset):
        for organizer in queryset:
            organizer.user.is_active = True
            organizer.user.save()
        self.message_user(request, f"{queryset.count()} organiser(s) restored.")
    restore_organisers.short_description = "Restore selected organisers"


# Register models with the Admin panel
admin.site.register(Organizer, OrganizerAdmin)  # Uses custom OrganizerAdmin config above
admin.site.register(Event)       # Basic admin view for events
admin.site.register(Session)     # Basic admin view for sessions
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ['get_name', 'get_email', 'get_event', 'registered_at']
    list_per_page = 10

    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    get_name.short_description = 'Name'

    def get_email(self, obj):
        return obj.email
    get_email.short_description = 'Email'

    def get_event(self, obj):
        return obj.event.title
    get_event.short_description = 'Event'

admin.site.register(Registration, RegistrationAdmin)