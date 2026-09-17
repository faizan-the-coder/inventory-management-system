
import customtkinter as ctk
import tkinter.messagebox as messagebox
import db
from purchase_orders_frame import PurchaseOrdersFrame
from settings_frame import SettingsFrame

class SupplierDashboard(ctk.CTkFrame):
    def __init__(self, parent,supplier_ids):
        super().__init__(parent)
        self.parent = parent
        self.supplier_ids = supplier_ids

        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        self.create_widgets()
        self.update_dashboard()

    def create_widgets(self):
        """Create dashboard widgets"""
        # Title
        self.title_label = ctk.CTkLabel(
            self,
            text="Supplier Dashboard",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        self.title_label.grid(row=0, column=0, columnspan=2, padx=20, pady=20)

        # Statistics cards
        self.create_stats_cards()

        # Quick actions
        self.create_quick_actions()

        # Recent purchase orders
        self.create_recent_pos()

    def create_stats_cards(self):
        """Create statistics cards"""
        # Pending POs
        self.pending_card = ctk.CTkFrame(self)
        self.pending_card.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.pending_title = ctk.CTkLabel(
            self.pending_card,
            text="Pending Orders",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.pending_title.pack(pady=(20, 5))

        self.pending_count = ctk.CTkLabel(
            self.pending_card,
            text="0",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="orange"
        )
        self.pending_count.pack(pady=(0, 20))

        # Completed POs
        self.completed_card = ctk.CTkFrame(self)
        self.completed_card.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        self.completed_title = ctk.CTkLabel(
            self.completed_card,
            text="Completed Orders",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.completed_title.pack(pady=(20, 5))

        self.completed_count = ctk.CTkLabel(
            self.completed_card,
            text="0",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="green"
        )
        self.completed_count.pack(pady=(0, 20))

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
            ("View Orders", self.view_orders),
            ("Update Profile", self.update_profile),
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

        self.buttons_frame.grid_columnconfigure((0, 1, 2), weight=1)

    def create_recent_pos(self):
        """Create recent purchase orders section"""
        self.recent_frame = ctk.CTkFrame(self)
        self.recent_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.recent_title = ctk.CTkLabel(
            self.recent_frame,
            text="Recent Purchase Orders",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.recent_title.pack(pady=(10, 5))

        # Scrollable frame for recent POs
        self.recent_scroll = ctk.CTkScrollableFrame(self.recent_frame, height=200)
        self.recent_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def update_dashboard(self):
        try:
            purchase_orders = db.get_purchase_orders_for_suppliers(self.supplier_ids)

            # Separate pending and completed orders
            pending_pos = [po for po in purchase_orders if po['status'] == 'Ordered']
            completed_pos = [po for po in purchase_orders if po['status'] == 'Received']

            self.pending_count.configure(text=str(len(pending_pos)))
            self.completed_count.configure(text=str(len(completed_pos)))

            # Show latest 5 purchase orders sorted by created date descending
            sorted_pos = sorted(purchase_orders, key=lambda x: x['created_at'], reverse=True)
            self.update_recent_pos(sorted_pos[:5])

        except Exception as e:
            print(f"Error updating dashboard: {e}")

    def update_recent_pos(self, purchase_orders):
        # Clear previous entries
        for widget in self.recent_scroll.winfo_children():
            widget.destroy()

        if not purchase_orders:
            label = ctk.CTkLabel(self.recent_scroll, text="No recent purchase orders found.")
            label.pack(pady=10)
            return

        for po in purchase_orders:
            # Fetch item count for PO
            items = db.get_purchase_items(po['po_id'])
            item_count = len(items) if items else 0
            po_text = f"PO #{po['po_id']} | Status: {po['status']} | Items: {item_count} | Created: {po['created_at'].strftime('%Y-%m-%d')} | Expected: {po['expected_date'].strftime('%Y-%m-%d') if po['expected_date'] else 'N/A'} | Total: ₹{po['total_amount']:,.2f}"
            po_frame = ctk.CTkFrame(self.recent_scroll)
            po_frame.pack(fill='x', pady=2, padx=5)

            po_label = ctk.CTkLabel(po_frame, text=po_text, anchor='w')
            po_label.pack(fill='x', padx=10, pady=5)

    def view_orders(self):
        # Navigate to PurchaseOrders frame
        if hasattr(self.parent, 'show_frame'):
            self.parent.show_frame(PurchaseOrdersFrame)
        else:
            messagebox.showinfo("Info", "Cannot navigate to Orders view.")

    def update_profile(self):
        if hasattr(self.parent, 'show_frame'):
            self.parent.show_frame(SettingsFrame)
        else:
            messagebox.showinfo("Info", "Cannot navigate to Settings.")

