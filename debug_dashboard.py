
import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from app import create_app
from flask_login import login_user
from extensions import db
from models.user import User

app = create_app('development')
with app.app_context():
    user = User.query.first()
    if not user:
        print("No user found")
        sys.exit(1)
    
    print(f"Testing dashboard for user: {user.username}")
    
    from flask import Flask, request
    with app.test_request_context():
        from flask_login import login_user
        login_user(user)
        
        from routes.dashboard import index
        try:
            res = index()
            print("Dashboard index ran successfully")
        except Exception as e:
            import traceback
            traceback.print_exc()
