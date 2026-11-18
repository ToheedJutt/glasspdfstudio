"""SQLAlchemy models for GlassPDFStudio.

User accounts, trials, OTP verification, and trial blocking.
"""

from __future__ import annotations

from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    """User account with authentication and trial tracking."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Trial management
    trial_started = db.Column(db.DateTime, nullable=True)
    trial_ip = db.Column(db.String(45), nullable=True)  # IPv6 can be long
    trial_device = db.Column(db.String(255), nullable=True)

    def set_password(self, password: str) -> None:
        """Hash and set the password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify the password."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class PendingSignup(db.Model):
    """Pending signup awaiting OTP verification."""

    __tablename__ = "pending_signups"

    email = db.Column(db.String(255), primary_key=True)
    password_hash = db.Column(db.String(255), nullable=False)
    otp = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<PendingSignup {self.email}>"


class PasswordReset(db.Model):
    """Password reset request with OTP."""

    __tablename__ = "password_resets"

    email = db.Column(db.String(255), primary_key=True)
    otp = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<PasswordReset {self.email}>"


class FileActivity(db.Model):
    """One processed file in a member's personal history.

    Recorded for signed-in users every time a tool finishes, so members
    can see (and re-download) what they converted or generated.
    """

    __tablename__ = "file_activities"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), nullable=False, index=True)
    tool = db.Column(db.String(64), nullable=False)
    input_names = db.Column(db.Text, nullable=False, default="")
    output_name = db.Column(db.String(255), nullable=False)
    job_id = db.Column(db.String(64), nullable=False)
    output_size = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<FileActivity {self.email} {self.tool} -> {self.output_name}>"


class LoginOTP(db.Model):
    """One-time sign-in code emailed to an existing user."""

    __tablename__ = "login_otps"

    email = db.Column(db.String(255), primary_key=True)
    otp = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<LoginOTP {self.email}>"


class TrialBlock(db.Model):
    """Records IP/device combos that have claimed a trial to prevent abuse."""

    __tablename__ = "trial_blocks"
    __table_args__ = (
        db.UniqueConstraint(
            "ip_address", "device_id", name="uq_trial_blocks_ip_device"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False, index=True)
    device_id = db.Column(db.String(255), nullable=False, index=True)
    email = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<TrialBlock {self.ip_address}:{self.device_id}>"
