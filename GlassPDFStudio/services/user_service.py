"""User service: authentication, OTP, trial management, using SQLAlchemy.

All user data is now stored in SQLite database instead of JSON files.
OTPs are sent via email instead of just printing to console.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import List, Optional

from models import db, User, PendingSignup, PasswordReset, TrialBlock
from services.mail_service import send_otp_email

# Free tier tools - limited selection for users after trial expires or non-trial users
FREE_TIER_TOOLS = [
    "merge_pdf", "split_pdf", "compress_pdf",  # Organize + Optimize
    "jpg_to_pdf", "pdf_to_jpg",  # Basic conversion
]

# Set OTP Expiry to 5 minutes (300 seconds)
OTP_EXPIRY_SECONDS = 5 * 60


def _clean_email(email: str) -> str:
    """Helper to strip spaces, trailing dots, and lowercase the email address."""
    return email.strip().rstrip(".").lower()


def create_pending_signup(email: str, password: str) -> str:
    """Create a pending signup, send OTP via email, return OTP for dev logging."""
    email = _clean_email(email)
    
    # Check if user already exists
    if User.query.filter_by(email=email).first():
        raise ValueError("User already exists")
    
    # Check if pending signup already exists
    existing = PendingSignup.query.filter_by(email=email).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
    
    # Generate OTP
    otp = f"{secrets.randbelow(900000)+100000}"
    
    # Create pending signup record
    pending = PendingSignup(email=email, password_hash=password, otp=otp)
    db.session.add(pending)
    db.session.commit()
    
    # Send OTP via email
    send_otp_email(email, otp, type_="signup")
    print(f"[OTP] signup for {email}: {otp}")  # Still log to console for debugging
    
    return otp


def resend_pending_signup(email: str) -> Optional[str]:
    """Resend OTP for pending signup."""
    email = _clean_email(email)
    pending = PendingSignup.query.filter_by(email=email).first()
    
    if not pending:
        return None
    
    otp = f"{secrets.randbelow(900000)+100000}"
    pending.otp = otp
    pending.created_at = datetime.utcnow()  # Reset timestamp on resend
    db.session.commit()
    
    # Send OTP via email
    send_otp_email(email, otp, type_="signup")
    print(f"[OTP] resend signup for {email}: {otp}")
    
    return otp


def verify_pending_signup(email: str, otp: str) -> bool:
    """Verify OTP and move user to verified users table."""
    email = _clean_email(email)
    pending = PendingSignup.query.filter_by(email=email).first()
    
    if not pending:
        return False
    
    # Check expiry (5 minutes) using UTC datetime delta instead of timestamp ms
    if datetime.utcnow() - pending.created_at > timedelta(seconds=OTP_EXPIRY_SECONDS):
        db.session.delete(pending)
        db.session.commit()
        return False
    
    # Verify OTP
    if str(pending.otp) != str(otp):
        return False
    
    # Create verified user
    user = User(email=email)
    user.set_password(pending.password_hash)
    db.session.add(user)
    
    # Remove pending
    db.session.delete(pending)
    db.session.commit()
    
    return True


def authenticate_user(email: str, password: str) -> bool:
    """Authenticate user by email and password."""
    email = _clean_email(email)
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return False
    
    return user.check_password(password)


def start_password_reset(email: str) -> Optional[str]:
    """Initiate password reset, send OTP via email."""
    email = _clean_email(email)
    user = User.query.filter_by(email=email).first()
    
    if not user:
        # Silently ignore to avoid user enumeration
        return None
    
    otp = f"{secrets.randbelow(900000)+100000}"
    
    # Delete existing reset if any
    existing = PasswordReset.query.filter_by(email=email).first()
    if existing:
        db.session.delete(existing)
    
    # Create reset record
    reset = PasswordReset(email=email, otp=otp)
    db.session.add(reset)
    db.session.commit()
    
    # Send OTP via email
    send_otp_email(email, otp, type_="reset")
    print(f"[OTP] password reset for {email}: {otp}")
    
    return otp


def resend_password_reset(email: str) -> Optional[str]:
    """Resend password reset OTP."""
    email = _clean_email(email)
    reset = PasswordReset.query.filter_by(email=email).first()
    
    if not reset:
        # Create fresh reset if user exists
        user = User.query.filter_by(email=email).first()
        if not user:
            return None
        return start_password_reset(email)
    
    otp = f"{secrets.randbelow(900000)+100000}"
    reset.otp = otp
    reset.created_at = datetime.utcnow()  # Reset timestamp on resend
    db.session.commit()
    
    # Send OTP via email
    send_otp_email(email, otp, type_="reset")
    print(f"[OTP] resend password reset for {email}: {otp}")
    
    return otp


def verify_password_reset(email: str, otp: str, new_password: str) -> bool:
    """Verify reset OTP and update password."""
    email = _clean_email(email)
    reset = PasswordReset.query.filter_by(email=email).first()
    
    if not reset:
        return False
    
    # Check expiry (5 minutes) using UTC datetime delta instead of timestamp ms
    if datetime.utcnow() - reset.created_at > timedelta(seconds=OTP_EXPIRY_SECONDS):
        db.session.delete(reset)
        db.session.commit()
        return False
    
    # Verify OTP
    if str(reset.otp) != str(otp):
        return False
    
    # Update password
    user = User.query.filter_by(email=email).first()
    if not user:
        return False
    
    user.set_password(new_password)
    db.session.delete(reset)
    db.session.commit()
    
    return True


def start_trial(
    email: str, ip_address: str = "unknown", device_id: str = "unknown"
) -> bool:
    """Start trial for user and record IP/device to prevent abuse."""
    email = _clean_email(email)
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return False
    
    user.trial_started = datetime.utcnow()
    user.trial_ip = ip_address
    user.trial_device = device_id
    db.session.commit()
    
    # Record this IP/device combo to block future trials
    existing_block = TrialBlock.query.filter_by(
        ip_address=ip_address, device_id=device_id
    ).first()
    if not existing_block:
        block = TrialBlock(ip_address=ip_address, device_id=device_id, email=email)
        db.session.add(block)
        db.session.commit()
    
    # Send welcome email
    trial_end = user.trial_started + timedelta(days=30)
    from services.mail_service import send_welcome_email
    send_welcome_email(email, trial_end.strftime("%Y-%m-%d"))
    
    return True


def is_ip_device_blocked_from_trial(ip_address: str, device_id: str) -> bool:
    """Check if this IP/device combo has already claimed a trial."""
    block = TrialBlock.query.filter_by(
        ip_address=ip_address, device_id=device_id
    ).first()
    return block is not None


def is_trial_active(email: str) -> bool:
    """Check if user has active trial (within 30 days)."""
    email = _clean_email(email)
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.trial_started:
        return False
    
    trial_end = user.trial_started + timedelta(days=30)
    return datetime.utcnow() < trial_end


def trial_end_date(email: str) -> Optional[int]:
    """Return Unix timestamp of trial expiry, or None if no trial."""
    email = _clean_email(email)
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.trial_started:
        return None
    
    trial_end = user.trial_started + timedelta(days=30)
    return int(trial_end.timestamp())


def get_user_tier(email: str) -> str:
    """Return 'trial' if user has active trial, else 'free'."""
    email = _clean_email(email)
    if is_trial_active(email):
        return "trial"
    return "free"


def get_accessible_tools(email: Optional[str]) -> List[str] | None:
    """Return list of tool IDs accessible to user based on their tier.
    
    Returns:
        None if all tools accessible (trial user)
        List of tool IDs if free tier
    """
    if not email:
        return FREE_TIER_TOOLS
    
    tier = get_user_tier(email)
    if tier == "trial":
        # Trial users get access to ALL tools
        return None
    else:
        # Free tier only gets basic tools
        return FREE_TIER_TOOLS