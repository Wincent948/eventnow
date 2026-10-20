# EventNow

EventNow is a web-based event management platform where organisers can create events, schedule sessions,
and track attendee registrations. Attendees can browse events and register without needing an account.

---

## How to Run Locally

```bash
pip install django requests pillow
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000 in your browser.

---

## Pages

| Page | URL | Access |
|------|-----|--------|
| Homepage | / | Public |
| Login / Register | /login/ | Public |
| Organiser Dashboard | /dashboard/ | Login required |
| Create Event | /events/create/ | Login required |
| Session Management | /events/<id>/sessions/ | Login required |
| Registration Management | /events/<id>/registrations/ | Login required |
| Public Event Page | /events/<slug>/ | Public |
| Attendee Registration | /events/<slug>/register/ | Public |
| Admin Panel | /admin/ | Superuser only |

---

## Deployment

**Live URL:** https://infs3202-96e162bb.uqcloud.net

**Test Organiser Account:**
- Email: lisa@eventnow.com
- Password: test1234

---

## Admin Panel

The Django Admin panel allows a superuser to manage organiser accounts, including archiving accounts 
(soft delete — the account is disabled but data is kept).

**Admin login:**
- URL: https://infs3202-96e162bb.uqcloud.net/admin/
- Username: s4847848
- Password: Admin12345

**How to archive an organiser:**
1. Go to Organizers in the Admin panel
2. Select the account you want to archive
3. Choose "Archive selected organisers" from the Action dropdown
4. Click Run — the account will be disabled but data is kept

**How to restore an organiser:**
1. Select the archived account
2. Choose "Restore selected organisers" from the Action dropdown
3. Click Run — the account will be re-enabled

---

## AI Features

### 1. AI Event Description Generator
- Go to the Create Event page
- Enter the event title and location
- Click "Generate with AI"
- A professional event description will be generated and filled in automatically
- You can edit the description before saving

### 2. AI Session Recommender
- Go to the Session Management page for any event
- Click "Recommend Sessions"
- The AI will suggest 4 sessions based on your event title and description
- Click any suggestion card to auto-fill the session form
- You can edit the details before saving

---

## AI Tool Usage Declaration

Claude (claude.ai) was used during the development of this project to assist with debugging Django views, 
resolving Python errors, and improving HTML and CSS structure. All code was reviewed 
and tested by the author before being included in the project.