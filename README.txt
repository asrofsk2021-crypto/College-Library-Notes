POLYTECHNIC COLLEGE LIBRARY — BACKEND-READY EDITION
==================================================

WHAT IS INCLUDED
- Existing Bootstrap-based Polytechnic College Library interface retained.
- Flask backend with student registration and login.
- PDF-only upload (maximum 25 MB).
- Student uploads are private/pending until admin approval.
- Admin dashboard to approve, reject, and delete submissions.
- SQL database for users and material records.
- Supabase Storage integration for durable cloud file storage.
- Local SQLite/local-file mode for development only.

IMPORTANT BEFORE PUBLIC DEPLOYMENT
1. Configure a strong SECRET_KEY.
2. Configure a strong ADMIN_PASSWORD.
3. Configure DATABASE_URL with a PostgreSQL connection string.
4. Create a PRIVATE Supabase Storage bucket named college-notes (or set SUPABASE_BUCKET).
5. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY as server-side environment variables.
6. NEVER put the Supabase service-role key in HTML, JavaScript, a public repository, or send it in chat.
7. Use HTTPS in production.
8. Back up the database and storage files periodically.

LOCAL TESTING (Windows 11)
1. Install Python 3.11 or newer.
2. Open this project folder in VS Code.
3. Open Terminal > New Terminal.
4. Run:
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
5. Copy .env.example to .env and set SECRET_KEY and ADMIN_PASSWORD.
6. Run:
   py app.py
7. Open http://127.0.0.1:5000

SUPABASE SETUP
- Create a Supabase project.
- In Storage, create a PRIVATE bucket named college-notes.
- Copy the Project URL and service_role key from Project Settings > API.
- Add them as environment variables on the hosting provider. The service-role key must stay server-side.
- Copy the PostgreSQL connection string from Project Settings > Database and set DATABASE_URL.
- The app creates its SQL tables on first start. For an existing production database, back it up and plan a migration before replacing the old app.

ADMIN
- Visit /admin/login
- Use the ADMIN_PASSWORD configured in hosting environment variables.
- Do not use a weak or shared password.

LIMITATIONS / NOTES
- This version uses app-managed student accounts (email + password hash), not email verification or password reset yet.
- For a real public launch, add email verification, password reset, rate limiting, CSRF protection, moderation/reporting, and regular backups.
- Local SQLite and local uploads are only for testing. Local files may be lost on many free cloud hosts after redeploy/restart.
- The original sample/demo material records were removed; real PDFs should be uploaded.
- Only upload materials you have permission to share. Do not distribute copyrighted books or paid course material without permission.
