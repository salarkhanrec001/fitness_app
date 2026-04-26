# FitAI — AI-Powered Fitness App

A complete Flask web application with:
- JWT-free session auth (signup/login/logout)
- 6-step onboarding with BMI calculation
- AI-generated workout plans (built-in fallback library)
- Goals & streak tracking
- Social friend system + real-time polling chat
- Profile management with avatar upload
- Password reset via simulated OTP

## Quick Start

```bash
# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python app.py
```

Open http://127.0.0.1:5000 in your browser.

## Folder Structure

```
fitness_app/
├── app.py               # App factory + blueprint registration
├── config.py            # Dev / production config
├── extensions.py        # Shared Flask extensions (db, bcrypt, login_manager)
├── requirements.txt
├── .env                 # Environment variables
├── passenger_wsgi.py    # cPanel deployment entry point
├── models/              # SQLAlchemy ORM models
├── routes/              # Flask blueprints
├── templates/           # Jinja2 HTML templates
├── static/              # CSS, JS, images, uploads
└── instance/            # SQLite database (auto-created)
```

## Environment Variables (.env)

| Variable | Description |
|---|---|
| `SECRET_KEY` | Flask session secret (change in production!) |
| `DATABASE_URL` | SQLAlchemy URI (default: SQLite) |
| `FLASK_ENV` | `development` or `production` |
| `AI_API_KEY` | Optional: AI API key for real plan generation |

## URL Map

| URL | Description |
|---|---|
| `/auth/signup` | Create account |
| `/auth/login` | Login |
| `/auth/logout` | Logout |
| `/onboard/step1` – `/step6` | Onboarding flow |
| `/` | Dashboard |
| `/exercise/workout` | Workout hub |
| `/goals/` | Goals manager |
| `/social/friends` | Friends list |
| `/social/chat/<id>` | Chat with friend |
| `/profile/` | User profile |
| `/account/forgot-password` | Password reset |
| `/ai/regenerate` | Regenerate AI plan |
