
import customtkinter as ctk
import tkinter.messagebox as messagebox
import auth

class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, login_callback):
        super().__init__(parent)
        self.login_callback = login_callback

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_widgets()

    def create_widgets(self):
        """Create login form widgets"""



        # Main container
        self.login_container = ctk.CTkFrame(self, width=400, height=500)
        self.login_container.grid(row=0, column=0)
        self.login_container.grid_propagate(False)

        # Help button - placed at the top right IN the login_container
        self.help_btn = ctk.CTkButton(
            self.login_container,  # attach to login_container, NOT to self!
            text="❔",
            width=0,
            command=self.show_help_dialog,
            fg_color="gray",
            text_color="white"
        )
        self.help_btn.grid(row=0, column=1, sticky="ne", padx=10, pady=10)

        # Title
        self.title_label = ctk.CTkLabel(
            self.login_container,
            text="Inventory Management System",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.grid(row=1, column=0, columnspan=2, padx=20, pady=30)

        # Role selection
        self.role_label = ctk.CTkLabel(self.login_container, text="Role:")
        self.role_label.grid(row=2, column=0, padx=20, pady=10, sticky="w")

        self.role_var = ctk.StringVar(value="Admin")
        self.role_dropdown = ctk.CTkComboBox(
            self.login_container,
            values=["Admin", "Employee", "Supplier"],
            variable=self.role_var,
            state="readonly"
        )
        self.role_dropdown.grid(row=2, column=1, padx=20, pady=10, sticky="ew")

        # Username
        self.username_label = ctk.CTkLabel(self.login_container, text="Username:")
        self.username_label.grid(row=3, column=0, padx=20, pady=10, sticky="w")

        self.username_entry = ctk.CTkEntry(self.login_container, placeholder_text="Enter username")
        self.username_entry.grid(row=3, column=1, padx=20, pady=10, sticky="ew")

        # Password
        self.password_label = ctk.CTkLabel(self.login_container, text="Password:")
        self.password_label.grid(row=4, column=0, padx=20, pady=10, sticky="w")

        self.password_entry = ctk.CTkEntry(self.login_container, placeholder_text="Enter password", show="*")
        self.password_entry.grid(row=4, column=1, padx=20, pady=10, sticky="ew")
        self.username_entry.insert(0,'admin')
        self.password_entry.insert(0,'Admin@123')
        # Login button
        self.login_button = ctk.CTkButton(
            self.login_container,
            text="Login",
            command=self.handle_login,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.login_button.grid(row=5, column=0, columnspan=2, padx=20, pady=30, sticky="ew")

        # existing widgets ...
        self.forgot_pwd_btn = ctk.CTkButton(
            self.login_container,
            text="Forgot Password?",
            command=self.forgot_password_flow,
            fg_color="transparent",
            text_color="#3B82F6",
            hover_color="lightblue"
        )

        self.forgot_pwd_btn.grid(row=6, column=0, columnspan=2, pady=(0, 20))


        # Configure column weights
        self.login_container.grid_columnconfigure(1, weight=1)

        # Bind Enter key to login
        self.master.bind("<Return>", lambda event: self.handle_login())

    def forgot_password_flow(self):
        self.reset_win = ctk.CTkToplevel(self)
        self.reset_win.title("Reset Password")
        self.reset_win.geometry("350x250")
        self.reset_win.grab_set()

        # Step 1: Email Entry Frame
        self.email_frame = ctk.CTkFrame(self.reset_win)
        self.email_frame.pack(fill="both", expand=True,pady=50,padx=20)

        ctk.CTkLabel(self.email_frame, text="Enter your registered email:").pack(pady=10)
        self.email_entry = ctk.CTkEntry(self.email_frame, width=200)
        self.email_entry.pack(pady=10)
        ctk.CTkButton(self.email_frame, text="Send OTP", command=self.send_otp_action).pack(pady=10)

    def send_otp_action(self):
        email = self.email_entry.get().strip()
        if not email:
            messagebox.showerror("Error", "Please enter your email")
            return
        # Call backend: if email exists: send OTP, else error
        success = auth.send_otp(email)
        if success:
            self.email_frame.pack_forget()
            self.otp_frame = ctk.CTkFrame(self.reset_win)
            self.otp_frame.pack(fill="both", expand=True,pady=50,padx=20)
            ctk.CTkLabel(self.otp_frame, text="Enter the OTP sent to your email:").pack(pady=10)
            self.otp_entry = ctk.CTkEntry(self.otp_frame, width=100)
            self.otp_entry.pack(pady=10)
            ctk.CTkButton(self.otp_frame, text="Verify OTP", command=self.verify_otp_action).pack(pady=10)
        else:
            messagebox.showerror("Error", "Email not found")

    def verify_otp_action(self):
        otp = self.otp_entry.get().strip()
        email = self.email_entry.get().strip()
        if auth.verify_otp(email, otp):
            self.otp_frame.pack_forget()
            # Show password reset frame next
            self.reset_pass_frame = ctk.CTkFrame(self.reset_win)
            self.reset_pass_frame.pack(fill="both", expand=True)
            ctk.CTkLabel(self.reset_pass_frame, text="Enter new password:").pack(pady=10)
            self.new_pass_entry = ctk.CTkEntry(self.reset_pass_frame, show="*", width=200)
            self.new_pass_entry.pack(pady=10)
            ctk.CTkLabel(self.reset_pass_frame, text="Confirm new password:").pack(pady=10)
            self.confirm_pass_entry = ctk.CTkEntry(self.reset_pass_frame, show="*", width=200)
            self.confirm_pass_entry.pack(pady=10)
            ctk.CTkButton(self.reset_pass_frame, text="Reset Password", command=self.reset_password_action).pack(
                pady=10)
        else:
            messagebox.showerror("Error", "Invalid OTP")

    def reset_password_action(self):
        new_pass = self.new_pass_entry.get()
        confirm_pass = self.confirm_pass_entry.get()
        email = self.email_entry.get()
        if not new_pass or not confirm_pass:
            messagebox.showerror("Error", "Please enter and confirm new password")
            return
        if new_pass != confirm_pass:
            messagebox.showerror("Error", "Passwords do not match")
            return
        # Call backend to update password
        success = auth.update_login_password(email, new_pass)
        if success:
            messagebox.showinfo("Success", "Password has been reset. Please login.")
            self.reset_win.destroy()
        else:
            messagebox.showerror("Error", "Failed to reset password. Try again.")

    def show_help_dialog(self):
        demo_text = (
            "* Demo User Accounts for Quick Access *\n\n"
            "1. Admin Account:\n"
            "   - Username: admin\n"
            "   - Password: Admin@123\n\n"
            "2. Employee Account:\n"
            "   - Username: emp\n"
            "   - Password: Emp@123\n\n"
            "3. Supplier Account:\n"
            "   - Username: supp\n"
            "   - Password: Supp@123\n\n"
            "⚠️ For security, please change these default passwords after first login.\n"
            "If you forget your password, use the 'Forgot Password' option or contact your administrator.\n"
        )

        messagebox.showinfo("Demo Credentials", demo_text)

    def handle_login(self):
        """Handle login attempt"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return

        # Authenticate user
        user_data = auth.authenticate_user(username, password)

        if user_data:
            # Check if role matches selected role
            if user_data['role'] != self.role_var.get():
                messagebox.showerror("Error", "Role mismatch. Please select the correct role.")
                return

            # Successful login
            self.login_callback(user_data)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")
            self.password_entry.delete(0, 'end')  # Clear password field
