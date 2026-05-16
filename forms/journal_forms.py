"""Journal Forms"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length


class JournalEntryForm(FlaskForm):
    title = StringField('Title', validators=[Length(max=200)])
    content = TextAreaField('What\'s on your mind?', validators=[DataRequired(), Length(min=1, max=5000)])
    mood = SelectField('Mood', choices=[
        ('great', '🤩 Great'), ('good', '😊 Good'), ('neutral', '😐 Neutral'),
        ('bad', '😔 Bad'), ('terrible', '😢 Terrible'),
    ], default='neutral')
    tags = StringField('Tags (comma-separated)', validators=[Length(max=500)])
    submit = SubmitField('Save Entry')
