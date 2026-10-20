from django.urls import path
from . import views

urlpatterns = [
    # ── Public pages ──────────────────────────────────────────────
    path('', views.homepage, name='homepage'),
    # Landing page showing all published events

    path('login/', views.login_view, name='login'),
    # Login page (uses email instead of username)

    path('register/', views.register_view, name='register'),
    # Organiser registration page

    path('logout/', views.logout_view, name='logout'),
    # Logs out the current user and redirects to homepage

    # ── Organiser dashboard ───────────────────────────────────────
    path('dashboard/', views.dashboard, name='dashboard'),
    # Main control panel showing all events and stats

    path('my-events/', views.my_events, name='my_events'),
    # Lists all events belonging to the logged-in organiser

    # ── Event management ──────────────────────────────────────────
    path('events/create/', views.create_event, name='create_event'),
    # Create a new event (redirects to sessions page after saving)

    path('events/<int:event_id>/edit/', views.edit_event, name='edit_event'),
    # Edit an existing event (ownership verified)

    path('events/<int:event_id>/delete/', views.delete_event, name='delete_event'),
    # Delete an event (POST only, ownership verified)

    # ── Session management ────────────────────────────────────────
    path('events/<int:event_id>/sessions/', views.sessions_view, name='sessions'),
    # View, add, and manage sessions for an event

    path('events/<int:event_id>/sessions/<int:session_id>/delete/', views.delete_session, name='delete_session'),
    # Delete a specific session from an event

    # ── Registration management ───────────────────────────────────
    path('events/<int:event_id>/registrations/', views.registrations_view, name='registrations'),
    # View all registrations and session capacity for an event

    # ── Public event pages ────────────────────────────────────────
    path('events/<slug:slug>/', views.event_public, name='event_public'),
    # Public event page visible to all visitors (published events only)

    path('events/<slug:slug>/register/', views.register_attendee, name='register_attendee'),
    # Attendee registration form (no login required)

    # ── AI endpoints (AJAX) ───────────────────────────────────────
    path('ai/generate-description/', views.ai_generate_description, name='ai_generate_description'),
    # Returns AI-generated event description as JSON

    path('ai/recommend-sessions/', views.ai_recommend_sessions, name='ai_recommend_sessions'),
    # Returns 4 AI-suggested sessions as JSON
]