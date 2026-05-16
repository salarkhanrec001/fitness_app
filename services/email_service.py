"""
Email Service
Handles sending transactional emails (welcome, OTP, reminders).
Ported from Motivaura.
"""

from flask import current_app
from flask_mail import Message
from extensions import mail


class EmailService:
    """Handles all outbound email operations."""

    @staticmethod
    def _send(subject, recipients, html_body):
        """Internal helper to send an email."""
        try:
            msg = Message(
                subject=subject,
                recipients=recipients if isinstance(recipients, list) else [recipients],
                html=html_body,
                sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
            )
            mail.send(msg)
            return True
        except Exception as e:
            current_app.logger.error(f'Email send failed: {e}')
            return False

    @staticmethod
    def send_welcome_email(user, otp):
        """Send welcome email with verification OTP."""
        html = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto;
                    background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 100%); padding: 40px;
                    border-radius: 16px; color: #e2e8f0;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #818cf8; margin: 0; font-size: 28px;">⚡ FitAI</h1>
                <p style="color: #94a3b8; margin-top: 8px;">Your AI-powered fitness journey starts now.</p>
            </div>
            <div style="background: rgba(255,255,255,0.05); border-radius: 12px; padding: 30px;
                        border: 1px solid rgba(129,140,248,0.2);">
                <h2 style="color: #f1f5f9; margin-top: 0;">Welcome, {user.username}! 🚀</h2>
                <p style="color: #cbd5e1; line-height: 1.6;">
                    Thank you for joining FitAI. To get started, please verify your email
                    with the code below:
                </p>
                <div style="text-align: center; margin: 30px 0;">
                    <div style="display: inline-block; background: linear-gradient(135deg, #6366f1, #8b5cf6);
                                padding: 16px 40px; border-radius: 12px; font-size: 32px;
                                letter-spacing: 8px; font-weight: bold; color: #fff;">
                        {otp}
                    </div>
                </div>
                <p style="color: #94a3b8; font-size: 14px; text-align: center;">
                    This code expires in 10 minutes.
                </p>
            </div>
            <div style="text-align: center; margin-top: 30px; color: #64748b; font-size: 12px;">
                <p>FitAI — Train smarter. Track better. Stay disciplined.</p>
            </div>
        </div>
        """
        return EmailService._send(
            subject='Welcome to FitAI — Verify Your Email',
            recipients=user.email,
            html_body=html,
        )

    @staticmethod
    def send_verification_otp(user, otp):
        """Send a new verification OTP code."""
        html = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto;
                    background: #0f0f23; padding: 40px; border-radius: 16px; color: #e2e8f0;">
            <h2 style="color: #818cf8;">🔐 Verification Code</h2>
            <p style="color: #cbd5e1;">Hi {user.username}, here's your new verification code:</p>
            <div style="text-align: center; margin: 30px 0;">
                <div style="display: inline-block; background: linear-gradient(135deg, #6366f1, #8b5cf6);
                            padding: 16px 40px; border-radius: 12px; font-size: 32px;
                            letter-spacing: 8px; font-weight: bold; color: #fff;">
                    {otp}
                </div>
            </div>
            <p style="color: #94a3b8; font-size: 14px;">This code expires in 10 minutes.</p>
        </div>
        """
        return EmailService._send(
            subject='FitAI — Your Verification Code',
            recipients=user.email,
            html_body=html,
        )

    @staticmethod
    def send_password_reset_email(user, otp):
        """Send password reset OTP email."""
        html = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto;
                    background: #0f0f23; padding: 40px; border-radius: 16px; color: #e2e8f0;">
            <h2 style="color: #f59e0b;">🔑 Password Reset Request</h2>
            <p style="color: #cbd5e1;">Hi {user.username}, we received a request to reset your password.</p>
            <p style="color: #cbd5e1;">Use the code below to set a new password:</p>
            <div style="text-align: center; margin: 30px 0;">
                <div style="display: inline-block; background: linear-gradient(135deg, #f59e0b, #ef4444);
                            padding: 16px 40px; border-radius: 12px; font-size: 32px;
                            letter-spacing: 8px; font-weight: bold; color: #fff;">
                    {otp}
                </div>
            </div>
            <p style="color: #94a3b8; font-size: 14px;">
                This code expires in 10 minutes. If you didn't request this, ignore this email.
            </p>
        </div>
        """
        return EmailService._send(
            subject='FitAI — Password Reset Code',
            recipients=user.email,
            html_body=html,
        )

    @staticmethod
    def send_goal_reminder(user, goal):
        """Send a goal deadline reminder email."""
        html = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto;
                    background: #0f0f23; padding: 40px; border-radius: 16px; color: #e2e8f0;">
            <h2 style="color: #10b981;">⏰ Goal Deadline Approaching</h2>
            <p style="color: #cbd5e1;">Hi {user.username}, your goal is due soon:</p>
            <div style="background: rgba(255,255,255,0.05); border-radius: 12px; padding: 20px;
                        margin: 20px 0; border-left: 4px solid #10b981;">
                <h3 style="color: #f1f5f9; margin-top: 0;">{goal.title}</h3>
                <p style="color: #94a3b8;">Deadline: {goal.deadline.strftime('%B %d, %Y') if goal.deadline else 'No deadline'}</p>
            </div>
            <p style="color: #cbd5e1;">Keep pushing — you're almost there! 💪</p>
        </div>
        """
        return EmailService._send(
            subject=f'FitAI — Goal Reminder: {goal.title}',
            recipients=user.email,
            html_body=html,
        )
