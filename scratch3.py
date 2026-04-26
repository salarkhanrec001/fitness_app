from app import create_app
from flask import render_template
from flask_login import login_user
from models.user import User

app = create_app()
with app.app_context():
    app.config['SERVER_NAME'] = 'localhost:5000'
    with app.test_request_context('/exercise/history'):
        user = User.query.first()
        login_user(user)
        from routes.exercise import history
        html = history()
        if '<div class="heatmap-cell' in html:
            print('Heatmap cells found.')
            print('Cell count:', html.count('heatmap-cell'))
        else:
            print('No heatmap cells found in HTML output')
