
import customtkinter as ctk
import sys
import os
from login_frame import LoginFrame
from admin_dashboard import AdminDashboard
from employee_dashboard import EmployeeDashboard
from supplier_dashboard import SupplierDashboard
from products_frame import ProductsFrame
from categories_frame import CategoriesFrame
from suppliers_frame import SuppliersFrame
from sales_frame import SalesFrame
from billing_frame import BillingFrame
from purchase_orders_frame import PurchaseOrdersFrame
from users_frame import UsersFrame
from settings_frame import SettingsFrame
from db import initialize_database,get_suppliers_for_user
import auth

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class InventoryApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        import config  # config module with load_user_settings

        # Load saved theme and scaling from settings file
        user_settings = config.load_user_settings()
        saved_theme = user_settings.get("theme", "dark")
        saved_scaling = user_settings.get("scaling", "100%")

        # Apply the saved theme and scaling immediately on program start
        ctk.set_appearance_mode(saved_theme)
        try:
            scale_val = int(saved_scaling.replace("%", "")) / 100
            ctk.set_widget_scaling(scale_val)
        except Exception:
            pass

        # Configure window
        self.title("Inventory Management System")
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"{screen_width}x{screen_height}+0+0")

        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Initialize database
        initialize_database()

        # Track current user and frame
        self.current_user = None
        self.current_frame = None

        # invoice being edited
        self.edit_sale_id = None

        # Create frames dictionary
        self.frames = {}

        self.nav_buttons = {}

        # Start with login frame
        self.show_login()

    def show_login(self):
        """Show the login frame"""
        # Clear any existing frame
        if self.current_frame:
            self.current_frame.destroy()

        # Create and show login frame
        self.current_frame = LoginFrame(self, self.on_login_success)
        self.current_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

    def on_login_success(self, user_data):
        """Handle successful login"""
        self.current_user = user_data

        suppliers = get_suppliers_for_user(user_data['user_id'])
        self.current_supplier_ids = [s['supplier_id'] for s in suppliers]

        # Clear login frame
        if self.current_frame:
            self.current_frame.destroy()

        # Create sidebar
        self.create_sidebar()

        # Show appropriate dashboard based on role
        if user_data['role'] == 'Admin':
            self.show_frame(AdminDashboard)
        elif user_data['role'] == 'Employee':
            self.show_frame(EmployeeDashboard)
        elif user_data['role'] == 'Supplier':
            self.show_frame(SupplierDashboard)

    def create_sidebar(self):
        """Create navigation sidebar"""
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(20, weight=1)

        # Logo/Title
        self.logo_label = ctk.CTkLabel(
            self.sidebar, 
            text="Inventory\nManagement", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=20)

        # Navigation buttons based on user role
        self.create_navigation_buttons()

        # User info and logout at bottom
        self.create_user_section()

    def create_navigation_buttons(self):
        """Create navigation buttons based on user role"""
        row = 1

        # Dashboard button (all roles)
        if self.current_user['role'] == 'Admin':
            btn = ctk.CTkButton(self.sidebar, text="Dashboard", 
                              command=lambda: self.show_frame(AdminDashboard))
            self.nav_buttons[AdminDashboard] = btn
        elif self.current_user['role'] == 'Employee':
            btn = ctk.CTkButton(self.sidebar, text="Dashboard", 
                              command=lambda: self.show_frame(EmployeeDashboard))
            self.nav_buttons[EmployeeDashboard] = btn
        else:
            btn = ctk.CTkButton(self.sidebar, text="Dashboard", 
                              command=lambda: self.show_frame(SupplierDashboard))

            self.nav_buttons[SupplierDashboard] = btn
        btn.grid(row=row, column=0, padx=20, pady=10, sticky="ew")
        row += 1

        # Role-specific navigation buttons
        if self.current_user['role'] == 'Admin':
            buttons = [
                ("Products", ProductsFrame),
                ("Categories", CategoriesFrame),
                ("Suppliers", SuppliersFrame),
                ("Sales", SalesFrame),
                ("Purchase Orders", PurchaseOrdersFrame),
                ("Users", UsersFrame),
                ("Settings", SettingsFrame)
            ]
        elif self.current_user['role'] == 'Employee':
            buttons = [
                ("Products", ProductsFrame),
                ("Billing", BillingFrame),
                ("Sales", SalesFrame),
                ("Settings", SettingsFrame)
            ]
        else:  # Supplier
            buttons = [
                ("Purchase Orders", PurchaseOrdersFrame),
                ("Settings", SettingsFrame)
            ]

        for text, frame_class in buttons:
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                command=lambda f=frame_class: self.show_frame(f)
            )

            btn.grid(
                row=row,
                column=0,
                padx=20,
                pady=10,
                sticky="ew"
            )

            self.nav_buttons[frame_class] = btn

            row += 1


    def create_user_section(self):
        """Create user info and logout section"""
        # User info
        user_frame = ctk.CTkFrame(self.sidebar)
        user_frame.grid(row=21, column=0, padx=20, pady=10, sticky="ew")

        user_label = ctk.CTkLabel(
            user_frame, 
            text=f"Welcome,\n{self.current_user['full_name']}", 
            font=ctk.CTkFont(size=12)
        )
        user_label.pack(pady=10)

        # Logout button
        logout_btn = ctk.CTkButton(
            user_frame, 
            text="Logout", 
            command=self.logout,
            fg_color="red",
            hover_color="darkred"
        )
        logout_btn.pack(pady=(0, 10))

    def highlight_active_button(self, active_frame):
        """
        Highlight currently selected sidebar button
        """

        normal_color = ("#3B8ED0", "#1F6AA5")
        active_color = ("#2FA572", "#106A43")

        for frame_class, button in self.nav_buttons.items():

            if frame_class == active_frame:
                button.configure(
                    fg_color=active_color,
                    hover_color=active_color
                )
            else:
                button.configure(
                    fg_color=normal_color
                )

    def show_frame(self, frame_class):

        if self.current_frame:
            self.current_frame.destroy()

        if frame_class in (
                SupplierDashboard,
                PurchaseOrdersFrame
        ):
            self.current_frame = frame_class(
                self,
                self.current_supplier_ids
            )
        else:
            self.current_frame = frame_class(self)

        self.current_frame.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=10,
            pady=10
        )

        self.highlight_active_button(frame_class)

    def logout(self):
        """Handle logout"""
        self.current_user = None

        # Destroy sidebar
        if hasattr(self, 'sidebar'):
            self.sidebar.destroy()

        # Show login
        self.show_login()

if __name__ == "__main__":
    app = InventoryApp()
    app.mainloop()
