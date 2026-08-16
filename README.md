# SkillBridge — Student Skills Freelancing Platform

SkillBridge is a full-stack freelancing marketplace that connects **students/freelancers**, **clients**, and an **admin**. It is built with Flask, Flask-SQLAlchemy and PostgreSQL (Neon), and uses a premium **Royal Blue (#1E3A8A) + Gold (#F59E0B)** design system.

The platform is a complete, interconnected marketplace — not a simplified CRUD demo. Every major button performs a real action: posting projects, submitting proposals, hiring, milestone tracking, messaging, payments, two-way reviews, notifications, skill-based matching, and full admin management.

---

## Features

### Students / Freelancers
- Registration & login with role-based auth
- Profile with bio, university, experience, hourly rate, availability, languages
- Skills management (with skill level) and smart skill matching to projects
- Portfolio showcase (images, tech, links)
- Certificates (with verification workflow)
- Skill assessments (MCQ) with pass/fail results
- Resume builder & printable resume
- Browse projects marketplace with search & filters
- Browse student marketplace (public profiles)
- Apply to projects with cover letter, price, delivery time
- Track applications, hired projects and earnings
- Project workspace: milestones, deliverables, chat, reviews
- Wishlist of students/projects
- Withdraw earnings

### Clients
- Registration & login
- Post projects (budget, deadline, category, type, location, required skills)
- Review proposals and accept/reject
- Hire students → creates a Hire + pending Payment (10% platform fee)
- Project workspace with milestone management
- Mark project complete and release payment
- Two-way reviews
- Payments overview

### Messaging
- One-to-one chat threads per project
- Unread message indicators

### Notifications
- Real-time style notifications (proposals, hires, payments, messages)
- Mark read / mark all read / delete

### Admin Panel
- Dashboard with platform KPIs
- Manage users (role change, suspend, delete)
- Verify students & certificates
- Manage categories, skills, projects, proposals, hires
- Payments & withdrawal approvals
- Broadcast notifications
- Banner management
- Reports & assessments

### Smart Skill Matching
Transparent, rule-based scoring (not fake AI). A student's match % for a project is computed from the overlap between the student's skills and the project's required skills, weighted by skill level. See `utils.skill_match_percentage()` and `utils.project_match_for_student()`.

---

## Tech Stack
- **Backend:** Flask 3, Flask-SQLAlchemy, Flask-Migrate, Flask-Login, Flask-WTF
- **Database:** PostgreSQL (Neon) with SQLite fallback for quick local testing
- **Frontend:** Jinja2 templates, vanilla CSS (design system), vanilla JS
- **Auth:** Werkzeug password hashing, Flask-Login sessions, CSRF tokens via session

---

## Project Structure
```
.
├── app.py                 # Application factory + CLI seed command
├── config.py              # Configuration (reads .env)
├── extensions.py          # SQLAlchemy, Migrate, LoginManager
├── utils.py               # Uploads, notifications, matching, filters
├── seed.py                # Demo data (seed_all)
├── models/                # SQLAlchemy models
├── routes/                # Blueprints (auth, home, student, client, project, ...)
├── templates/             # Jinja2 templates
├── static/
│   ├── css/               # style, auth, dashboard, student, client, admin, responsive
│   └── js/                # main, dashboard, auth, search, chat, notifications, project, admin
└── requirements.txt
```

---

## Setup

### 1. Clone & create a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables
Copy `.env.example` to `.env` and fill in your values:
```bash
cp .env.example .env
```
Key variables:
- `DATABASE_URL` — PostgreSQL connection string (Neon). If omitted, the app falls back to a local `app.db` SQLite file.
- `SECRET_KEY` — long random string for session signing
- `FLASK_DEBUG` — `0` or `1`
- `PLATFORM_NAME`, `PLATFORM_FEE_PERCENT`, `UPLOAD_FOLDER`, `MAX_CONTENT_LENGTH`

> **Never commit your real `.env` file.** It is already listed in `.gitignore`.

### 4. Run database migrations
```bash
flask db init        # only first time
flask db migrate -m "initial"
flask db upgrade
```

### 5. Seed demo data
```bash
flask seed
```
This populates the database with an admin, students, clients, categories, skills, projects, proposals, hires, payments, reviews, messages, notifications, banners and wishlist items.

### 6. Run the app
```bash
flask run
# or
python app.py
```
Open http://localhost:5000

---

## Demo Accounts (after seeding)
| Role    | Email                     | Password       |
|---------|---------------------------|----------------|
| Admin   | admin@skillbridge.com     | admin123       |
| Student | alex@student.com          | password123    |
| Client  | techcorp@client.com       | password123    |

---

## Notes
- **Payments** are simulated — no real card data is ever stored. Only a `transaction_reference` and `payment_method` label are kept.
- **CSRF protection** uses a per-session token (`session['_csrf_token']`) injected into forms.
- **File uploads** are validated by extension and stored under `static/uploads/` in subfolders (profiles, portfolio, certificates, banners, general, messages).
- The default avatar is `static/images/default-avatar.png`; templates fall back gracefully if a user has no profile picture.

---

## License
This project is provided as a demonstration of a full-stack freelancing marketplace.
"# student-skills-and-freelancing-platform"  
