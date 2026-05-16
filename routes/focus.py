from flask import Blueprint, render_template
from flask_login import login_required

focus_bp = Blueprint("focus", __name__)

@focus_bp.route("/")
@login_required
def index():
    return render_template("focus/index.html")
