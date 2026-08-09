from __future__ import annotations

from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from services.user_service import (
    create_pending_signup,
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
            otp = create_pending_signup(email, password)
        except ValueError:
            flash("An account with this email already exists.", "error")
            return render_template("signup.html")
        # For now OTP is logged to server console by the service; show next step.
        flash("Verification code sent to your email address.", "info")
        return redirect(url_for("auth.verify") + f"?email={email}")
    return render_template("signup.html")


@auth_bp.route("/verify", methods=("GET", "POST"))
def verify():
    email = clean_email(request.args.get("email") or request.form.get("email"))
    if request.method == "POST":
        if request.form.get("resend"):
            # resend OTP for signup
            email = clean_email(request.form.get("email"))
            if resend_pending_signup(email):
                flash("Verification code resent (check server log in dev).", "info")
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


@auth_bp.route("/logout")
def logout():
    session.pop("user", None)
    flash("Signed out.", "info")
    return redirect(url_for("home.index"))


@auth_bp.route("/forgot", methods=("GET", "POST"))
def forgot():
    if request.method == "POST":
        email = clean_email(request.form.get("email"))
        start_password_reset(email)
        flash("A password reset code was sent (check server log in dev).", "info")
        return redirect(url_for("auth.reset") + f"?email={email}")
    return render_template("forgot.html")


@auth_bp.route("/reset", methods=("GET", "POST"))
def reset():
    email = clean_email(request.args.get("email") or request.form.get("email"))
    if request.method == "POST":
        if request.form.get("resend"):
            email = clean_email(request.form.get("email"))
            if resend_password_reset(email):
                flash("Reset code resent (check server log in dev).", "info")
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