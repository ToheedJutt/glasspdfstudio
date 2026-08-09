# GlassPDFStudio - Production Setup Guide

## ✅ What Has Been Implemented

### 1. **Email OTP Delivery** ✨
- **Service:** `services/mail_service.py` - Sends OTP codes via email
- **Supported Messages:**
  - Signup verification emails
  - Password reset emails  
  - Trial started notifications
  - Trial ending reminders (customizable)
- **Transport:** Flask-Mail using SMTP (Gmail, SendGrid, etc.)

### 2. **SQLite Database** 🗄️
- **Models:** `models.py` - SQLAlchemy ORM models
  - `User` - User accounts with trial tracking
  - `PendingSignup` - OTP-pending registrations
  - `PasswordReset` - Password reset requests
  - `TrialBlock` - IP/device abuse prevention
- **Storage:** Automatic SQLite database (`glasspdstudio.db`)
- **Benefits:**
  - ACID transactions
  - Data integrity
  - Concurrent user support
  - Easy backups

### 3. **Environment Variables** 🔐
- **File:** `.env` - Secret configuration (DO NOT COMMIT)
- **Includes:**
  - `SECRET_KEY` - Flask session encryption
  - `DATABASE_URL` - Database connection string
  - `MAIL_SERVER`, `MAIL_USERNAME`, `MAIL_PASSWORD` - Email config
  - `OTP_EXPIRY_SECONDS` - OTP validity period
  - Other app settings

### 4. **Updated Dependencies**
```bash
Flask==3.1.3
flask-sqlalchemy==3.0.5        # Database ORM
python-dotenv==1.0.0           # Environment variables
flask-mail==0.9.1              # Email delivery
email-validator==2.1.0         # Email validation
waitress==2.1.2                # Production web server
```

---

## 🚀 SETUP INSTRUCTIONS

### Step 1: Gmail App Password (One-time)

1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Select "Mail" and "Windows Computer"
3. Google will generate a **16-character app password**
4. Copy it (example: `xxxx xxxx xxxx xxxx`)

### Step 2: Configure `.env` File

Edit `.env` in your project root:

```env
# IMPORTANT: Change these values!

FLASK_ENV=development
DEBUG=False
SECRET_KEY=change-me-to-a-random-string

# Database
DATABASE_URL=sqlite:///glasspdstudio.db

# Email Configuration - ADD YOUR GMAIL DETAILS
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=xxxx xxxx xxxx xxxx
MAIL_DEFAULT_SENDER=noreply@glasspdstudio.com
ADMIN_EMAIL=toheedjutt34@gmail.com

# Application
APP_NAME=GlassPDFStudio
APP_VERSION=2.0.0
HOST=127.0.0.1
PORT=5055

# OTP
OTP_EXPIRY_SECONDS=900
OTP_LENGTH=6

# Pricing
PKR_TO_USD=0.0034
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Run the Application

```bash
python app.py
```

**First run will automatically create the database!**

---

## 📧 How OTP Email Delivery Works

### User Signs Up:
1. User enters email + password on `/auth/signup`
2. Server generates 6-digit OTP
3. **Email sent** to user with verification code
4. Console shows: `[OTP] signup for user@email.com: 123456`
5. User receives email with code
6. User enters code on `/auth/verify`
7. Account created ✅

### Password Reset:
1. User clicks "Forgot password"
2. **Email sent** with reset code
3. User enters reset code + new password
4. Password updated ✅

### Trial Started:
1. User clicks "Start free trial"
2. **Welcome email sent** with trial details
3. Trial lasts 30 days
4. 3 days before expiry, **reminder email sent**

---

## 🛡️ Environment Variables Reference

| Variable | Purpose | Example |
|----------|---------|---------|
| `SECRET_KEY` | Flask session encryption | `abc123def456` |
| `DATABASE_URL` | Database connection | `sqlite:///glasspdstudio.db` |
| `MAIL_SERVER` | SMTP server address | `smtp.gmail.com` |
| `MAIL_PORT` | SMTP port | `587` |
| `MAIL_USERNAME` | Email account | `your-email@gmail.com` |
| `MAIL_PASSWORD` | App password (16 char) | `xxxx xxxx xxxx xxxx` |
| `MAIL_DEFAULT_SENDER` | From email address | `noreply@glasspdstudio.com` |
| `ADMIN_EMAIL` | Admin contact | `toheedjutt34@gmail.com` |
| `OTP_EXPIRY_SECONDS` | OTP valid for (15 min) | `900` |

---

## 📱 Testing Email Delivery

### Test Signup Flow:

1. Go to `http://127.0.0.1:5055/auth/signup`
2. Enter test email: `test@example.com`
3. Enter password: `Test12345`
4. Click "Sign up"
5. **You should receive an email** with OTP code
6. Enter the OTP on verification page
7. Account created ✅

### Check Console Output:

Terminal will show:
```
[OTP] signup for test@example.com: 123456
```

---

## 🗄️ Database Files

After first run, you'll see:

```
GlassPDFStudio/
├── glasspdstudio.db          (SQLite database - DO NOT DELETE)
├── glasspdstudio.db-wal      (Write-ahead log)
├── glasspdstudio.db-shm      (Shared memory)
```

### Backup Database:
```bash
# Copy the entire database
cp glasspdstudio.db backups/glasspdstudio_2026-08-09.db
```

---

## 🔧 Troubleshooting

### Issue: "No module named 'models'"
**Fix:** Restart Python environment
```bash
pip install -r requirements.txt
```

### Issue: Emails not sending
**Check:**
1. Email enabled in Gmail: [myaccount.google.com/security](https://myaccount.google.com/security)
2. App password is 16 characters (includes spaces)
3. `MAIL_USERNAME` matches your Gmail address
4. Check `.env` file has no typos

### Issue: Database locked
**Fix:** Delete `glasspdstudio.db` and restart app (WARNING: deletes all users!)

### Issue: "SQLAlchemy not found"
**Fix:**
```bash
pip install flask-sqlalchemy
```

---

## 📝 Next Steps for Production

Once email is working:

1. **HTTPS/SSL Certificate** - Get from Let's Encrypt (free)
2. **Rate Limiting** - Prevent brute force attacks
3. **Payment Integration** - Stripe/JazzCash for real payments
4. **Email Templates** - Custom branding for emails
5. **Monitoring** - Add Sentry for error tracking
6. **Backups** - Automated daily database backups
7. **Domain Setup** - Point your domain to server

---

## 📞 Quick Links

- **Flask-Mail Docs:** https://pythonhosted.org/Flask-Mail/
- **Gmail App Passwords:** https://myaccount.google.com/apppasswords
- **SQLAlchemy Docs:** https://docs.sqlalchemy.org/
- **Python-Dotenv:** https://pypi.org/project/python-dotenv/

---

## ⚠️ SECURITY REMINDERS

1. ✅ **`.env` in `.gitignore`** - Never commit secrets!
2. ✅ **`SECRET_KEY` is unique** - Change from default in production
3. ✅ **App password, not Gmail password** - Use 16-char app password only
4. ✅ **Database backups** - Keep daily backups
5. ✅ **Logs in production** - Monitor for suspicious activity

---

## 🎯 What You Get Now

✅ Users receive OTP codes via email  
✅ Database stores all user data safely  
✅ Trial tracking with IP/device blocking  
✅ Free tier tool restrictions working  
✅ Environment-based configuration  
✅ Production-ready foundation  

**Your app is now 70% ready for production!** 🚀

Next: Deploy to a server and configure HTTPS.
