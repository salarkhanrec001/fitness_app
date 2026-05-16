"""Habit Forms"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class HabitForm(FlaskForm):
    name = StringField('Habit Name', validators=[DataRequired(), Length(max=150)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    is_bad_habit = BooleanField('This is a bad habit I want to break')
    frequency = SelectField('Frequency', choices=[
        ('daily', 'Daily'), ('weekly', 'Weekly'),
    ], default='daily')
    color = StringField('Color', default='#6366f1')
    icon = SelectField('Icon', choices=[
        ('⭐', '⭐ Star'), ('💪', '💪 Strength'), ('📚', '📚 Study'),
        ('🏃', '🏃 Exercise'), ('💧', '💧 Water'), ('🧘', '🧘 Meditate'),
        ('✍️', '✍️ Write'), ('🎯', '🎯 Focus'), ('😴', '😴 Sleep'),
        ('🚫', '🚫 Quit'),
    ], default='⭐')
    submit = SubmitField('Save Habit')
