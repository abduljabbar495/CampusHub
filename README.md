# CampusHub – Secure Campus Management & Security Platform

SE331 · Lab 41_B1 · Group 9 · Fall 2026
Python · Django · Django ORM · MySQL · Bootstrap 5 · Render · Git/GitHub

A role-based web platform that digitises academic, administrative and campus-security work.

## Modules (mapped to the proposal)

| Module | Features | Where |
|---|---|---|
| **1. User & Academic Management** | Registration & RBAC, student profiles, course enrollment, class schedule, **QR-based attendance**, academic results | `accounts/`, `academics/` |
| **2. Learning & Campus Activity** | Learning materials, assignments (submit + grade), **online quizzes** (timed, auto-graded), notices, events + RSVP, complaints with resolution workflow | `campus/` |
| **3. Campus Security & Administration** | **Visitor registration & QR passes** (check-in/out, expiry, revoke), incident reporting & tracking, **audit log**, role dashboards, reports + CSV export | `security/`, `accounts/` |

Roles: Student · Teacher · Administrative Staff · Security Guard · System Administrator · University Management (read-only monitoring).

## Security features

- **RBAC** on every view (`accounts/permissions.py`), plus object-level scoping (teachers see only their courses, students only their data). Denied attempts are audited.
- **MFA** – TOTP (Google Authenticator / Authy). Secrets are **encrypted at rest** (Fernet).
- **Password hashing** – Argon2 (PBKDF2 fallback), 10-char minimum, common-password checks.
- **Brute-force protection** – account lockout after 5 failed logins / MFA attempts (15 min).
- **Audit logging** – logins, failures, MFA, CRUD, exports, access-denied, visitor scans (`/audit/`).
- **Secure file uploads** – extension whitelist, 10 MB limit, random UUID file names, served only to signed-in users.
- Input validation via Django forms; CSRF; secure/HttpOnly cookies; HSTS + HTTPS redirect in production; clickjacking protection; 1-hour idle session timeout; CSV-injection guard on exports; visitor ID numbers encrypted.
- Teacher self-registrations require administrator approval.

## Run locally

```bash
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # optional; with no DB_ENGINE it uses SQLite

python manage.py makemigrations accounts academics campus security   # first time only – commit the generated files
python manage.py migrate
python manage.py createsuperuser        # becomes a System Administrator
python manage.py seed_demo              # optional: one demo user per role (password: CampusHub@2026!)
python manage.py runserver
python manage.py test                   # run the test-suite
```

Open http://127.0.0.1:8000/ . Environment variables are read from the process (load `.env` with your shell, or use `export $(cat .env | xargs)`).

### Using MySQL

```sql
CREATE DATABASE campushub CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
then set `DB_ENGINE=mysql`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`. (PyMySQL is used, so no C compiler is needed.)

## Deploy on Render

1. Push this folder to GitHub (commit the generated `*/migrations/0001_initial.py` files).
2. In Render choose **New → Blueprint** (uses `render.yaml`) or create a Web Service with build command `./build.sh` and start command `gunicorn config.wsgi:application`.
3. Render does not host MySQL – use an external MySQL (Aiven, Railway, TiDB Cloud, a VPS…) and set `DB_*` variables.
4. Set `DJANGO_SUPERUSER_USERNAME / EMAIL / PASSWORD` to auto-create the first administrator.
5. **Uploads:** Render's disk is ephemeral. Attach a Render Disk mounted at `media/` (or move `MEDIA_ROOT` to S3/Cloudinary) so uploaded files survive redeploys. Back up the database regularly (`mysqldump`).

## Project layout

```
config/      settings, urls, wsgi
accounts/    users, RBAC, MFA, audit log, notifications, dashboards, reports
academics/   courses, enrollment, schedule, QR attendance, results
campus/      materials, assignments, quizzes, notices, events, complaints
security/    visitors & passes, incidents
templates/   Bootstrap 5 templates (generic list/form/delete templates are reused everywhere)
```

## Typical flows to demo

1. Admin creates a teacher/guard/staff user → teacher creates a course, a class session and opens attendance (QR appears).
2. Student registers, enrolls, scans the QR (or opens the link) → attendance recorded; submits an assignment; takes a quiz; files a complaint.
3. Staff posts a notice/event and resolves the complaint → student gets a notification.
4. Guard registers a visitor → prints the QR pass → checks them in/out; anyone reports an incident → guard triages it.
5. Admin / Management open **Dashboard → Reports / Audit log** and export CSV.

## One-click local setup

- **Windows:** double-click `run_windows.bat` (Python 3.11+ must be installed and available as `py`).
- **macOS/Linux:** run `chmod +x run_linux_mac.sh && ./run_linux_mac.sh`.

The first run installs dependencies, creates database migrations, migrates SQLite, asks you to create an administrator, and starts the development server at http://127.0.0.1:8000/.
