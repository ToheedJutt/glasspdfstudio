# GlassPDFStudio - Production Readiness Checklist

## 🔴 CRITICAL ISSUES (Must Fix Before Public)

### 1. **OTP Delivery System** ⚠️ HIGHEST PRIORITY
**Current State:** OTPs are only printed to server console
```
[OTP] signup for user@email.com: 123456
```
**Problem:** Users can't actually receive verification codes

**Solution Options:**
- **Email (Recommended):** Use `flask-mail` or `sendgrid-python`
- **SMS:** Use Twilio or AWS SNS
- **Mixed:** Email for signup, SMS for password reset

**Implementation needed in:** `services/user_service.py`
```python
# Add to requirements.txt:
# flask-mail==0.9.1  # For email delivery
# OR
# twilio==8.10.0  # For SMS via Twilio
```

---

### 2. **Database Migration** 🗄️
**Current State:** User data stored in JSON files (`storage/users.json`)
- No data integrity
- No ACID transactions
- No concurrent user support
- All data in plain text files

**Files to replace:**
- `users.json` → SQLite database
- `pending_signups.json` → Database table
- `password_resets.json` → Database table
- `trial_blocks.json` → Database table

**Implementation Plan:**
```bash
# Add to requirements.txt:
# flask-sqlalchemy==3.0.5
# python-dotenv==1.0.0
```

**Create `models.py`:**
```python
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    trial_started = db.Column(db.DateTime)
    trial_ip = db.Column(db.String(45))
    trial_device = db.Column(db.String(255))

class TrialBlock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)
    device_id = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('ip_address', 'device_id'),)

class PendingSignup(db.Model):
    email = db.Column(db.String(255), primary_key=True)
    password_hash = db.Column(db.String(255), nullable=False)
    otp = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

---

### 3. **Environment Variables & Secret Management** 🔐
**Current State:** Hardcoded in `config.py`
```python
SECRET_KEY: str = "dev-secret-change-me"  # ❌ EXPOSED
HOST: str = "127.0.0.1"  # ❌ LOCALHOST ONLY
```

**Create `.env` file (NEVER commit to git):**
```env
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-generate-with-secrets.token_hex(32)
DATABASE_URL=sqlite:///glasspdstudio.db
# OR PostgreSQL: postgresql://user:password@localhost/glasspdstudio

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password

# SMS Configuration (if using Twilio)
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=+1234567890

# PKR to USD conversion
PKR_TO_USD=0.0034

# Admin contact
ADMIN_EMAIL=toheedjutt34@gmail.com
```

**Update `config.py`:**
```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///glasspdstudio.db"
    )
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
```

---

## 🟡 HIGH PRIORITY ISSUES

### 4. **Production WSGI Server** 🚀
**Current State:** Running Flask built-in dev server
```bash
python app.py  # ❌ NOT PRODUCTION-SAFE
```

**Switch to Gunicorn:**
```bash
# Add to requirements.txt:
# gunicorn==21.2.0

# Run with:
gunicorn -w 4 -b 0.0.0.0:5055 app:create_app()
```

**Better: Use Waitress (Windows-friendly):**
```bash
# Add to requirements.txt:
# waitress==2.1.2

# In app.py at bottom:
if __name__ == "__main__":
    from waitress import serve
    serve(create_app(), host="0.0.0.0", port=5055, threads=4)
```

---

### 5. **HTTPS/SSL Certificate** 🔒
**Current State:** HTTP only (no encryption)

**Required for:**
- Payment processing (even WhatsApp integration needs secure channel)
- User data protection (passwords, emails)
- Trust and professionalism

**Solutions:**
- **Free:** Let's Encrypt + Certbot
- **Paid:** DigiCert, AWS Certificate Manager
- **Cloud:** Auto-handled by Heroku, Railway, Render

---

### 6. **Rate Limiting & Brute Force Protection** 🛡️
**Current State:** No protection against:
- OTP brute force attacks (try all 1M combinations)
- Login attempts (unlimited guesses)
- API abuse

**Add to requirements.txt:**
```
# flask-limiter==3.5.0
```

**Example in routes/auth.py:**
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@auth_bp.route("/login", methods=("POST",))
@limiter.limit("5 per minute")  # Max 5 login attempts/minute
def login():
    # ... existing code
```

---

### 7. **Input Validation & XSS Protection** ✅
**Current State:** Minimal validation
```python
email = request.form.get("email", "").strip().lower()
if not email or not password:  # ❌ Only checks if empty
    flash("Enter email and password", "error")
```

**Add proper validation:**
```bash
# Add to requirements.txt:
# flask-wtf==1.2.1
# email-validator==2.1.0
```

**Example:**
```python
from email_validator import validate_email, EmailNotValidError

try:
    valid_email = validate_email(email).email
except EmailNotValidError:
    flash("Invalid email address", "error")
    return

# Password strength
if len(password) < 8:
    flash("Password must be at least 8 characters", "error")
    return
```

---

## 🟢 MEDIUM PRIORITY ISSUES

### 8. **Logging & Monitoring** 📊
**Current State:** No logs (Flask debug prints only)

**Add logging:**
```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/glasspdstudio.log', 
                                      maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s'
    ))
    app.logger.addHandler(file_handler)
```

---

### 9. **Error Pages & Exception Handling** ⚠️
**Current State:** Generic Flask error pages

**Add custom error handlers:**
```python
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    app.logger.error(f'Server error: {e}')
    return render_template('500.html'), 500
```

**Create:**
- `templates/500.html` - Server error page
- `templates/maintenance.html` - Maintenance mode

---

### 10. **CORS & Security Headers** 🔐
**Add to app.py:**
```python
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

---

## 🟡 MEDIUM-LOW PRIORITY

### 11. **Trial & Subscription Management** 💳
**Current State:** Trial tracking only, no actual payment/cancellation

**Needed:**
- Trial expiry notifications (email 3 days before)
- Automatic trial-to-paid conversion workflow
- Payment integration (Stripe, JazzCash, EasyPaisa for PKR)
- Subscription cancellation flow
- Invoice generation

**For now:**
- Add email template for "Trial ending in 3 days"
- Add email template for "Trial expired, upgrade to Pro"

---

### 12. **Backup & Data Recovery** 💾
**Current State:** No backups
- If server crashes, all user data is lost
- No way to recover deleted accounts

**Minimum setup:**
```bash
# Daily automated backups to S3 or Google Drive
# Keep 30-day retention
# Test restore process monthly
```

---

### 13. **API Documentation** 📚
**Current State:** No API docs

**Add Swagger/OpenAPI:**
```bash
# pip install flasgger
```

---

## 📋 DEPLOYMENT STEPS

### **Step 1: Prepare Environment**
```bash
# 1. Create production `.env` file
cp .env.example .env
# Edit with real values

# 2. Create database
python -c "from app import create_app, db; app = create_app(); db.create_all()"

# 3. Generate strong SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"
# Copy output to .env
```

### **Step 2: Server Setup (Ubuntu/Debian)**
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-venv python3-pip nginx postgresql -y

# Clone your project
cd /var/www
git clone your-repo glasspdstudio
cd glasspdstudio

# Virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### **Step 3: Configure Nginx**
```nginx
# /etc/nginx/sites-available/glasspdstudio
server {
    listen 80;
    server_name glasspdstudio.com www.glasspdstudio.com;

    location / {
        proxy_pass http://127.0.0.1:5055;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/glasspdstudio/static/;
    }
}
```

### **Step 4: Run with Gunicorn + Systemd**
```bash
# /etc/systemd/system/glasspdstudio.service
[Unit]
Description=GlassPDFStudio Flask App
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/glasspdstudio
Environment="PATH=/var/www/glasspdstudio/venv/bin"
ExecStart=/var/www/glasspdstudio/venv/bin/gunicorn -w 4 -b 127.0.0.1:5055 app:create_app()
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 🚦 BEFORE GOING PUBLIC - FINAL CHECKLIST

- [ ] OTP delivery working (email or SMS)
- [ ] Database migrated from JSON
- [ ] Environment variables configured
- [ ] SECRET_KEY is strong and unique
- [ ] HTTPS/SSL certificate installed
- [ ] Rate limiting enabled
- [ ] Input validation & XSS protection
- [ ] Logging configured
- [ ] Error pages customized
- [ ] Security headers added
- [ ] WSGI server (Gunicorn/Waitress) configured
- [ ] Database backups automated
- [ ] Testing completed (auth, trials, tools)
- [ ] Terms of Service & Privacy Policy pages
- [ ] Contact form working
- [ ] Admin dashboard (if needed)
- [ ] Monitoring & alerts set up
- [ ] Rollback plan documented

---

## ⚠️ SECURITY REMINDERS

1. **NEVER commit `.env` to git** - Add to `.gitignore`
2. **Change demo phone number** - Currently `+923094986325` in WhatsApp links
3. **Remove debug prints** - Replace all `print()` with `app.logger`
4. **Hash passwords** - Already using Werkzeug (good!)
5. **CORS origins** - Restrict to your domain only
6. **Rate limits** - Prevent brute force & DDoS
7. **SQL injection** - Use SQLAlchemy ORM (not raw SQL)
8. **File uploads** - Validate file types in `/api/process`

---

## 📞 RECOMMENDED PAID SERVICES FOR PRODUCTION

1. **Email:** SendGrid, AWS SES, Mailgun (~$0-10/month)
2. **SMS:** Twilio (~$0.01 per SMS)
3. **Hosting:** Railway, Render, Heroku, AWS (~$10-50/month)
4. **Database:** Managed PostgreSQL on Railway/Render (~$7/month)
5. **SSL:** Let's Encrypt (free)
6. **Monitoring:** Sentry (free tier available)
7. **Payment:** Stripe, JazzCash API, EasyPaisa (~2-3% fees)

**Estimated Monthly Cost:** $30-80 for production setup
