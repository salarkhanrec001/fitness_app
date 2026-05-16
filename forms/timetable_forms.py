"""Timetable Forms"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class TimetableForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    color = StringField('Color', default='#6366f1')
    submit = SubmitField('Create Timetable')


class TimeSlotForm(FlaskForm):
    day_of_week = SelectField('Day', choices=[
        ('0', 'Monday'), ('1', 'Tuesday'), ('2', 'Wednesday'),
        ('3', 'Thursday'), ('4', 'Friday'), ('5', 'Saturday'), ('6', 'Sunday'),
    ], coerce=int)
    start_time = StringField('Start Time', validators=[DataRequired()])
    end_time = StringField('End Time', validators=[Optional()])
    duration = SelectField('Duration', choices=[
        ('60', '1 Hour'), ('30', '30 Minutes'), ('15', '15 Minutes'),
    ], default='60')
    task = StringField('Task', validators=[DataRequired(), Length(max=200)])
    category = SelectField('Category', choices=[
        ('general', '📋 General'), ('study', '📚 Study'), ('workout', '💪 Workout'),
        ('work', '💼 Work'), ('personal', '🏠 Personal'), ('creative', '🎨 Creative'),
        ('social', '👥 Social'), ('rest', '😴 Rest'),
    ])
    notes = TextAreaField('Notes', validators=[Length(max=500)])
    submit = SubmitField('Add Slot')
