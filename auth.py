import hashlib
import secrets
import pymysql
from config import DB_CONFIG, DATABASE_NAME
import os
import db
import random
import smtplib
import time
from email.mime.text import MIMEText
from threading import Timer
from config import EMAIL_CONFIG
from email.message import EmailMessage

def send_email_with_attachment(to_email, subject, body, attachment_path):
    smtp_host = EMAIL_CONFIG['smtp_host']
    smtp_port = EMAIL_CONFIG['smtp_port']
    smtp_user = EMAIL_CONFIG['smtp_user']
    smtp_password = EMAIL_CONFIG['smtp_password']

    msg = EmailMessage()
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    # Attach PDF file
    with open(attachment_path, 'rb') as f:
        file_data = f.read()
        file_name = os.path.basename(attachment_path)
    msg.add_attachment(file_data, maintype='application', subtype='pdf', filename=file_name)

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False

# Simple in-memory store for OTPs
_otp_store = {}


def send_email(to_email, subject, body):
    # Configure your SMTP settings here
    smtp_host = EMAIL_CONFIG.get('smtp_host', 'smtp.gmail.com')
    smtp_port = EMAIL_CONFIG.get('smtp_port', 587)
    smtp_user = EMAIL_CONFIG.get('smtp_user', '')
    smtp_password = EMAIL_CONFIG.get('smtp_password', '')

    if not smtp_user or not smtp_password:
        print("SMTP credentials are not configured in config.py")
        return False

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = smtp_user
    msg['To'] = to_email

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, [to_email], msg.as_string())
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def generate_otp():
    return '{:06d}'.format(random.randint(0, 999999))


def send_otp(email):
    # Verify user exists for email
    user = get_user_by_email(email)
    if not user:
        return False  # Email not found

    otp = generate_otp()
    _otp_store[email] = otp

    # Schedule OTP removal after 5 minutes
    def remove_otp():
        _otp_store.pop(email, None)

    Timer(300, remove_otp).start()

    # Send OTP email
    subject = "Your OTP for Password Reset"
    body = f"Your OTP code is: {otp}\nThis code will expire in 5 minutes."
    try:
        return send_email(email, subject, body)
    except Exception as e:
        print(f"Failed to send OTP email: {e}")
        return False


def verify_otp(email, otp_input):
    if not email or not otp_input:
        return False
    otp = _otp_store.get(email)
    if otp and otp == str(otp_input).strip():
        # Invalidate OTP after successful verification to prevent replay
        _otp_store.pop(email, None)
        return True
    return False


def update_login_password(email, new_password):
    user = get_user_by_email(email)
    if not user:
        return False

    salt = generate_salt()
    password_hash = hash_password(new_password, salt)

    conn = db.get_connection()
    try:
        with conn.cursor() as cur:
            sql = "UPDATE users SET password_hash=%s, salt=%s WHERE email=%s"
            cur.execute(sql, (password_hash, salt, email))
        conn.commit()
        return True
    except Exception as e:
        print(f"Failed to update password: {e}")
        return False
    finally:
        conn.close()


def get_user_by_email(email):
    conn = db.get_connection()
    try:
        with conn.cursor(db.pymysql.cursors.DictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE email=%s", (email,))
            return cur.fetchone()
    except Exception as e:
        print(f"DB error fetching user by email: {e}")
        return None
    finally:
        conn.close()


def generate_salt():
    """Generate a random salt for password hashing"""
    return secrets.token_hex(16)


def hash_password(password, salt):
    """Hash password with salt using SHA256"""
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()


def verify_password(password, salt, stored_hash):
    """Verify password against stored hash"""
    return hash_password(password, salt) == stored_hash


def authenticate_user(username, password):
    """Authenticate user and return user data if successful"""
    try:
        # Connect to database
        connection = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DATABASE_NAME,
            charset=DB_CONFIG['charset']
        )

        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Get user data
            query = """
            SELECT user_id, username, role, password_hash, salt, full_name, 
                   phone, email, is_active 
            FROM users 
            WHERE username = %s AND is_active = TRUE
            """
            cursor.execute(query, (username,))
            user = cursor.fetchone()

            if not user:
                return None

            # Verify password
            if verify_password(password, user['salt'], user['password_hash']):
                # Remove sensitive data before returning
                user.pop('password_hash', None)
                user.pop('salt', None)
                return user
            else:
                return None

    except Exception as e:
        print(f"Authentication error: {e}")
        return None
    finally:
        if 'connection' in locals():
            connection.close()


def create_user(username, password, role, full_name, phone, email):
    """Create a new user account"""
    try:
        # Connect to database
        connection = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DATABASE_NAME,
            charset=DB_CONFIG['charset']
        )

        # Generate salt and hash password
        salt = generate_salt()
        password_hash = hash_password(password, salt)

        with connection.cursor() as cursor:
            # Insert new user
            query = """
            INSERT INTO users (username, role, password_hash, salt, full_name, phone, email, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
            """
            cursor.execute(query, (username, role, password_hash, salt, full_name, phone, email))
            connection.commit()

            # Return new user's ID
            return cursor.lastrowid

    except Exception as e:
        print(f"User creation error: {e}")
        return None

    finally:
        if 'connection' in locals():
            connection.close()



def update_password(user_id, new_password):
    """Update user password"""
    try:
        # Connect to database  
        connection = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DATABASE_NAME,
            charset=DB_CONFIG['charset']
        )

        # Generate new salt and hash password
        salt = generate_salt()
        password_hash = hash_password(new_password, salt)

        with connection.cursor() as cursor:
            # Update password
            query = "UPDATE users SET password_hash = %s, salt = %s WHERE user_id = %s"
            cursor.execute(query, (password_hash, salt, user_id))
            connection.commit()
            return True

    except Exception as e:
        print(f"Password update error: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()
