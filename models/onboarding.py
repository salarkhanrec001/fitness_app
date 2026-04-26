from datetime import datetime, timezone
from extensions import db


class OnboardingProfile(db.Model):
    __tablename__ = "onboarding_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    height_cm = db.Column(db.Float, nullable=True)
    weight_kg = db.Column(db.Float, nullable=True)
    fitness_goal = db.Column(db.String(100), nullable=True)  # lose_weight, build_muscle, stay_fit, etc.
    experience_level = db.Column(db.String(50), nullable=True)  # beginner, intermediate, advanced
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    @property
    def bmi(self):
        """Calculate BMI from height and weight."""
        if self.height_cm and self.weight_kg and self.height_cm > 0:
            height_m = self.height_cm / 100
            return round(self.weight_kg / (height_m ** 2), 1)
        return None

    @property
    def bmi_category(self):
        """Return BMI category string."""
        bmi = self.bmi
        if bmi is None:
            return "Unknown"
        if bmi < 18.5:
            return "Underweight"
        elif bmi < 25:
            return "Normal weight"
        elif bmi < 30:
            return "Overweight"
        else:
            return "Obese"

    @property
    def bmi_color(self):
        """Return a color class for the BMI category."""
        bmi = self.bmi
        if bmi is None:
            return "gray"
        if bmi < 18.5:
            return "blue"
        elif bmi < 25:
            return "green"
        elif bmi < 30:
            return "orange"
        else:
            return "red"

    def goal_display(self):
        goals = {
            "lose_weight": "Lose Weight",
            "build_muscle": "Build Muscle",
            "stay_fit": "Stay Fit",
            "increase_endurance": "Increase Endurance",
            "improve_flexibility": "Improve Flexibility",
            "six_pack": "Get a Six Pack",
        }
        return goals.get(self.fitness_goal, self.fitness_goal or "Not set")

    def experience_display(self):
        levels = {
            "beginner": "Beginner",
            "intermediate": "Intermediate",
            "advanced": "Advanced",
        }
        return levels.get(self.experience_level, self.experience_level or "Not set")

    def __repr__(self):
        return f"<OnboardingProfile user_id={self.user_id}>"
