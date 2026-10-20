# =============================================================================
# views.py - EventNow
#
# Contains all view functions for the EventNow platform.
# A view receives an HTTP request, processes business logic, queries the
# database, and returns either a rendered HTML page or a redirect.
#
# User types:
#   - Organiser: registered user who creates and manages events (login required)
#   - Attendee:  public user who registers for events (no login needed)
# =============================================================================
import os
import json               # Parses JSON data sent from the browser 
import urllib.request     # Sends HTTP requests to the OpenAI API
import requests as req_lib  # More reliable HTTP client

from django.shortcuts import render, redirect, get_object_or_404
# render()            - loads an HTML template, fills it with data, and returns it to the browser
# redirect()          - sends the browser to a different URL
# get_object_or_404() - fetches a database record, or returns a 404 page if not found

from django.contrib.auth import login, logout, authenticate
# login()        - saves the user's identity to the session (keeps them logged in)
# logout()       - clears the session (logs the user out)
# authenticate() - checks if a username/password is correct; returns User or None

from django.contrib.auth.decorators import login_required
# @login_required - decorator that blocks unauthenticated users and redirects them to login

from django.contrib.auth.models import User
# Django's built-in User model (stores username, hashed password, email, name)

from django.contrib import messages
# Stores one-time flash notifications (e.g. "Event deleted") that show on the next page load

from django.http import JsonResponse
# Returns JSON instead of HTML - used by AI endpoints called via JavaScript fetch()

from .models import Organizer, Event, Session, Room, Timeslot, Registration, RegistrationSession

# OpenAI API key provided by the course
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# =============================================================================
# HOMEPAGE
# URL: /
# Public - no login required
# =============================================================================
def homepage(request):
    # Fetch up to 6 published events to display on the landing page.
    # Draft events are excluded so only ready-to-go events are shown to the public.
    events = Event.objects.filter(status='published').order_by('start_date')
    return render(request, 'core/homepage.html', {'events': events})


# =============================================================================
# LOGIN
# URL: /login/
# Public - no login required
#
# EventNow uses email as the login identifier instead of Django's default username.
# On POST: looks up the user by email, verifies the password, and logs them in.
# On GET: renders the login form.
# =============================================================================
def login_view(request):
    if request.method == 'POST':
        email    = request.POST.get('email')
        password = request.POST.get('password')
        try:
            # Find the User record by email to retrieve the username,
            # since Django's authenticate() requires a username not an email.
            user = User.objects.get(email=email)
            # authenticate() checks the password against the stored hash.
            # Returns the User object if valid, or None if the password is wrong.
            user = authenticate(request, username=user.username, password=password)
            if user:
                login(request, user)       # Save login state to the session
                return redirect('dashboard')
            else:
                # Use the same error message for wrong email and wrong password
                # to avoid revealing which field was incorrect (security best practice)
                messages.error(request, 'Invalid email or password')
        except User.DoesNotExist:
            messages.error(request, 'Invalid email or password')
    return render(request, 'core/login.html')


# =============================================================================
# REGISTER
# URL: /register/
# Public - no login required
#
# Creates a new organiser account. Two records are created:
#   1. A Django User (handles authentication)
#   2. An Organizer profile (required to access event management features)
# The user is automatically logged in after registration.
# =============================================================================
def register_view(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name  = request.POST.get('last_name')
        email      = request.POST.get('email')
        password   = request.POST.get('password')

        # Prevent duplicate accounts with the same email address
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return render(request, 'core/login.html')

        # create_user() hashes the password automatically before saving to the database.
        # The email is used as the username to ensure uniqueness across accounts.
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Create the Organizer profile linked to this User.
        # Without this record, the user cannot access any organiser pages
        # because every organiser view calls get_object_or_404(Organizer, user=request.user).
        Organizer.objects.create(user=user)

        login(request, user)    # Log in automatically after registration
        return redirect('dashboard')

    return render(request, 'core/login.html')


# =============================================================================
# LOGOUT
# URL: /logout/
# =============================================================================
def logout_view(request):
    logout(request)             # Clears the session, ending the login state
    return redirect('homepage')


# =============================================================================
# ORGANISER DASHBOARD
# URL: /dashboard/
# Login required
#
# The main control panel for an organiser. Shows all their events and
# summary statistics: published count, draft count, and total registrations.
# =============================================================================
@login_required
def dashboard(request):
    # Retrieve the Organizer profile for the currently logged-in user.
    # Returns 404 if no Organizer record exists (e.g. a superuser account
    # that was created before the Organizer profile was set up).
    organizer = get_object_or_404(Organizer, user=request.user)
    events    = Event.objects.filter(organizer=organizer)

    # event__organizer uses Django's double-underscore syntax to follow the
    # foreign key: Registration -> Event -> Organizer in a single database query.
    total_registrations = Registration.objects.filter(event__organizer=organizer).count()

    return render(request, 'core/dashboard.html', {
        'events':              events,
        'organizer':           organizer,
        'published_count':     events.filter(status='published').count(),
        'draft_count':         events.filter(status='draft').count(),
        'total_registrations': total_registrations,
    })


# =============================================================================
# CREATE EVENT
# URL: /events/create/
# Login required
#
# On GET: renders an empty event creation form.
# On POST: saves the new event to the database and redirects to the dashboard.
# =============================================================================
@login_required
def create_event(request):
    organizer = get_object_or_404(Organizer, user=request.user)

    if request.method == 'POST':
        from django.utils.text import slugify
        title = request.POST.get('title')

        event = Event.objects.create(
            organizer=organizer,
            title=title,
            slug=slugify(title),
            description=request.POST.get('description'),
            location=request.POST.get('location'),
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date'),
            status='draft',
        )
        messages.success(request, 'Event created! Now add at least one session before publishing.')
        return redirect('sessions', event_id=event.id)

    return render(request, 'core/create_event.html')


# =============================================================================
# EDIT EVENT
# URL: /events/<event_id>/edit/
# Login required
#
# Ownership is verified before any changes are allowed - an organiser can only
# edit their own events, not events belonging to other organisers.
# =============================================================================
@login_required
def edit_event(request, event_id):
    organizer = get_object_or_404(Organizer, user=request.user)
    # Passing organizer=organizer ensures the event belongs to this organiser.
    # If someone tries to edit another organiser's event by changing the URL,
    # they will get a 404 instead of being able to make changes.
    event     = get_object_or_404(Event, id=event_id, organizer=organizer)

    if request.method == 'POST':
        from django.utils.text import slugify
        new_status = request.POST.get('status', 'draft')

        # Block publishing if the event has no sessions
        if new_status == 'published' and not Session.objects.filter(event=event).exists():
            messages.error(request, 'Please add at least one session before publishing.')
            return render(request, 'core/create_event.html', {'event': event})

        event.title       = request.POST.get('title')
        event.slug        = slugify(event.title)
        event.description = request.POST.get('description')
        event.location    = request.POST.get('location')
        event.start_date  = request.POST.get('start_date')
        event.end_date    = request.POST.get('end_date')
        event.status      = new_status
        event.save()
        return redirect('dashboard')

    # Pass the event to the template so the form fields can be pre-filled
    return render(request, 'core/create_event.html', {'event': event})


# =============================================================================
# DELETE EVENT
# URL: /events/<event_id>/delete/
# Login required
#
# Only processes DELETE on POST requests. This prevents accidental deletion
# if a browser pre-fetches a link or a user shares the URL.
# =============================================================================
@login_required
def delete_event(request, event_id):
    organizer = get_object_or_404(Organizer, user=request.user)
    event     = get_object_or_404(Event, id=event_id, organizer=organizer)

    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Event deleted successfully!')

    return redirect('dashboard')


# =============================================================================
# EVENT PUBLIC PAGE
# URL: /events/<slug>/
# Public - no login required
#
# Only published events are accessible - drafts return a 404 to keep
# unpublished content hidden from the public.
# =============================================================================
def event_public(request, slug):
    event    = get_object_or_404(Event, slug=slug, status='published')
    sessions = Session.objects.filter(event=event)
    return render(request, 'core/event_public.html', {'event': event, 'sessions': sessions})


# =============================================================================
# SESSION MANAGEMENT
# URL: /events/<event_id>/sessions/
# Login required
#
# Allows an organiser to view and add sessions (talks, workshops, panels)
# to one of their events. A room and timeslot must exist before a session
# can be created, as sessions must be assigned to both.
# =============================================================================
@login_required
def sessions_view(request, event_id):
    organizer = get_object_or_404(Organizer, user=request.user)
    event     = get_object_or_404(Event, id=event_id, organizer=organizer)
    sessions  = Session.objects.filter(event=event)
    rooms     = Room.objects.filter(event=event)
    timeslots = Timeslot.objects.filter(event=event)

    if request.method == 'POST':
        room_name     = request.POST.get('room_name', '')
        timeslot_name = request.POST.get('timeslot_name', '')

        Session.objects.create(
            event=event,
            title=request.POST.get('title'),
            speaker=request.POST.get('speaker', ''),
            track=request.POST.get('track', ''),
            capacity=request.POST.get('capacity'),
            room_name=room_name,
            time_display=timeslot_name,
            room=None,
            timeslot=None,
        )
        messages.success(request, 'Session added successfully!')
        # Auto-publish if requested
        if request.POST.get('publish_now') == '1':
            event.status = 'published'
            event.save()
            messages.success(request, 'Event published successfully!')
            return redirect('dashboard')
        return redirect('sessions', event_id=event_id)

    return render(request, 'core/sessions.html', {
        'event': event, 'sessions': sessions,
        'rooms': rooms, 'timeslots': timeslots
    })


# =============================================================================
# DELETE SESSION
# URL: /events/<event_id>/sessions/<session_id>/delete/
# Login required
# =============================================================================
@login_required
def delete_session(request, event_id, session_id):
    organizer = get_object_or_404(Organizer, user=request.user)
    event     = get_object_or_404(Event, id=event_id, organizer=organizer)
    # Verify the session belongs to this event, not just any event
    session   = get_object_or_404(Session, id=session_id, event=event)

    if request.method == 'POST':
        session.delete()
        messages.success(request, 'Session deleted successfully!')

    return redirect('sessions', event_id=event_id)


# =============================================================================
# REGISTRATION MANAGEMENT
# URL: /events/<event_id>/registrations/
# Login required
#
# Shows all attendee registrations for an event.
# Also calculates capacity stats per session (registered / remaining / percentage)
# so the organiser can see how full each session is.
# =============================================================================
@login_required
def registrations_view(request, event_id):
    organizer     = get_object_or_404(Organizer, user=request.user)
    event         = get_object_or_404(Event, id=event_id, organizer=organizer)
    registrations = Registration.objects.filter(event=event)
    sessions      = Session.objects.filter(event=event)

    # Build capacity data for each session to display as a progress bar in the template
    session_capacity = []
    for session in sessions:
        registered = RegistrationSession.objects.filter(session=session).count()
        remaining  = session.capacity - registered
        # Guard against division by zero if a session has no capacity set
        percentage = int((registered / session.capacity) * 100) if session.capacity > 0 else 0
        session_capacity.append({
            'session':    session,
            'registered': registered,
            'remaining':  remaining,
            'percentage': percentage,
        })

    return render(request, 'core/registrations.html', {
        'event':            event,
        'registrations':    registrations,
        'session_capacity': session_capacity,
    })


# =============================================================================
# ATTENDEE REGISTRATION
# URL: /events/<slug>/register/
# Public - no login required
#
# Allows anyone to register for a published event without creating an account.
# A Registration record is created, then linked to each chosen session via
# the RegistrationSession junction table (many-to-many relationship).
# =============================================================================
def register_attendee(request, slug):
    event    = get_object_or_404(Event, slug=slug, status='published')
    sessions = Session.objects.filter(event=event)

    # Build capacity info for each session to show remaining spots
    sessions_with_capacity = []
    for s in sessions:
        registered = RegistrationSession.objects.filter(session=s).count()
        remaining  = s.capacity - registered
        percentage = int((registered / s.capacity) * 100) if s.capacity > 0 else 0
        sessions_with_capacity.append({
            'session':    s,
            'registered': registered,
            'remaining':  remaining,
            'percentage': percentage,
            'is_full':    remaining <= 0,
        })

    if request.method == 'POST':
        session_ids = request.POST.getlist('sessions')

        # Validate: at least one session must be selected
        if not session_ids:
            messages.error(request, 'Please select at least one session to register.')
            return render(request, 'core/registration.html', {
                'event': event,
                'sessions': sessions,
                'sessions_with_capacity': sessions_with_capacity,
            })

        registration = Registration.objects.create(
            event=event,
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            email=request.POST.get('email'),
        )

        for session_id in session_ids:
            try:
                session = Session.objects.get(id=session_id)
                # Check capacity before registering
                registered = RegistrationSession.objects.filter(session=session).count()
                if registered < session.capacity:
                    RegistrationSession.objects.create(registration=registration, session=session)
            except Session.DoesNotExist:
                pass

        return render(request, 'core/registration_success.html', {
            'event': event,
            'registration': registration,
        })

    return render(request, 'core/registration.html', {
        'event': event,
        'sessions': sessions,
        'sessions_with_capacity': sessions_with_capacity,
    })


# =============================================================================
# AI: GENERATE EVENT DESCRIPTION
# URL: /ai/generate-description/
# Login required
# Returns JSON (AJAX endpoint - called via JavaScript fetch(), not a page load)
#
# Sends event details to the OpenAI API and returns a generated
# professional event description as a JSON response.
# =============================================================================
@login_required
def ai_generate_description(request):
    if request.method == 'POST':
        try:
            # AJAX requests send data as a raw JSON body, not as form fields
            data       = json.loads(request.body)
            title      = data.get('title', '')
            location   = data.get('location', '')
            event_type = data.get('event_type', 'conference')

            # Build the request payload for the OpenAI Chat Completions API
            api_data = json.dumps({
                "model": "gpt-5.4-mini",   # OpenAI model provided by the course
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a professional event copywriter. Write engaging and professional event descriptions."
                    },
                    {
                        "role": "user",
                        "content": f"""Write a professional and engaging event description for the following event:
Title: {title}
Location: {location}
Type: {event_type}

Write 2-3 paragraphs that would attract attendees. Be specific, enthusiastic and professional. Do not include any headers or bullet points, just flowing paragraphs."""
                    }
                ],
                "max_completion_tokens": 500
            }).encode('utf-8')

            response = req_lib.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {OPENAI_API_KEY}'
                },
                data=api_data,
                timeout=30
            )
            result = response.json()
            description = result['choices'][0]['message']['content']
            return JsonResponse({'success': True, 'description': description})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


# =============================================================================
# AI: RECOMMEND SESSIONS
# URL: /ai/recommend-sessions/
# Login required
# Returns JSON (AJAX endpoint - called via JavaScript fetch(), not a page load)
#
# Sends event details to the OpenAI API and returns 4 suggested sessions
# as a JSON array. The AI is told to respond in JSON format only so the
# response can be parsed directly without any text cleanup.
# =============================================================================
@login_required
def ai_recommend_sessions(request):
    if request.method == 'POST':
        try:
            data              = json.loads(request.body)
            event_title       = data.get('event_title', '')
            event_description = data.get('event_description', '')
            existing_sessions = data.get('existing_sessions', 0)

            # The prompt explicitly asks for JSON-only output so the response
            # can be parsed directly with json.loads()
            api_data = json.dumps({
                "model": "gpt-5.4-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an event planning assistant. Always respond with valid JSON only, no other text."
                    },
                    {
                        "role": "user",
                        "content": f"""Suggest 4 sessions for this event:

Event Title: {event_title}
Description: {event_description}
Existing sessions: {existing_sessions}

Respond ONLY with a JSON array. Example format:
[
  {{"title": "Keynote: The Future of AI", "speaker": "Industry Expert", "track": "AI", "timeslot": "9:00 AM - 10:00 AM", "room": "Main Hall"}},
  {{"title": "Workshop: Hands-on Python", "speaker": "Senior Developer", "track": "Workshop", "timeslot": "10:30 AM - 11:30 AM", "room": "Workshop Room A"}}
]"""
                    }
                ],
                "max_completion_tokens": 500
            }).encode('utf-8')

            response = req_lib.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {OPENAI_API_KEY}'
                },
                data=api_data,
                timeout=30
            )
            result = response.json()
            text = result['choices'][0]['message']['content']
            suggestions = json.loads(text)
            return JsonResponse({'success': True, 'suggestions': suggestions})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})
@login_required
def my_events(request):
    # Shows only the events belonging to the logged-in organiser
    organizer = get_object_or_404(Organizer, user=request.user)
    events = Event.objects.filter(organizer=organizer)
    return render(request, 'core/my_events.html', {
        'events': events,
        'organizer': organizer,
    })
