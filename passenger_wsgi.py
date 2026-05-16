"""
passenger_wsgi.py — cPanel/Passenger deployment entry point.

Upload this to your cPanel public_html or the application root.
Set the "Application startup file" to passenger_wsgi.py in cPanel's
Python App manager.
"""
import sys
import os

# Add the project directory to sys.path
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Load environment variables from .env file
from dotenv import load_dotenv

env_path = os.path.join(project_dir, ".env")
loaded = load_dotenv(env_path, override=False)

openai_set = bool(os.environ.get("OPENAI_API_KEY"))
gemini_set = bool(os.environ.get("GEMINI_API_KEY"))
ai_set = bool(os.environ.get("AI_API_KEY"))

print(
    f"[FitAI] .env_loaded={loaded} OPENAI_API_KEY_set={openai_set} GEMINI_API_KEY_set={gemini_set} AI_API_KEY_set={ai_set}",
    file=sys.stderr,
)

# Import the Flask application
from app import app as application  # noqa: F401
# Passenger expects the WSGI callable to be named 'application'
