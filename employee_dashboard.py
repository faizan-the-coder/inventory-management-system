
import customtkinter as ctk
import tkinter.messagebox as messagebox
import db
from datetime import datetime
from billing_frame import BillingFrame
from products_frame import ProductsFrame
from sales_frame import SalesFrame

class EmployeeDashboard(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.app = self.master
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        self.create_widgets()
        self.update_dashboard()

    def create_widgets(self):
        """Create dashboard widgets"""
        # Title
        self.title_label = ctk.CTkLabel(
            self,
            text="Employee Dashboard",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        self.title_label.grid(row=0, column=0, columnspan=2, padx=20, pady=20)

        # Statistics cards
        self.create_stats_cards()

        # Quick actions
        self.create_quick_actions()

        # Recent sales
        self.create_recent_sales()

    def create_stats_cards(self):
        """Create statistics cards"""
        # Today's Sales
        self.sales_card = ctk.CTkFrame(self)
        self.sales_card.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.sales_title = ctk.CTkLabel(
            self.sales_card,
            text="Today's Sales",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.sales_title.pack(pady=(20, 5))

        self.sales_amount = ctk.CTkLabel(
            self.sales_card,
            text="₹0.00",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="green"
        )
        self.sales_amount.pack(pady=(0, 10))

        self.sales_count = ctk.CTkLabel(
            self.sales_card,
            text="0 transactions",
            font=ctk.CTkFont(size=14)
        )
        self.sales_count.pack(pady=(0, 20))

        # Product Count
        self.products_card = ctk.CTkFrame(self)
        self.products_card.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        self.products_title = ctk.CTkLabel(
            self.products_card,
            text="Available Products",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.products_title.pack(pady=(20, 5))

        self.products_count = ctk.CTkLabel(
            self.products_card,
            text="0",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="blue"
        )
        self.products_count.pack(pady=(0, 20))

    def create_quick_actions(self):
        """Create quick action buttons"""
        self.actions_frame = ctk.CTkFrame(self)
        self.actions_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self.actions_title = ctk.CTkLabel(
            self.actions_frame,
            text="Quick Actions",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.actions_title.pack(pady=(10, 5))

        # Button frame
        self.buttons_frame = ctk.CTkFrame(self.actions_frame)
        self.buttons_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Quick action buttons
        actions = [
            ("New Sale", self.new_sale),
            ("View Products", self.view_products),
            ("Sales History", self.view_sales),
            ("Refresh", self.update_dashboard)
        ]

        for i, (text, command) in enumerate(actions):
            btn = ctk.CTkButton(
                self.buttons_frame,
                text=text,
                command=command,
                width=150
            )
            btn.grid(row=0, column=i, padx=5, pady=10)

        self.buttons_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

    def create_recent_sales(self):
        """Create recent sales section"""
        self.recent_frame = ctk.CTkFrame(self)
        self.recent_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.recent_title = ctk.CTkLabel(
            self.recent_frame,
            text="Recent Sales",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.recent_title.pack(pady=(10, 5))

        # Scrollable frame for recent sales
        self.recent_scroll = ctk.CTkScrollableFrame(self.recent_frame, height=200)
        self.recent_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def update_dashboard(self):
        """Update dashboard statistics"""
        try:
            # Get today's sales
            today = datetime.now().date()
            sales = db.get_sales_history(today, today)

            total_amount = sum(sale['total'] for sale in sales)
            transaction_count = len(sales)

            self.sales_amount.configure(text=f"₹{total_amount:,.2f}")
            self.sales_count.configure(text=f"{transaction_count} transactions")

            # Get product count
            products = db.get_all_products()
            self.products_count.configure(text=str(len(products)))

            # Update recent sales
            self.update_recent_sales(sales[:5])  # Show last 5 sales

        except Exception as e:
            print(f"Error updating dashboard: {e}")

    def update_recent_sales(self, sales):
        for widget in self.recent_scroll.winfo_children():
            widget.destroy()

        if not sales:
            no_sales = ctk.CTkLabel(self.recent_scroll, text="No sales today", font=ctk.CTkFont(size=14),
                                    text_color="gray")
            no_sales.pack(pady=10)
        else:
            for sale in sales:
                sale_frame = ctk.CTkFrame(self.recent_scroll)
                sale_frame.pack(fill="x", padx=5, pady=2)
                sale_text = (f"Sale #{sale['sale_id']} - ₹{sale['total']:,.2f} - "
                             f"{sale.get('items_count', 0)} items - "
                             f"Cashier: {sale['employee_name']} - "
                             f"{sale['datetime'].strftime('%Y-%m-%d %H:%M:%S')}")
                sale_label = ctk.CTkLabel(sale_frame, text=sale_text, font=ctk.CTkFont(size=12))
                sale_label.pack(pady=5)
                # Optional: binding for details
                # sale_label.bind("<Button-1>", lambda e, sid=sale['sale_id']: self.show_sale_details(sid))

    def new_sale(self):
        self.app.show_frame(BillingFrame)

    def view_products(self):
        self.app.show_frame(ProductsFrame)

    def view_sales(self):
        self.app.show_frame(SalesFrame)