
import customtkinter as ctk
import tkinter.messagebox as messagebox
import db
from datetime import datetime, timedelta

from products_frame import ProductsFrame
from categories_frame import CategoriesFrame
from suppliers_frame import SuppliersFrame
from sales_frame import SalesFrame
from purchase_orders_frame import PurchaseOrdersFrame


class AdminDashboard(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.grid_columnconfigure((0, 1, 2), weight=1)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        self.create_widgets()
        self.update_dashboard()

    def create_widgets(self):
        """Create dashboard widgets"""
        # Title
        self.title_label = ctk.CTkLabel(
            self,
            text="Admin Dashboard",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        self.title_label.grid(row=0, column=0, columnspan=3, padx=20, pady=20)

        # Statistics cards
        self.create_stats_cards()

        # Recent activity and low stock alerts
        self.create_activity_section()

        # Quick actions
        self.create_quick_actions()

    def create_stats_cards(self):
        """Create statistics cards"""
        # Total Products
        self.products_card = ctk.CTkFrame(self)
        self.products_card.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.products_title = ctk.CTkLabel(
            self.products_card,
            text="Total Products",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.products_title.pack(pady=(20, 5))

        self.products_count = ctk.CTkLabel(
            self.products_card,
            text="0",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color="green"
        )
        self.products_count.pack(pady=(0, 20))

        # Total Categories
        self.categories_card = ctk.CTkFrame(self)
        self.categories_card.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        self.categories_title = ctk.CTkLabel(
            self.categories_card,
            text="Total Categories",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.categories_title.pack(pady=(20, 5))

        self.categories_count = ctk.CTkLabel(
            self.categories_card,
            text="0",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color="blue"
        )
        self.categories_count.pack(pady=(0, 20))

        # Total Suppliers
        self.suppliers_card = ctk.CTkFrame(self)
        self.suppliers_card.grid(row=1, column=2, padx=10, pady=10, sticky="nsew")

        self.suppliers_title = ctk.CTkLabel(
            self.suppliers_card,
            text="Total Suppliers",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.suppliers_title.pack(pady=(20, 5))

        self.suppliers_count = ctk.CTkLabel(
            self.suppliers_card,
            text="0",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color="orange"
        )
        self.suppliers_count.pack(pady=(0, 20))

    def create_activity_section(self):
        """Create activity and alerts section"""
        # Low Stock Alerts
        self.alerts_frame = ctk.CTkFrame(self)
        self.alerts_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.alerts_title = ctk.CTkLabel(
            self.alerts_frame,
            text="Low Stock Alerts",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.alerts_title.pack(pady=(10, 5))

        # Scrollable frame for alerts
        self.alerts_scroll = ctk.CTkScrollableFrame(self.alerts_frame)
        self.alerts_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Recent Sales Summary
        self.sales_frame = ctk.CTkFrame(self)
        self.sales_frame.grid(row=2, column=2, padx=10, pady=10, sticky="nsew")

        self.sales_title = ctk.CTkLabel(
            self.sales_frame,
            text="Today's Sales",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.sales_title.pack(pady=(10, 5))

        self.sales_amount = ctk.CTkLabel(
            self.sales_frame,
            text="₹0.00",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="green"
        )
        self.sales_amount.pack(pady=10)

        self.sales_count = ctk.CTkLabel(
            self.sales_frame,
            text="0 transactions",
            font=ctk.CTkFont(size=14)
        )
        self.sales_count.pack(pady=(0, 20))

    def create_quick_actions(self):
        """Create quick action buttons"""
        self.actions_frame = ctk.CTkFrame(self)
        self.actions_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky="ew")

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
            ("Add Product", self.add_product),
            ("Add Category", self.add_category),
            ("Add Supplier", self.add_supplier),
            ("View Sales", self.view_sales),
            ("Create PO", self.create_po),
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

        self.buttons_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

    def update_dashboard(self):
        """Update dashboard statistics"""
        try:
            # Get product count
            products = db.get_all_products()
            self.products_count.configure(text=str(len(products)))

            # Get category count
            categories = db.get_all_categories()
            self.categories_count.configure(text=str(len(categories)))

            # Get supplier count
            suppliers = db.get_all_suppliers()
            self.suppliers_count.configure(text=str(len(suppliers)))

            # Update low stock alerts
            self.update_low_stock_alerts()

            # Update sales summary
            self.update_sales_summary()

        except Exception as e:
            print(f"Error updating dashboard: {e}")

    def update_low_stock_alerts(self):
        """Update low stock alerts"""
        # Clear existing alerts
        for widget in self.alerts_scroll.winfo_children():
            widget.destroy()

        low_stock_products = db.get_low_stock_products()

        if not low_stock_products:
            no_alerts = ctk.CTkLabel(
                self.alerts_scroll,
                text="No low stock alerts",
                font=ctk.CTkFont(size=14),
                text_color="green"
            )
            no_alerts.pack(pady=10)
        else:
            for product in low_stock_products:
                alert_frame = ctk.CTkFrame(self.alerts_scroll)
                alert_frame.pack(fill="x", padx=5, pady=2)

                alert_text = f"{product['name']} - Stock: {product['stock_qty']} (Reorder: {product['reorder_level']})"
                alert_label = ctk.CTkLabel(
                    alert_frame,
                    text=alert_text,
                    font=ctk.CTkFont(size=12),
                    text_color="red"
                )
                alert_label.pack(pady=5)

    def update_sales_summary(self):
        """Update today's sales summary"""
        try:
            today = datetime.now().date()
            sales = db.get_sales_history(today, today)

            total_amount = sum(sale['total'] for sale in sales)
            transaction_count = len(sales)

            self.sales_amount.configure(text=f"₹{total_amount:,.2f}")
            self.sales_count.configure(text=f"{transaction_count} transactions")

        except Exception as e:
            print(f"Error updating sales summary: {e}")

    def add_product(self):
        self.parent.show_frame(ProductsFrame)

    def add_category(self):
        self.parent.show_frame(CategoriesFrame)

    def add_supplier(self):
        self.parent.show_frame(SuppliersFrame)

    def view_sales(self):
        self.parent.show_frame(SalesFrame)

    def create_po(self):
        self.parent.show_frame(PurchaseOrdersFrame)
