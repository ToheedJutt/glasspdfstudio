from __future__ import annotations

from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from services.mail_service import mail_configured
from services.user_service import (
    create_account,
    create_login_otp,
    list_activity,
    verify_login_otp,
    verify_pending_signup,
    authenticate_user,
    start_password_reset,
    verify_password_reset,
    resend_pending_signup,
    resend_password_reset,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def clean_email(raw_email: str | None) -> str:
    """Helper to strip spaces, trailing dots, and lowercase the email address."""
    if not raw_email:
        return ""
    return raw_email.strip().rstrip(".").lower()


@auth_bp.route("/signup", methods=("GET", "POST"))
def signup():
    if request.method == "POST":
        email = clean_email(request.form.get("email"))
        password = request.form.get("password", "")
        if not email or not password:
            flash("Enter email and password", "error")
            return render_template("signup.html")
        try:
            create_account(email, password)
        except ValueError:
            flash("An account with this email already exists.", "error")
            return render_template("signup.html")
        # Instant signup: the account is live immediately and the user is
        # signed straight in — nobody waits on an email that may not arrive.
        session["user"] = email
        flash("Account created — you are signed in.", "success")
        return redirect(url_for("home.index"))
    return render_template("signup.html")


@auth_bp.route("/verify", methods=("GET", "POST"))
def verify():
    email = clean_email(request.args.get("email") or request.form.get("email"))
    if request.method == "POST":
        if request.form.get("resend"):
            # resend OTP for signup
            email = clean_email(request.form.get("email"))
            if resend_pending_signup(email):
                flash("Verification code resent to your email address.", "info")
            else:
                flash("No pending signup found for that email.", "error")
            return redirect(url_for("auth.verify") + f"?email={email}")
        
        email = clean_email(request.form.get("email"))
        otp = request.form.get("otp", "").strip()
        ok = verify_pending_signup(email, otp)
        if ok:
            # AUTO-LOGIN FIX: Log the user in immediately after successful verification
            session["user"] = email
            flash("Account verified! You are now logged in.", "success")
            return redirect(url_for("home.index"))
            
        flash("Verification failed or expired — check the code and try again.", "error")
    return render_template("verify_signup.html", email=email)


@auth_bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        email = clean_email(request.form.get("email"))
        password = request.form.get("password", "")
        if authenticate_user(email, password):
            session["user"] = email
            flash("Signed in successfully.", "success")
            return redirect(url_for("home.index"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")


@auth_bp.route("/login/otp", methods=("POST",))
def login_otp_request():
    """Email a one-time sign-in code (only when mail is really configured)."""
    email = clean_email(request.form.get("email"))
    if not mail_configured():
        flash("Email code sign-in isn't set up on this server yet — please sign in with your password.", "error")
        return redirect(url_for("auth.login"))
    if create_login_otp(email):
        flash("Sign-in code sent to your email address.", "info")
        return redirect(url_for("auth.login_otp_verify") + f"?email={email}")
    flash("No account found for that email.", "error")
    return redirect(url_for("auth.login"))


@auth_bp.route("/login/otp/verify", methods=("GET", "POST"))
def login_otp_verify():
    email = clean_email(request.args.get("email") or request.form.get("email"))
    if request.method == "POST":
        if request.form.get("resend"):
            if create_login_otp(email):
                flash("A new sign-in code was sent to your email address.", "info")
            else:
                flash("Couldn't send a new code — check the email address and try again.", "error")
            return redirect(url_for("auth.login_otp_verify") + f"?email={email}")
        otp = request.form.get("otp", "").strip()
        if verify_login_otp(email, otp):
            session["user"] = email
            flash("Signed in successfully.", "success")
            return redirect(url_for("home.index"))
        flash("That code is wrong or has expired — request a new one and try again.", "error")
    return render_template("login_otp.html", email=email)


@auth_bp.route("/account")
def account():
    """Member page: the signed-in user's personal file history."""
    user = session.get("user")
    if not user:
        flash("Sign in to see your file history.", "info")
        return redirect(url_for("auth.login"))
    return render_template("account.html", email=user, entries=list_activity(user))


@auth_bp.route("/logout")
def logout():
    session.pop("user", None)
    flash("Signed out.", "info")
    return redirect(url_for("home.index"))


@auth_bp.route("/forgot", methods=("GET", "POST"))
def forgot():
    if request.method == "POST":
        email = clean_email(request.form.get("email"))
        if not mail_configured():
            flash("Password reset by email isn't set up on this server yet.", "error")
            return render_template("forgot.html")
        sent = start_password_reset(email)
        if sent:
            flash("Password reset code sent to your email address.", "info")
            return redirect(url_for("auth.reset") + f"?email={email}")
        if sent is None:
            flash("No account found for that email.", "error")
        else:
            flash("The reset email couldn't be sent — please try again later.", "error")
    return render_template("forgot.html")


@auth_bp.route("/reset", methods=("GET", "POST"))
def reset():
    email = clean_email(request.args.get("email") or request.form.get("email"))
    if request.method == "POST":
        if request.form.get("resend"):
            email = clean_email(request.form.get("email"))
            if resend_password_reset(email):
                flash("Reset code resent to your email address.", "info")
            else:
                flash("No account found for that email.", "error")
            return redirect(url_for("auth.reset") + f"?email={email}")
        
        email = clean_email(request.form.get("email"))
        otp = request.form.get("otp", "").strip()
        new_pw = request.form.get("password", "")
        ok = verify_password_reset(email, otp, new_pw)
        if ok:
            flash("Password updated — you can now sign in.", "success")
            return redirect(url_for("auth.login"))
        flash("Reset failed or code expired — check code and try again.", "error")
    return render_template("reset_password.html", email=email)
