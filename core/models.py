from django.db import models
from django.contrib.auth.models import User


# =============================================================================
# ORGANIZER
# Stores the organiser profile linked to a Django User account.
# Every registered organiser has one User and one Organizer record.
# =============================================================================
class Organizer(models.Model):
    # OneToOneField: each User can only have one Organizer profile
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # The following fields are optional and not currently used in the UI
    organization = models.CharField(max_length=200, blank=True)  # Optional company name
    phone = models.CharField(max_length=20, blank=True)          # Optional phone number
    bio = models.TextField(blank=True)                           # Optional profile bio

    def __str__(self):
        return self.user.get_full_name()


# =============================================================================
# EVENT
# Represents an event created by an organiser.
# Events can be in Draft, Published, or Archived state.
# Only Published events are visible to the public.
# =============================================================================
class Event(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),         # Not visible to public, still being set up
        ('published', 'Published'), # Visible to public, open for registration
        ('archived', 'Archived'),   # Hidden from public, data kept for records
    ]

    organizer = models.ForeignKey(Organizer, on_delete=models.CASCADE)  # Event owner
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)     # URL-friendly title e.g. "tech-summit-2026"
    description = models.TextField()
    location = models.CharField(max_length=300)
    start_date = models.DateField()
    end_date = models.DateField()
    cover_image = models.ImageField(upload_to='events/', blank=True, null=True)  # Optional banner
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically set on creation

    def __str__(self):
        return self.title


# =============================================================================
# ROOM
# NOTE: This model was part of the original design but is not actively used.
# Sessions use the free-text field 'room_name' instead of this foreign key.
# Kept to avoid migration issues.
# =============================================================================
class Room(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    capacity = models.IntegerField()

    def __str__(self):
        return self.name


# =============================================================================
# TIMESLOT
# NOTE: This model was part of the original design but is not actively used.
# Sessions use the free-text field 'time_display' instead of this foreign key.
# Kept to avoid migration issues.
# =============================================================================
class Timeslot(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def __str__(self):
        return f"{self.start_time} - {self.end_time}"


# =============================================================================
# SESSION
# Represents a single talk, workshop, or panel within an event.
# Each session has a title, speaker, track, capacity, room and time.
# room_name and time_display are free-text fields used instead of
# the Room and Timeslot foreign keys for simplicity.
# =============================================================================
class Session(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True)         # Not used
    timeslot = models.ForeignKey(Timeslot, on_delete=models.CASCADE, null=True, blank=True) # Not used
    title = models.CharField(max_length=200)
    speaker = models.CharField(max_length=100, blank=True)      # Optional speaker name
    track = models.CharField(max_length=100, blank=True)        # Optional category e.g. "AI", "Workshop"
    capacity = models.IntegerField()                            # Max attendees for this session
    room_name = models.CharField(max_length=100, blank=True)    # Free-text room name e.g. "Main Hall"
    time_display = models.CharField(max_length=100, blank=True) # Free-text time e.g. "May 26, 9:00 AM"

    def __str__(self):
        return self.title


# =============================================================================
# REGISTRATION
# Records an attendee signing up for an event.
# Attendees do not need a login account to register.
# One registration can include multiple sessions via RegistrationSession.
# =============================================================================
class Registration(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    registered_at = models.DateTimeField(auto_now_add=True)  # Automatically set on registration
    # Many-to-many relationship with Session through the junction table
    sessions = models.ManyToManyField(Session, through='RegistrationSession')

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# =============================================================================
# REGISTRATIONSESSION
# Junction table linking a Registration to a Session (many-to-many).
# One registration can be linked to multiple sessions.
# unique_together prevents an attendee from registering for the same session twice.
# =============================================================================
class RegistrationSession(models.Model):
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('registration', 'session')  # No duplicate session registrations