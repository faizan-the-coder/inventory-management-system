import customtkinter as ctk
import tkinter.messagebox as messagebox
import tkinter.ttk as ttk
import auth
import db
from config import USER_ROLES
import csv
from tkinter import filedialog
import re
from config import validate_password


class UsersFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        # Only admin can access this frame
        if self.parent.current_user['role'] != 'Admin':
            self.show_access_denied()
            return

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.create_widgets()
        self.load_users()

    def show_access_denied(self):
        """Show access denied message"""
        access_label = ctk.CTkLabel(
            self,
            text="Access Denied\n\nOnly administrators can manage users.",
            font=ctk.CTkFont(size=18),
            text_color="red"
        )
        access_label.pack(expand=True)

    def create_widgets(self):
        """Create user management widgets"""
        # Title and controls
        title_frame = ctk.CTkFrame(self)
        title_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        self.title_label = ctk.CTkLabel(
            title_frame,
            text="User Management",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(side="left", padx=(20, 40), pady=10)

        # Create a filter frame to group Role + Active filters
        filter_frame = ctk.CTkFrame(title_frame)
        filter_frame.pack(side="right", padx=20)

        self.role_filter = ctk.CTkComboBox(filter_frame, values=["All"] + USER_ROLES, width=120)
        self.role_filter.pack(side="left", padx=(0, 10))

        self.active_filter = ctk.CTkComboBox(filter_frame, values=["All", "Active", "Inactive"], width=100)
        self.active_filter.pack(side="left")

        self.role_filter.set("All")
        self.role_filter.pack(side="right", padx=5)
        self.role_filter.configure(command=lambda _: self.load_users())

        self.active_filter.set("All")
        self.active_filter.pack(side="right", padx=5)
        self.active_filter.configure(command=lambda _: self.load_users())

        self.search_entry = ctk.CTkEntry(title_frame, placeholder_text="Search users...")
        self.search_entry.pack(side="right", padx=10)
        self.search_entry.bind("<KeyRelease>", lambda e: self.search_users())

        add_user_btn = ctk.CTkButton(
            title_frame,
            text="Add User",
            command=self.add_user,
            width=100
        )
        add_user_btn.pack(side="right", padx=20, pady=10)

        # Users table
        self.create_users_table()

        # Action buttons
        self.create_action_buttons()

    def create_users_table(self):
        """Create users table"""
        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Create Treeview
        columns = ("User ID", "Username", "Role", "Full Name", "Phone", "Email", "Active", "Created")
        self.users_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        # Configure columns
        column_widths = {"User ID": 70, "Username": 100, "Role": 80, "Full Name": 150,
                         "Phone": 120, "Email": 180, "Active": 60, "Created": 100}

        for col in columns:
            self.users_tree.heading(col, text=col)
            self.users_tree.column(col, width=column_widths.get(col, 100), minwidth=50)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.users_tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=self.users_tree.xview)
        self.users_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        self.users_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
        style.configure("Treeview", font=("Arial", 10))

        self.users_tree.tag_configure('Admin', background='#ffd6d6')  # Light red
        self.users_tree.tag_configure('Employee', background='#d6e0ff')  # Light blue
        self.users_tree.tag_configure('Supplier', background='#d6ffd6')  # Light green

        # Bind double-click to edit
        self.users_tree.bind("<Double-1>", lambda e: self.edit_user())

        self.users_tree.bind("<<TreeviewSelect>>", lambda e: self.update_toggle_active_button_text())

    def create_action_buttons(self):
        """Create action buttons"""
        actions_frame = ctk.CTkFrame(self)
        actions_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)

        edit_btn = ctk.CTkButton(
            actions_frame,
            text="Edit Selected",
            command=self.edit_user,
            width=120
        )
        edit_btn.pack(side="left", padx=10, pady=10)

        reset_pwd_btn = ctk.CTkButton(
            actions_frame,
            text="Reset Password",
            command=self.reset_password,
            width=120
        )
        reset_pwd_btn.pack(side="left", padx=(5, 10), pady=10)

        self.toggle_active_btn = ctk.CTkButton(
            actions_frame,
            text="Toggle Active",
            command=self.toggle_user_active,
            width=120
        )
        self.toggle_active_btn.pack(side="left", padx=(5, 10), pady=10)

        self.delete_btn = ctk.CTkButton(
            actions_frame,
            text="Delete Selected",
            command=self.delete_user,
            width=120,
            fg_color="red",
            hover_color="darkred"
        )
        self.delete_btn.pack(side="left", padx=(5, 10), pady=10)

        export_btn = ctk.CTkButton(actions_frame, text="Export to CSV", command=self.export_users_to_csv)
        export_btn.pack(side="right", padx=5)

        refresh_btn = ctk.CTkButton(
            actions_frame,
            text="Refresh",
            command=self.load_users,
            width=80
        )
        refresh_btn.pack(side="right", padx=10, pady=10)


    # New method
    def update_toggle_active_button_text(self):
        selection = self.users_tree.selection()
        if not selection:
            self.toggle_active_btn.configure(text="Toggle Active")
            return
        user_data = self.users_tree.item(selection[0])['values']
        is_active = user_data[6] == "Yes"
        self.toggle_active_btn.configure(text="Deactivate User" if is_active else "Activate User")

    def delete_user(self):
        selection = self.users_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a user to delete")
            return

        user_data = self.users_tree.item(selection[0])['values']
        user_id = user_data[0]
        username = user_data[1]

        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete user '{username}'?"):
            return

        try:
            success = db.delete_user(user_id)
            if success:
                messagebox.showinfo("Success", "User deleted successfully")
                self.load_users()
            else:
                messagebox.showerror("Error", "Cannot delete user: linked records found or error occurred.")
        except Exception as e:
            messagebox.showerror("Error", f"Error deleting user: {e}")

    def export_users_to_csv(self):
        users = db.get_all_users()
        if not users:
            messagebox.showinfo("Info", "No users to export")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".csv",
                                                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not filepath:
            return
        try:
            with open(filepath, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["ID", "Username", "Role", "Full Name", "Phone", "Email", "Active", "Created"])
                for u in users:
                    writer.writerow([
                        u['user_id'],
                        u['username'],
                        u['role'],
                        u['full_name'],
                        u['phone'],
                        u['email'],
                        "Yes" if u['is_active'] else "No",
                        u['created_at'].strftime('%Y-%m-%d') if u['created_at'] else ""
                    ])
            messagebox.showinfo("Success", f"Users exported to {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export users: {e}")

    def load_users(self):
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)

        users = db.get_all_users()

        filter_val = self.active_filter.get()
        if filter_val == "Active":
            users = [u for u in users if u['is_active']]
        elif filter_val == "Inactive":
            users = [u for u in users if not u['is_active']]

        # Role filter
        role_filter = getattr(self, 'role_filter', None)
        if role_filter:
            selected_role = self.role_filter.get()
            if selected_role != "All":
                users = [u for u in users if u['role'] == selected_role]

        for user in users:
            values = (
                user['user_id'],
                user['username'],
                user['role'],
                user['full_name'],
                user['phone'],
                user['email'],
                "Yes" if user['is_active'] else "No",
                user['created_at'].strftime('%Y-%m-%d') if user['created_at'] else ""
            )
            # Apply role tag to row for coloring
            self.users_tree.insert("", "end", values=values, tags=(user['role'],))

    def show_user_form(self, user_data=None):
        """Show user add/edit form"""
        form_window = ctk.CTkToplevel(self)
        form_window.title("Add User" if user_data is None else "Edit User")
        form_window.geometry("400x500")
        form_window.transient(self)
        form_window.grab_set()

        # Form fields
        form_frame = ctk.CTkFrame(form_window)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # User ID
        ctk.CTkLabel(
            form_frame,
            text="User ID:"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=10,
            pady=5
        )

        user_id_entry = ctk.CTkEntry(
            form_frame,
            width=250
        )
        user_id_entry.grid(
            row=0,
            column=1,
            padx=10,
            pady=5
        )
        user_id_entry.configure(state="readonly")

        # Username
        ctk.CTkLabel(form_frame, text="Username:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        username_entry = ctk.CTkEntry(form_frame, width=250)
        username_entry.grid(row=1, column=1, padx=10, pady=5)

        # Full Name
        ctk.CTkLabel(form_frame, text="Full Name:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        fullname_entry = ctk.CTkEntry(form_frame, width=250)
        fullname_entry.grid(row=2, column=1, padx=10, pady=5)

        # Role
        ctk.CTkLabel(form_frame, text="Role:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        role_combo = ctk.CTkComboBox(form_frame, values=USER_ROLES, width=250)
        role_combo.grid(row=3, column=1, padx=10, pady=5)

        # Suppliers single-select combo below Role (hidden by default)
        supplier_label = ctk.CTkLabel(form_frame, text="Supplier:")
        supplier_label.grid(row=4, column=0, sticky="w", padx=10, pady=5)
        supplier_label.grid_remove()

        suppliers = db.get_all_suppliers()
        supplier_names = [s['name'] for s in suppliers]
        supplier_combo = ctk.CTkComboBox(form_frame, values=supplier_names, width=250)
        supplier_combo.grid(row=4, column=1, padx=10, pady=5)
        supplier_combo.grid_remove()

        def toggle_supplier_combo(event=None):
            if role_combo.get() == 'Supplier':
                supplier_label.grid()
                supplier_combo.grid()
            else:
                supplier_label.grid_remove()
                supplier_combo.grid_remove()

        role_combo.configure(command=lambda value=None: toggle_supplier_combo())

        # Phone (now moved down one row)
        ctk.CTkLabel(form_frame, text="Phone:").grid(row=5, column=0, sticky="w", padx=10, pady=5)
        phone_entry = ctk.CTkEntry(form_frame, width=250)
        phone_entry.grid(row=5, column=1, padx=10, pady=5)

        # Email (moved down one row)
        ctk.CTkLabel(form_frame, text="Email:").grid(row=6, column=0, sticky="w", padx=10, pady=5)
        email_entry = ctk.CTkEntry(form_frame, width=250)
        email_entry.grid(row=6, column=1, padx=10, pady=5)

        # Password (only for new users)
        if user_data is None:
            ctk.CTkLabel(form_frame, text="Password:").grid(row=7, column=0, sticky="w", padx=10, pady=5)
            password_entry = ctk.CTkEntry(form_frame, width=250, show="*")
            password_entry.grid(row=7, column=1, padx=10, pady=5)

        # Active status
        active_var = ctk.BooleanVar(value=True)
        active_checkbox = ctk.CTkCheckBox(form_frame, text="Active", variable=active_var)
        active_checkbox.grid(row=8, column=1, sticky="w", padx=10, pady=5)
        # User ID
        if user_data is None:
            # Add mode
            user_id_entry.configure(state="normal")
            user_id_entry.delete(0, "end")
            user_id_entry.insert(
                0,
                str(db.get_next_user_id())
            )
            user_id_entry.configure(state="readonly")

        else:
            # Edit mode
            user_id_entry.configure(state="normal")
            user_id_entry.delete(0, "end")
            user_id_entry.insert(
                0,
                str(user_data[0])  # User ID
            )
            user_id_entry.configure(state="readonly")
        # Fill form if editing
        if user_data:
            username_entry.insert(0, user_data[1])
            username_entry.configure(state="disabled")  # Don't allow username change
            fullname_entry.insert(0, user_data[3])
            role_combo.set(user_data[2])
            toggle_supplier_combo()
            phone_entry.insert(0, user_data[4])
            email_entry.insert(0, user_data[5])
            active_var.set(user_data[6] == "Yes")

        # Buttons
        button_frame = ctk.CTkFrame(form_frame)
        button_frame.grid(row=9, column=0, columnspan=2, pady=20)

        def save_user():
            username = username_entry.get().strip()
            fullname = fullname_entry.get().strip()
            role = role_combo.get()
            phone = phone_entry.get().strip()
            email = email_entry.get().strip()

            if not all([username, fullname, role, email]):
                messagebox.showerror("Error", "Please fill all required fields")
                return
            # Phone validation (10 digits, numeric)
            if not re.fullmatch(r"\d{10}", phone):
                messagebox.showerror("Error", "Phone must be exactly 10 digits")
                return

            # Email format validation
            if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email):
                messagebox.showerror("Error", "Invalid email format")
                return

            # Uniqueness validation
            all_users = db.get_all_users()
            for u in all_users:
                # Exclude current user when editing
                if user_data is None or u['user_id'] != user_data[0]:
                    if u['username'].lower() == username.lower():
                        messagebox.showerror("Error", "Username already exists")
                        return
                    if u['email'].lower() == email.lower():
                        messagebox.showerror("Error", "Email already exists")
                        return

            try:
                if user_data is None:
                    # Add new user
                    password = password_entry.get().strip()
                    if not password:
                        messagebox.showerror("Error", "Password is required")
                        return
                    valid, msg = validate_password(password)
                    if not valid:
                        messagebox.showerror("Error", msg)
                        return

                    new_user_id = auth.create_user(username, password, role, fullname, phone, email)
                    if new_user_id:
                        if role == 'Supplier':
                            selected_supplier_name = supplier_combo.get()
                            supplier_obj = next((s for s in suppliers if s['name'] == selected_supplier_name), None)
                            if supplier_obj:
                                db.remove_suppliers_for_user(new_user_id)  # optional but safe
                                db.assign_supplier_to_user(new_user_id, supplier_obj['supplier_id'])
                        messagebox.showinfo("Success", "User created successfully")
                    else:
                        messagebox.showerror("Error", "Failed to create user")

                else:
                    # Update existing user
                    user_id = user_data[0]
                    is_active = active_var.get()
                    success = db.update_user(user_id, user_data[1], role, fullname, phone, email, is_active)
                    if success:
                        # Handle supplier-user linkage
                        if role == 'Supplier':
                            selected_supplier_name = supplier_combo.get()
                            supplier_obj = next((s for s in suppliers if s['name'] == selected_supplier_name), None)
                            if supplier_obj:
                                # Remove existing associations before adding new
                                db.remove_suppliers_for_user(user_id)
                                db.assign_supplier_to_user(user_id, supplier_obj['supplier_id'])
                        else:
                            # If role is not Supplier, remove association if any
                            db.remove_suppliers_for_user(user_id)

                        messagebox.showinfo("Success", "User updated successfully")
                    else:
                        messagebox.showerror("Error", "Failed to update user")

                form_window.destroy()
                self.load_users()

            except Exception as e:
                messagebox.showerror("Error", f"Error saving user: {e}")

        save_btn = ctk.CTkButton(
            button_frame,
            text="Save",
            command=save_user,
            width=100
        )
        save_btn.pack(side="left", padx=10, pady=10)

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=form_window.destroy,
            width=80
        )
        cancel_btn.pack(side="left", padx=(5, 10), pady=10)

    def add_user(self):
        """Show add user form"""
        self.show_user_form()

    def search_users(self):
        query = self.search_entry.get().lower()
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        users = db.get_all_users()
        filtered_users = [u for u in users if query in u['username'].lower() or query in u['full_name'].lower()]
        for user in filtered_users:
            tag = user['role']
            values = (
                user['user_id'],
                user['username'],
                user['role'],
                user['full_name'],
                user['phone'],
                user['email'],
                "Yes" if user['is_active'] else "No",
                user['created_at'].strftime('%Y-%m-%d') if user['created_at'] else ""
            )
            self.users_tree.insert("", "end", values=values, tags=(tag,))

    def edit_user(self):
        """Edit selected user"""
        selection = self.users_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a user to edit")
            return



        user_data = self.users_tree.item(selection[0])['values']
        self.show_user_form(user_data)

    def reset_password(self):
        selection = self.users_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a user to reset password")
            return

        user_data = self.users_tree.item(selection[0])['values']
        username = user_data[1]

        while True:
            new_password = ctk.CTkInputDialog(
                text=f"Enter new password for {username}:",
                title="Reset Password"
            ).get_input()

            if new_password is None:
                # User cancelled input dialog
                break

            valid, msg = validate_password(new_password)

            if not valid:
                messagebox.showerror("Error", msg)
                # Loop continues, allowing re-entry

            else:
                user_id = user_data[0]
                if auth.update_password(user_id, new_password):
                    messagebox.showinfo("Success", f"Password reset for {username}")
                else:
                    messagebox.showerror("Error", "Failed to reset password")
                break  # Exit loop after success or failure update

    def toggle_user_active(self):
        """Toggle user active status"""
        selection = self.users_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a user to toggle status")
            return

        # Get the selected user's values
        user_data = self.users_tree.item(selection[0])['values']
        user_id = user_data[0]
        current_status = user_data[6]  # 'Yes' or 'No' in "Active" column

        # Convert to boolean and toggle
        is_active = current_status == "Yes"
        new_status = not is_active

        try:
            # Update in DB using the existing update_user function or create a toggle-specific function
            # We need to pass all required fields for update_user:
            success = db.update_user(
                user_id,
                user_data[1],  # username (unchanged)
                user_data[2],  # role
                user_data[3],  # full_name
                user_data[4],  # phone
                user_data[5],  # email
                new_status  # new is_active value
            )

            if success:
                messagebox.showinfo(
                    "Success",
                    f"User {'activated' if new_status else 'deactivated'} successfully"
                )
                self.load_users()
            else:
                messagebox.showerror("Error", "Failed to update user status")
        except Exception as e:
            messagebox.showerror("Error", f"Error toggling user status: {e}")
