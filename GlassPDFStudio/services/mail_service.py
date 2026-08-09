"""Email service for OTP delivery and notifications."""

from __future__ import annotations

from flask import render_template_string
from flask_mail import Mail, Message

mail = Mail()


def send_otp_email(email: str, otp: str, type_: str = "signup") -> bool:
    """Send OTP verification email.
    
    Args:
        email: Recipient email address
        otp: One-time password code
        type_: 'signup' or 'reset' to determine message content
    
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        if type_ == "signup":
            subject = "Verify your GlassPDFStudio email"
            template = """
            <h2>Email Verification</h2>
            <p>Welcome to GlassPDFStudio!</p>
            <p>Your verification code is:</p>
            <h1 style="color: #0ea5e9; letter-spacing: 2px;">{{ otp }}</h1>
            <p>This code expires in 15 minutes.</p>
            <p>If you didn't sign up for GlassPDFStudio, please ignore this email.</p>
            """
        elif type_ == "reset":
            subject = "Reset your GlassPDFStudio password"
            template = """
            <h2>Password Reset</h2>
            <p>You requested a password reset for your GlassPDFStudio account.</p>
            <p>Your reset code is:</p>
            <h1 style="color: #0ea5e9; letter-spacing: 2px;">{{ otp }}</h1>
            <p>This code expires in 15 minutes.</p>
            <p>If you didn't request this, please ignore this email and your password will remain unchanged.</p>
            """
        else:
            return False

        html_body = render_template_string(template, otp=otp)
        
        msg = Message(
            subject=subject,
            recipients=[email],
            html=html_body,
        )
        
        mail.send(msg)
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to send email to {email}: {e}")
        return False


def send_trial_ending_email(email: str, days_remaining: int) -> bool:
    """Send trial ending notification.
    
    Args:
        email: Recipient email address
        days_remaining: Number of days until trial expires
    
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        subject = f"Your GlassPDFStudio trial ends in {days_remaining} days"
        template = """
        <h2>Your trial is ending soon</h2>
        <p>Hi,</p>
        <p>Your 1-month free trial expires in <strong>{{ days_remaining }} day{{ 's' if days_remaining != 1 else '' }}</strong>.</p>
        <p>Keep using all 33 premium tools by upgrading to Pro:</p>
        <p><strong>Just PKR 500/month</strong> (approx. USD 1.70)</p>
        <p>No lock-in contract. Cancel anytime.</p>
        <p><a href="https://glasspdstudio.com/pricing" style="background: #0ea5e9; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Upgrade to Pro</a></p>
        """
        
        html_body = render_template_string(template, days_remaining=days_remaining)
        
        msg = Message(
            subject=subject,
            recipients=[email],
            html=html_body,
        )
        
        mail.send(msg)
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to send trial ending email to {email}: {e}")
        return False


def send_welcome_email(email: str, trial_end_date: str) -> bool:
    """Send welcome email after trial starts.
    
    Args:
        email: Recipient email address
        trial_end_date: Date when trial expires (YYYY-MM-DD format)
    
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        subject = "Welcome to GlassPDFStudio Pro — Your 1-month free trial starts now!"
        template = """
        <h2>Trial Activated! 🎉</h2>
        <p>Hi,</p>
        <p>Your 1-month free trial has been activated.</p>
        <p><strong>You now have access to all 33 premium PDF tools!</strong></p>
        <p>Trial expires on: <strong>{{ trial_end_date }}</strong></p>
        <h3>What you can do:</h3>
        <ul>
            <li>Merge & split PDFs</li>
            <li>Convert to/from Word, Excel, PowerPoint</li>
            <li>Compress PDFs</li>
            <li>Protect & unlock PDFs</li>
            <li>Add watermarks & signatures</li>
            <li>OCR scanned documents</li>
            <li>And 27 more tools!</li>
        </ul>
        <p><a href="https://glasspdstudio.com/tools" style="background: #0ea5e9; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Start using tools</a></p>
        <p>Questions? <a href="mailto:toheedjutt34@gmail.com">Contact us</a></p>
        """
        
        html_body = render_template_string(
            template, trial_end_date=trial_end_date
        )
        
        msg = Message(
            subject=subject,
            recipients=[email],
            html=html_body,
        )
        
        mail.send(msg)
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to send welcome email to {email}: {e}")
        return False
