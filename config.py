
import re
import json
import os


# Email (SMTP) Settings
EMAIL_CONFIG = {
    'smtp_host': 'smtp.gmail.com',
    'smtp_port': 587,
    'smtp_user': '', #add your email
    'smtp_password': '' #add your app password
}



# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': os.getenv('DB_PASSWORD', '1234'),  # Change this to your MySQL root password
    'charset': 'utf8mb4',
    'autocommit': True
}

DATABASE_NAME = 'inventory_db3'

# Application settings
APP_SETTINGS = {
    'default_theme': 'dark',
    'default_scaling': '100%',
    'tax_rate': 0.18,  # 18% GST
    'currency_symbol': '₹',
    'date_format': '%Y-%m-%d',
    'datetime_format': '%Y-%m-%d %H:%M:%S'
}



SETTINGS_FILE = "user_settings.json"

def save_user_settings(settings: dict):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

def load_user_settings():
    if os.path.isfile(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    # Default settings if file not found
    return {"theme": "dark"}


# User roles
USER_ROLES = ['Admin', 'Employee', 'Supplier']

def validate_password(pwd):
    failed = []
    if len(pwd) < 8:
        failed.append("• At least 8 characters long")
    if not re.search(r"[A-Z]", pwd):
        failed.append("• At least one uppercase letter (A-Z)")
    if not re.search(r"[a-z]", pwd):
        failed.append("• At least one lowercase letter (a-z)")
    if not re.search(r"\d", pwd):
        failed.append("• At least one digit (0-9)")
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", pwd):
        failed.append("• At least one special character (!@#$%^&*)")
    if failed:
        message = "Password must meet all of the following:\n" + "\n".join(failed)
        return False, message
    return True, ""
