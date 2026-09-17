
import customtkinter as ctk
import tkinter.messagebox as messagebox
import tkinter.filedialog as filedialog
import auth
from config import *
import shutil
import os
from datetime import datetime
import db,config
import os
from datetime import datetime
import subprocess

class SettingsFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.create_widgets()

    def create_shop_info_overview(self, parent):
        self.shop_frame = ctk.CTkFrame(parent)
        self.shop_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(self.shop_frame, text="Shop Information", font=ctk.CTkFont(size=18, weight="bold")).pack(
            pady=(10, 15))

        shop_data_frame = ctk.CTkFrame(self.shop_frame)
        shop_data_frame.pack(fill="x", padx=15, pady=10)

        self.shop_info_labels = {}

        fields = ["name", "address1", "address2", "phone", "email", "gstin", "upi_id", "upi_name"]
        for field in fields:
            label = ctk.CTkLabel(shop_data_frame, text=f"{field.title()}: Not set", anchor="center",text_color="gray",font=ctk.CTkFont(size=12),)
            label.pack(fill="x", padx=10, pady=2)
            self.shop_info_labels[field] = label

        edit_btn = ctk.CTkButton(shop_data_frame, text="Edit Shop Info", command=self.open_edit_shop_info)
        edit_btn.pack(pady=10)

        self.load_and_display_shop_info()

    def load_and_display_shop_info(self):
        shop_info = db.get_shop_info()
        if not shop_info:
            shop_info = {
                "name": "Dummy Shop",
                "address1": "123 Address St.",
                "address2": "City, State, ZIP",
                "phone": "9999999999",
                "email": "shop@example.com",
                "gstin": "22ABCDE1234F1",
                "upi_id": "999999999@upi",
                "upi_name": "Dummy Shop"
            }
        for key, label in self.shop_info_labels.items():
            label.configure(text=f"{key.title().replace('_', ' ')}: {shop_info.get(key, 'Not set')}")

    def open_edit_shop_info(self):
        edit_window = ctk.CTkToplevel(self)
        edit_window.title("Edit Shop Information")
        edit_window.geometry("400x500")
        edit_window.grab_set()  # Make modal

        fields = [
            ("name", "Shop Name"),
            ("address1", "Address Line 1"),
            ("address2", "Address Line 2"),
            ("phone", "Phone"),
            ("email", "Email"),
            ("gstin", "GSTIN"),
            ("upi_id", "UPI ID"),
            ("upi_name", "UPI Name"),
        ]

        shop_info = db.get_shop_info() or {}

        self.edit_entries = {}

        container = ctk.CTkScrollableFrame(edit_window)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        for field_key, field_label in fields:
            ctk.CTkLabel(container, text=field_label).pack(anchor="w", pady=(5, 2))
            entry = ctk.CTkEntry(container, width=350)
            entry.pack(fill="x", pady=(0, 10))
            entry.insert(0, shop_info.get(field_key, ""))
            self.edit_entries[field_key] = entry

        btn_frame = ctk.CTkFrame(container)
        btn_frame.pack(fill="x", pady=10)

        save_btn = ctk.CTkButton(btn_frame, text="Save", command=lambda: self.save_shop_info(edit_window))
        save_btn.pack(side="left", padx=10)

        cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", command=edit_window.destroy)
        cancel_btn.pack(side="right", padx=10)

    def save_shop_info(self, window):
        new_data = {key: entry.get().strip() for key, entry in self.edit_entries.items()}

        # Basic validation
        if not new_data["name"]:
            messagebox.showerror("Validation Error", "Shop name cannot be empty.")
            return
        if new_data["email"] and '@' not in new_data["email"]:
            messagebox.showerror("Validation Error", "Please enter a valid email address.")
            return

        if db.update_shop_info(new_data):
            messagebox.showinfo("Success", "Shop information updated successfully.")
            self.load_and_display_shop_info()
            window.destroy()
        else:
            messagebox.showerror("Error", "Failed to update shop information.")

    def create_widgets(self):
        """Create settings widgets"""
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Settings",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=20)

        # Settings sections
        settings_container = ctk.CTkScrollableFrame(self)
        settings_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # Appearance Settings
        self.create_appearance_section(settings_container)

        # User Profile Section
        self.create_profile_section(settings_container)

        # System Settings (Admin only)
        if self.parent.current_user['role'] == 'Admin':
            self.create_system_section(settings_container)
            self.create_shop_info_overview(settings_container)



        # About Section
        self.create_about_section(settings_container)

    def create_appearance_section(self, parent):
        """Create appearance settings section"""
        appearance_frame = ctk.CTkFrame(parent)
        appearance_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            appearance_frame,
            text="Appearance",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(15, 10))

        # Theme selection
        theme_frame = ctk.CTkFrame(appearance_frame)
        theme_frame.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(theme_frame, text="Theme:").pack(side="left", padx=10, pady=10)

        user_settings = config.load_user_settings()
        self.theme_var = ctk.StringVar(value=user_settings.get("theme", "dark"))

        theme_combo = ctk.CTkComboBox(
            theme_frame,
            values=["light", "dark"],
            variable=self.theme_var,
            command=self.change_theme,
            width=120
        )
        theme_combo.pack(side="left", padx=(10, 20), pady=10)

        # UI Scaling
        scaling_frame = ctk.CTkFrame(appearance_frame)
        scaling_frame.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(scaling_frame, text="UI Scale:").pack(side="left", padx=10, pady=10)

        # Load user settings
        user_settings = config.load_user_settings()
        # Get last saved scaling or default to "100%"
        scale_percent = user_settings.get("scaling", "100%")
        self.scaling_var = ctk.StringVar(value=scale_percent)

        scaling_options = ["80%", "90%", "100%", "110%", "120%"]
        scaling_combo = ctk.CTkComboBox(
            scaling_frame,
            values=scaling_options,
            variable=self.scaling_var,
            command=self.change_scaling,
            width=80
        )
        scaling_combo.pack(side="left", padx=(10, 20), pady=10)

    def create_profile_section(self, parent):
        """Create user profile section"""
        profile_frame = ctk.CTkFrame(parent)
        profile_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            profile_frame,
            text="User Profile",
            font=ctk.CTkFont(size=18, weight="bold"),

        ).pack(pady=(15, 10))

        # Current user info
        user_info_frame = ctk.CTkFrame(profile_frame)
        user_info_frame.pack(fill="x", padx=15, pady=10)

        user = self.parent.current_user

        info_text = f"""
Username: {user['username']}
Full Name: {user['full_name']}
Role: {user['role']}
Email: {user['email']}
Phone: {user['phone']}
        """.strip()

        info_label = ctk.CTkLabel(
            user_info_frame,
            text=info_text,
            font=ctk.CTkFont(size=12),
            justify="left",
            text_color='gray'
        )
        info_label.pack(padx=15, pady=15)

        # Change password button
        change_pwd_btn = ctk.CTkButton(
            profile_frame,
            text="Change Password",
            command=self.change_password,
            width=150
        )
        change_pwd_btn.pack(pady=(0, 15))

    def create_system_section(self, parent):
        """Create system settings section (Admin only)"""
        system_frame = ctk.CTkFrame(parent)
        system_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            system_frame,
            text="System Management",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(15, 10))

        # Database backup
        backup_frame = ctk.CTkFrame(system_frame)
        backup_frame.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(
            backup_frame,
            text="Database Backup",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))

        ctk.CTkLabel(
            backup_frame,
            text="Create a backup of the database",
            text_color="gray"
        ).pack()

        backup_btn = ctk.CTkButton(
            backup_frame,
            text="Create Backup",
            command=self.create_backup,
            width=120
        )
        backup_btn.pack(pady=(5, 10))

    def create_about_section(self, parent):
        """Create about section"""
        about_frame = ctk.CTkFrame(parent)
        about_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            about_frame,
            text="About",
            font=ctk.CTkFont(size=18, weight="bold"),

        ).pack(pady=(15, 10))

        about_text = """
Inventory Management System
Version 1.0.0

Built with Python 3.10+ and CustomTkinter
Database: MySQL with PyMySQL
Created: 2025

Features:
• Role-based access control
• Complete inventory tracking
• Point of sale system
• Purchase order management
• Sales reporting
• CSV data export

© 2025 Inventory Management System
        """.strip()

        about_label = ctk.CTkLabel(
            about_frame,
            text=about_text,
            font=ctk.CTkFont(size=12),
            justify="left",
            text_color='gray'
        )
        about_label.pack(padx=15, pady=(0, 15))

    def change_theme(self, theme):
        """Change application theme"""
        ctk.set_appearance_mode(theme)
        # Save to config file
        user_settings = config.load_user_settings()
        user_settings["theme"] = theme
        config.save_user_settings(user_settings)

    def change_scaling(self, scaling):
        scale_value = int(scaling.replace("%", "")) / 100
        try:
            ctk.set_widget_scaling(scale_value)
        except Exception as e:
            pass

        user_settings = config.load_user_settings()
        user_settings["scaling"] = scaling
        config.save_user_settings(user_settings)
        # Refresh current frame by recreating or reloading widgets
        self.destroy()  # destroy current frame
        self.parent.show_frame(SettingsFrame)

    def change_password(self):
        """Change current user password"""
        # Create password change dialog
        pwd_window = ctk.CTkToplevel(self)
        pwd_window.title("Change Password")
        pwd_window.geometry("300x350")
        pwd_window.transient(self)
        pwd_window.grab_set()

        # Form fields
        form_frame = ctk.CTkFrame(pwd_window)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Current password
        ctk.CTkLabel(form_frame, text="Current Password:").pack(pady=(10, 5))
        current_pwd_entry = ctk.CTkEntry(form_frame, show="*", width=200)
        current_pwd_entry.pack(pady=(0, 10))

        # New password
        ctk.CTkLabel(form_frame, text="New Password:").pack(pady=(10, 5))
        new_pwd_entry = ctk.CTkEntry(form_frame, show="*", width=200)
        new_pwd_entry.pack(pady=(0, 10))

        # Confirm password
        ctk.CTkLabel(form_frame, text="Confirm Password:").pack(pady=(10, 5))
        confirm_pwd_entry = ctk.CTkEntry(form_frame, show="*", width=200)
        confirm_pwd_entry.pack(pady=(0, 15))

        # Buttons
        def save_password():
            current_pwd = current_pwd_entry.get()
            new_pwd = new_pwd_entry.get()
            confirm_pwd = confirm_pwd_entry.get()

            if not all([current_pwd, new_pwd, confirm_pwd]):
                messagebox.showerror("Error", "Please fill all fields")
                return

            if new_pwd != confirm_pwd:
                messagebox.showerror("Error", "New passwords do not match")
                return

            valid, msg = validate_password(new_pwd)
            if not valid:
                messagebox.showerror("Error", msg)
                return

            # Verify current password
            user = auth.authenticate_user(
                self.parent.current_user['username'],
                current_pwd
            )

            if not user:
                messagebox.showerror("Error", "Current password is incorrect")
                return

            # Update password
            if auth.update_password(self.parent.current_user['user_id'], new_pwd):
                messagebox.showinfo("Success", "Password changed successfully")
                pwd_window.destroy()
            else:
                messagebox.showerror("Error", "Failed to change password")

        button_frame = ctk.CTkFrame(form_frame)
        button_frame.pack(fill="x", pady=10)

        save_btn = ctk.CTkButton(
            button_frame,
            text="Save",
            command=save_password,
            width=80
        )
        save_btn.pack(side="left", padx=10)

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=pwd_window.destroy,
            width=80
        )
        cancel_btn.pack(side="right", padx=10)



    def create_backup(self):
        backup_path = filedialog.askdirectory(title="Select Backup Location")
        if not backup_path:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"inventory_backup_{timestamp}.sql"
        backup_full_path = os.path.join(backup_path, backup_filename)

        try:
            # Run mysqldump command (replace user/password with your config)
            cmd = [
                "mysqldump",
                "-h", DB_CONFIG['host'],
                "-u", DB_CONFIG['user'],
                f"-p{DB_CONFIG['password']}",
                DATABASE_NAME
            ]
            with open(backup_full_path, 'w') as f:
                subprocess.run(cmd, stdout=f, check=True)

            messagebox.showinfo("Success", f"Backup created successfully at:\n{backup_full_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create backup: {e}")

