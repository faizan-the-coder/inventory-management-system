
import customtkinter as ctk
import tkinter.messagebox as messagebox
import tkinter.ttk as ttk
from tkinter import filedialog
import db
from datetime import datetime
from config import APP_SETTINGS
from decimal import Decimal
import invoice_pdf
import re
from tkinter import simpledialog
import auth
import os
import threading

class BillingFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.product_data_dict = {}

        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Cart items
        self.cart_items = []
        self.tax_rate = APP_SETTINGS['tax_rate']

        # Edit invoice mode
        self.edit_mode = False
        self.edit_sale_id = None

        self.create_widgets()

        if hasattr(self.parent, "edit_sale_id") and self.parent.edit_sale_id:
            self.load_sale_for_edit(
                self.parent.edit_sale_id
            )

            self.parent.edit_sale_id = None

    def create_widgets(self):
        """Create billing/POS widgets"""
        # Title
        # self.title_label = ctk.CTkLabel(
        #     self,
        #     text="Point of Sale - Billing",
        #     font=ctk.CTkFont(size=24, weight="bold")
        # )
        # self.title_label.grid(row=0, column=0, columnspan=2, padx=20, pady=10)

        self.create_customer_info_section()

        # Left side - Product search and selection
        self.create_product_section()


        # Right side - Cart and billing
        self.create_cart_section()

    def load_sale_for_edit(self, sale_id):
        """
        Load existing invoice into cart for editing
        """
        self.clear_cart()
        self.original_sale_items = {}

        self.edit_mode = True
        self.edit_sale_id = sale_id

        self.refresh_sale_id()

        # Load customer information
        sale = db.get_sale(sale_id)

        if sale:
            self.customer_name_entry.delete(0, "end")
            self.customer_name_entry.insert(
                0,
                sale.get("customer_name", "")
            )

            self.customer_phone_entry.delete(0, "end")
            self.customer_phone_entry.insert(
                0,
                sale.get("customer_phone", "")
            )

            self.customer_email_entry.delete(0, "end")
            self.customer_email_entry.insert(
                0,
                sale.get("customer_email") or ""
            )

        # Load invoice items
        sale_items = db.get_sale_items(sale_id)

        self.cart_items = []

        for item in sale_items:
            self.original_sale_items[item["product_id"]] = item["qty"]
            product = db.get_product_by_id(item["product_id"])

            cart_item = {
                "product_id": item["product_id"],
                "name": item["product_name"],
                "unit_price": item["unit_price"],
                "cost_price": product["cost_price"],
                "qty": item["qty"],
                "line_total": item["line_total"]
            }

            self.cart_items.append(cart_item)

        self.update_cart_display()

        self.checkout_btn.configure(
            text=f"UPDATE INVOICE #{sale_id}",
            fg_color="orange"
        )

    def get_original_invoice_qty(self, product_id):

        if not self.edit_mode:
            return 0

        return self.original_sale_items.get(product_id, 0)

    def reset_edit_mode(self):
        self.edit_mode = False
        self.edit_sale_id = None

        self.checkout_btn.configure(
            text="CHECKOUT",
            fg_color="green"
        )
        self.refresh_sale_id()



    def create_product_section(self):
        """Create product search and selection section"""
        self.product_frame = ctk.CTkFrame(self)
        self.product_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.product_frame.grid_columnconfigure(0, weight=1)
        self.product_frame.grid_rowconfigure(1, weight=1)

        # Search section
        search_frame = ctk.CTkFrame(self.product_frame)
        search_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        ctk.CTkLabel(search_frame, text="Search Products:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))

        search_controls = ctk.CTkFrame(search_frame)
        search_controls.pack(fill="x", padx=10, pady=(0, 10))

        self.search_entry = ctk.CTkEntry(
            search_controls,
            placeholder_text="Enter name, SKU, or barcode...",
            width=200
        )
        self.search_entry.pack(side="left", padx=(0, 10), pady=10)
        self.search_entry.bind("<KeyRelease>", self.on_search)

        search_btn = ctk.CTkButton(
            search_controls,
            text="Search",
            command=self.search_products,
            width=80
        )
        search_btn.pack(side="left", padx=(0, 10), pady=10)

        clear_btn = ctk.CTkButton(
            search_controls,
            text="Clear",
            command=self.clear_search,
            width=60
        )
        clear_btn.pack(side="left", pady=10)

        # Products list
        self.create_products_list()


    def create_products_list(self):
        """Create products selection list"""
        # Products table
        products_table_frame = ctk.CTkFrame(self.product_frame)
        products_table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        products_table_frame.grid_rowconfigure(0, weight=1)
        products_table_frame.grid_columnconfigure(0, weight=1)

        columns = ("SKU", "Name", "Price", "Stock")
        self.products_tree = ttk.Treeview(products_table_frame, columns=columns, show="headings", height=12)

        # Configure columns
        column_widths = {"SKU": 80, "Name": 200, "Price": 80, "Stock": 60}
        for col in columns:
            self.products_tree.heading(col, text=col)
            self.products_tree.column(col, width=column_widths.get(col, 100), minwidth=50)

        # Scrollbar
        scrollbar = ttk.Scrollbar(products_table_frame, orient="vertical", command=self.products_tree.yview)
        self.products_tree.configure(yscrollcommand=scrollbar.set)

        self.products_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Add to cart button
        add_frame = ctk.CTkFrame(products_table_frame)
        add_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        self.qty_entry = ctk.CTkEntry(
            add_frame,
            placeholder_text="Qty",
            width=60
        )
        self.qty_entry.pack(side="left", padx=10, pady=10)

        add_btn = ctk.CTkButton(
            add_frame,
            text="Add to Cart",
            command=self.add_to_cart,
            width=100
        )
        add_btn.pack(side="left", padx=(5, 10), pady=10)

        # Load all products initially
        self.load_products()

        # Bind double-click to add to cart
        self.products_tree.bind("<Double-1>", lambda e: self.add_to_cart())

    def create_customer_info_section(self):
        self.customer_frame = ctk.CTkFrame(self, corner_radius=10)  # Use same bg color as others
        self.customer_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=10,
                                 pady=10)  # Fill horizontally with padding

        # Make columns expand equally to fill the wider space
        self.customer_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        # Section Title
        section_title = ctk.CTkLabel(
            self.customer_frame,
            text="Customer Information",
            font=ctk.CTkFont(size=18, weight="bold"),
            corner_radius=6,
            pady=10
        )
        section_title.grid(
            row=0,
            column=0,
            columnspan=6,
            sticky="ew"
        )

        # Sale ID Display
        self.sale_id_label = ctk.CTkLabel(
            self.customer_frame,
            text=f"Invoice #{db.get_next_sale_id()}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#22C55E"
        )
        self.sale_id_label.grid(
            row=0,
            column=5,
            sticky="e",
            padx=20
        )

        # Fields with expanded width and horizontal fill
        ctk.CTkLabel(self.customer_frame, text="Name:", font=ctk.CTkFont(size=14)).grid(row=1, column=0, sticky="e",
                                                                                        padx=(0, 10), pady=5)
        self.customer_name_entry = ctk.CTkEntry(self.customer_frame, placeholder_text="Full Name")
        self.customer_name_entry.grid(row=1, column=1, sticky="ew", pady=5)

        ctk.CTkLabel(self.customer_frame, text="Phone:", font=ctk.CTkFont(size=14)).grid(row=1, column=2, sticky="e",
                                                                                         padx=(20, 10), pady=5)
        self.customer_phone_entry = ctk.CTkEntry(self.customer_frame, placeholder_text="9876543210")
        self.customer_phone_entry.grid(row=1, column=3, sticky="ew", pady=5)

        ctk.CTkLabel(self.customer_frame, text="Email:", font=ctk.CTkFont(size=14)).grid(row=1, column=4, sticky="e",
                                                                                         padx=(20, 10), pady=5)
        self.customer_email_entry = ctk.CTkEntry(self.customer_frame, placeholder_text="email@example.com")
        self.customer_email_entry.grid(row=1, column=5, sticky="ew", pady=5,padx=(0,40))
        self.refresh_sale_id()

    def refresh_sale_id(self):
        if self.edit_mode and self.edit_sale_id:
            self.sale_id_label.configure(
                text=f"Invoice #{self.edit_sale_id}"
            )
        else:
            self.sale_id_label.configure(
                text=f"Invoice #{db.get_next_sale_id()}"
            )

    def create_cart_section(self):
        """Create cart and billing section"""
        self.cart_frame = ctk.CTkFrame(self)
        self.cart_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        self.cart_frame.grid_columnconfigure(0, weight=1)
        self.cart_frame.grid_rowconfigure(1, weight=1)

        # Cart title
        ctk.CTkLabel(
            self.cart_frame, 
            text="Shopping Cart", 
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, pady=(10, 5))

        # Cart items table
        self.create_cart_table()

        # Billing summary
        self.create_billing_summary()

        # Action buttons
        self.create_action_buttons()

    def create_cart_table(self):
        """Create cart items table"""
        cart_table_frame = ctk.CTkFrame(self.cart_frame)
        cart_table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        cart_table_frame.grid_rowconfigure(0, weight=1)
        cart_table_frame.grid_columnconfigure(0, weight=1)

        columns = ("Product", "Price", "Qty", "Total")
        self.cart_tree = ttk.Treeview(cart_table_frame, columns=columns, show="headings", height=10)

        # Configure columns
        column_widths = {"Product": 150, "Price": 60, "Qty": 50, "Total": 80}
        for col in columns:
            self.cart_tree.heading(col, text=col)
            self.cart_tree.column(col, width=column_widths.get(col, 100), minwidth=50)

        # Scrollbar
        cart_scrollbar = ttk.Scrollbar(cart_table_frame, orient="vertical", command=self.cart_tree.yview)
        self.cart_tree.configure(yscrollcommand=cart_scrollbar.set)

        self.cart_tree.grid(row=0, column=0, sticky="nsew")
        cart_scrollbar.grid(row=0, column=1, sticky="ns")

        # Cart actions
        cart_actions = ctk.CTkFrame(cart_table_frame)
        cart_actions.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        update_btn = ctk.CTkButton(
            cart_actions,
            text="Update Qty",
            command=self.update_cart_item,
            width=100
        )
        update_btn.pack(side="left", padx=10, pady=10)

        remove_btn = ctk.CTkButton(
            cart_actions,
            text="Remove",
            command=self.remove_from_cart,
            width=80,
            fg_color="red",
            hover_color="darkred"
        )
        remove_btn.pack(side="left", padx=(5, 10), pady=10)

        clear_cart_btn = ctk.CTkButton(
            cart_actions,
            text="Clear Cart",
            command=self.clear_cart,
            width=80
        )
        clear_cart_btn.pack(side="right", padx=10, pady=10)

    def calculate_profit(self):


        profit = 0
        for item in self.cart_items:
            item_profit = (item["unit_price"] - item["cost_price"]) * item["qty"]

            profit += item_profit

        return profit

    def create_billing_summary(self):
        """Create billing summary section"""
        summary_frame = ctk.CTkFrame(self.cart_frame)
        summary_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)

        # Subtotal
        subtotal_frame = ctk.CTkFrame(summary_frame)
        subtotal_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(subtotal_frame, text="Subtotal:", font=ctk.CTkFont(size=14)).pack(side="left", padx=10)
        self.subtotal_label = ctk.CTkLabel(subtotal_frame, text="₹0.00", font=ctk.CTkFont(size=14, weight="bold"))
        self.subtotal_label.pack(side="right", padx=10)

        # Tax
        tax_frame = ctk.CTkFrame(summary_frame)
        tax_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(tax_frame, text=f"Tax ({self.tax_rate*100:.0f}%):", font=ctk.CTkFont(size=14)).pack(side="left", padx=10)
        self.tax_label = ctk.CTkLabel(tax_frame, text="₹0.00", font=ctk.CTkFont(size=14, weight="bold"))
        self.tax_label.pack(side="right", padx=10)

        # Total
        total_frame = ctk.CTkFrame(summary_frame)
        total_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(total_frame, text="TOTAL:", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10)
        self.total_label = ctk.CTkLabel(
            total_frame, 
            text="₹0.00", 
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="green"
        )
        self.total_label.pack(side="right", padx=10)

        self.profit_label = ctk.CTkLabel(summary_frame, text="Profit: ₹0.00", font=ctk.CTkFont(size=14, weight="bold"))
        self.profit_label.pack(side="left", padx=10)

    def view_invoice(self):
        """Open the last PDF invoice in the system default PDF viewer."""
        import os, platform, subprocess
        pdf_path = getattr(self, "last_invoice_file", None)
        if not pdf_path or not os.path.isfile(pdf_path):
            messagebox.showerror("Error", "No invoice PDF found.")
            return

        try:
            if platform.system() == "Windows":
                os.startfile(pdf_path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", pdf_path])
            else:
                subprocess.run(["xdg-open", pdf_path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open PDF: {e}")

    def save_invoice(self):
        """Let user save/copy the invoice PDF to chosen location."""
        import shutil
        pdf_path = getattr(self, "last_invoice_file", None)
        if not pdf_path or not os.path.isfile(pdf_path):
            messagebox.showerror("Error", "No invoice PDF found.")
            return

        dest = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            title="Save Invoice As"
        )
        if dest:
            try:
                shutil.copy(pdf_path, dest)
                messagebox.showinfo("Success", f"Invoice saved to {dest}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save invoice: {e}")

    def email_invoice(self):
        """Send the invoice PDF as an email attachment asynchronously."""

        pdf_path = getattr(self, "last_invoice_file", None)
        sale_id = getattr(self, "last_sale_id", None)

        if not pdf_path or not os.path.isfile(pdf_path):
            messagebox.showerror("Error", "No invoice PDF found.")
            return

        email = self.customer_email_entry.get().strip()  # Get email from entry field
        customer_name = self.customer_name_entry.get().strip()
        if not email or not self.validate_email(email):
            messagebox.showerror("Invalid Email", "Please enter a valid email address to send the invoice.")
            return
        shop_info = db.get_shop_info()
        shop_name = shop_info.get("name", "Your Shop Name")  # Fallback to default if not set

        subject = f"Your Invoice #{sale_id} from {shop_name}"

        body = f"Dear {customer_name or 'customer'},\n\nPlease find attached your invoice.\nThanks for shopping with us!"

        self.email_invoice_btn.configure(state="disabled", text="Sending...")

        def _send_worker():
            sent = auth.send_email_with_attachment(email, subject, body, pdf_path)
            def _on_finish():
                self.email_invoice_btn.configure(state="normal", text="Email Invoice")
                if sent:
                    messagebox.showinfo("Success", f"Invoice sent to {email}")
                else:
                    messagebox.showerror("Failed", "Failed to send invoice email. Please check your SMTP configuration.")
            self.after(0, _on_finish)

        threading.Thread(target=_send_worker, daemon=True).start()

    def create_action_buttons(self):
        """Create action buttons for billing frame (CHECKOUT, VIEW, SAVE, EMAIL)"""
        actions_frame = ctk.CTkFrame(self.cart_frame)
        actions_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)

        # Additional buttons (initially disabled)
        self.view_invoice_btn = ctk.CTkButton(
            actions_frame,
            text="View Invoice",
            command=self.view_invoice,
            width=80,
            state="disabled"
        )
        self.view_invoice_btn.pack(side="left", padx=10, pady=10)

        self.save_invoice_btn = ctk.CTkButton(
            actions_frame,
            text="Save Invoice",
            command=self.save_invoice,
            width=80,
            state="disabled"
        )
        self.save_invoice_btn.pack(side="left", padx=10, pady=10)

        self.email_invoice_btn = ctk.CTkButton(
            actions_frame,
            text="Email Invoice",
            width=80,
            command=self.email_invoice,
            state="disabled"
        )
        self.email_invoice_btn.pack(side="left", padx=10, pady=10)

        # Checkout button
        self.checkout_btn = ctk.CTkButton(
            actions_frame,
            text="CHECKOUT",
            command=self.checkout,
            width=120,
            height=40,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="green",
            hover_color="darkgreen"
        )
        self.checkout_btn.pack(side="right", padx=10, pady=10)

    def load_products(self):
        """Load all products into products list"""
        # Clear existing data
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)

        # Load products
        products = db.get_all_products()

        for product in products:
            if product['is_active'] and product['stock_qty'] > 0:
                values = (
                    product['sku'],
                    product['name'],
                    f"₹{product['unit_price']:.2f}",
                    product['stock_qty']
                )

                item_id = self.products_tree.insert("", "end", values=values)

                # Store product dict associated with item_id
                self.product_data_dict[item_id] = product

    def search_products(self):
        """Search products"""
        search_term = self.search_entry.get().strip()

        # Clear existing data
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)

        if not search_term:
            self.load_products()
            return

        # Search and load results
        products = db.search_products(search_term)

        for product in products:
            if product['is_active'] and product['stock_qty'] > 0:
                values = (
                    product['sku'],
                    product['name'],
                    f"₹{product['unit_price']:.2f}",
                    product['stock_qty']
                )

                item_id = self.products_tree.insert("", "end", values=values)

                # Store product dict associated with item_id
                self.product_data_dict[item_id] = product

    def clear_search(self):
        """Clear search and reload all products"""
        self.search_entry.delete(0, 'end')
        self.load_products()

    def on_search(self, event):
        """Handle search as user types"""
        # Optional: implement real-time search after a delay
        pass

    def add_to_cart(self):
        """Add selected product to cart"""
        selection = self.products_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a product to add")
            return

        # Get quantity
        try:
            qty = int(self.qty_entry.get() or 1)
            if qty <= 0:
                messagebox.showerror("Error", "Quantity must be greater than 0")
                return
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid quantity")
            return

        # Get selected product
        item = selection[0]
        product_data = self.get_product_from_tree_item(item)

        if not product_data:
            messagebox.showerror("Error", "Product data not found")
            return

        # Check stock
        # Check stock

        available_stock = product_data['stock_qty']

        if self.edit_mode:
            available_stock += self.get_original_invoice_qty(
                product_data['product_id']
            )

        if qty > available_stock:
            messagebox.showerror(
                "Error",
                f"Insufficient stock. Available: {available_stock}"
            )
            return

        # Check if product already in cart
        for cart_item in self.cart_items:
            if cart_item['product_id'] == product_data['product_id']:
                # Update existing item
                new_qty = cart_item['qty'] + qty
                available_stock = product_data['stock_qty']

                if self.edit_mode:
                    available_stock += self.get_original_invoice_qty(
                        product_data['product_id']
                    )

                if new_qty > available_stock:
                    f"Total quantity would exceed stock. Available: {available_stock}"
                    return
                cart_item['qty'] = new_qty
                cart_item['line_total'] = cart_item['qty'] * cart_item['unit_price']
                break
        else:
            # Add new item
            cart_item = {
                'product_id': product_data['product_id'],
                'name': product_data['name'],
                'unit_price': product_data['unit_price'],
                "cost_price": product_data["cost_price"],
                'qty': qty,
                'line_total': qty * product_data['unit_price']
            }
            self.cart_items.append(cart_item)


        # Clear quantity entry
        self.qty_entry.delete(0, 'end')

        # Update cart display
        self.update_cart_display()

    def get_product_from_tree_item(self, item):
        # Fetch product dict from the dictionary
        return self.product_data_dict.get(item)

    def update_cart_display(self):
        """Update cart display and totals"""
        # Clear cart tree
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)

        # Add cart items
        subtotal = 0
        for cart_item in self.cart_items:
            values = (
                cart_item['name'],
                f"₹{cart_item['unit_price']:.2f}",
                cart_item['qty'],
                f"₹{cart_item['line_total']:.2f}"
            )
            self.cart_tree.insert("", "end", values=values)
            subtotal += cart_item['line_total']

        # Update totals


        tax = subtotal * Decimal(str(self.tax_rate))

        total = subtotal + tax

        self.subtotal_label.configure(text=f"₹{subtotal:.2f}")
        self.tax_label.configure(text=f"₹{tax:.2f}")
        self.total_label.configure(text=f"₹{total:.2f}")

        # Enable/disable checkout button
        self.checkout_btn.configure(state="normal" if self.cart_items else "disabled")

        # ✅ Update profit label
        profit = self.calculate_profit()
        self.profit_label.configure(text=f"Profit: ₹{profit:.2f}")

    def update_cart_item(self):
        """Update quantity of selected cart item"""

        selection = self.cart_tree.selection()

        if not selection:
            messagebox.showwarning(
                "Warning",
                "Please select a cart item to update"
            )
            return

        new_qty = ctk.CTkInputDialog(
            text="Enter new quantity:",
            title="Update Quantity"
        ).get_input()

        if new_qty is None:
            return

        try:
            new_qty = int(new_qty)

            if new_qty <= 0:
                messagebox.showerror(
                    "Error",
                    "Quantity must be greater than 0"
                )
                return

        except ValueError:
            messagebox.showerror(
                "Error",
                "Please enter a valid quantity"
            )
            return

        item_index = self.cart_tree.index(selection[0])

        cart_item = self.cart_items[item_index]

        product_data = db.get_product_by_id(
            cart_item['product_id']
        )

        available_stock = product_data['stock_qty']

        if self.edit_mode:
            available_stock += self.get_original_invoice_qty(
                cart_item['product_id']
            )

        if new_qty > available_stock:
            messagebox.showerror(
                "Error",
                f"Insufficient stock. Available: {available_stock}"
            )
            return

        cart_item['qty'] = new_qty
        cart_item['line_total'] = (
                new_qty * cart_item['unit_price']
        )

        self.update_cart_display()

    def remove_from_cart(self):
        """Remove selected item from cart"""
        selection = self.cart_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a cart item to remove")
            return

        # Remove item
        item_index = self.cart_tree.index(selection[0])
        del self.cart_items[item_index]

        self.update_cart_display()

    def clear_cart(self):
        """Clear all items from cart"""
        if not self.cart_items:
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to clear the cart?"):
            self.cart_items.clear()
            self.update_cart_display()

            if self.edit_mode:
                self.reset_edit_mode()

    def calculate_totals(self):
        """Calculate cart totals"""
        subtotal = sum(item['line_total'] for item in self.cart_items)


        tax = subtotal * Decimal(str(self.tax_rate))

        total = subtotal + tax
        return subtotal, tax, total



    def checkout(self):
        if not self.cart_items:
            messagebox.showwarning("Warning", "Cart is empty")
            return
        customer_name = self.customer_name_entry.get().strip()
        customer_phone = self.customer_phone_entry.get().strip()
        customer_email = self.customer_email_entry.get().strip()


        if not customer_name:
            messagebox.showerror("Input Error", "Please enter Customer Name.")
            return

        if not customer_phone:
            messagebox.showerror("Input Error", "Please enter Customer Phone Number.")
            return

        if not re.fullmatch(r"\d{10}", customer_phone):
            messagebox.showerror("Error", "Phone must be exactly 10 digits")
            return

        if not messagebox.askyesno("Confirm Checkout", "Are you sure you want to process this sale?"):
            return

        try:
            subtotal, tax, total = self.calculate_totals()
            total_profit = self.calculate_profit()
            employee_id = self.parent.current_user['user_id']
            if self.edit_mode:

                success = db.update_sale(
                    self.edit_sale_id,
                    customer_name,
                    customer_phone,
                    customer_email,
                    self.cart_items,
                    subtotal,
                    tax,
                    total,
                    total_profit
                )

                if not success:
                    messagebox.showerror(
                        "Error",
                        "Failed to update invoice."
                    )
                    return

                sale_id = self.edit_sale_id

            else:

                sale_id = db.create_sale(
                    employee_id,
                    customer_name,
                    customer_phone,
                    customer_email,
                    self.cart_items,
                    subtotal,
                    tax,
                    total,
                    total_profit
                )

            if sale_id:
                messagebox.showinfo("Success", f"Sale completed successfully!\nSale ID: {sale_id}")

                # Prepare invoice PDF
                invoices_dir = "invoices"
                os.makedirs(invoices_dir, exist_ok=True)
                invoice_file = os.path.join(invoices_dir, f"Invoice_{sale_id}.pdf")

                shop_info = db.get_shop_info()
                if not shop_info:
                    shop_info = {
                        "name": "Your Shop Name",
                        "address1": "Address Line 1",
                        "address2": "City, State, ZIP",
                        "phone": "1234567890",
                        "email": "contact@yourshop.com",
                        "gstin": "22ABCDE1234F1",
                        "upi_id": "999999999@upi",
                        "upi_name": "Your Shop Name"
                    }



                invoice_pdf.build_invoice_pdf(
                    invoice_file,
                    self.cart_items,
                    customer_name,
                    customer_phone,
                    shop_info=shop_info,
                    invoice_number=sale_id,
                    tax_rate=float(self.tax_rate * 100)
                )
                self.last_invoice_file = invoice_file
                self.last_sale_id = sale_id
                self.view_invoice_btn.configure(state="normal")
                self.save_invoice_btn.configure(state="normal")
                self.email_invoice_btn.configure(state="normal")

                # Clear cart and reload
                self.cart_items.clear()
                self.update_cart_display()
                self.load_products()

                self.reset_edit_mode()


            else:
                messagebox.showerror("Error", "Failed to process the sale.")
        except Exception as ex:
            messagebox.showerror("Error", f"Checkout error: {str(ex)}")

    def prompt_email_and_send_invoice(self, invoice_path, sale_id):
        # Custom dialog to ask for email
        top = simpledialog.askstring("Customer Email", "Enter customer's email address:", parent=self)
        if top:
            email = top.strip()
            if not self.validate_email(email):
                messagebox.showerror("Invalid Email", "Please enter a valid email address.")
                return
            shop_info = db.get_shop_info()
            shop_name = shop_info.get("name", "Your Shop Name")
            subject = f"Your Invoice #{sale_id} from {shop_name}"
            body = "Dear customer,\n\nPlease find attached your invoice.\nThanks for shopping with us!"

            def _send_worker():
                sent = auth.send_email_with_attachment(email, subject, body, invoice_path)
                def _on_finish():
                    if sent:
                        messagebox.showinfo("Success", f"Invoice sent successfully to {email}.")
                    else:
                        messagebox.showerror("Failed", "Failed to send invoice email. Please check your SMTP settings.")
                self.after(0, _on_finish)

            threading.Thread(target=_send_worker, daemon=True).start()

    def validate_email(self, email):
        # simple regex for email validation
        pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        return re.match(pattern, email) is not None

    # def validate_phone(self, phone):
    #     # Allow digits, spaces, +, -, parentheses; length between 7 and 15 for reasonable phone numbers
    #     pattern = r'^\+?[\d\s\-\(\)]{7,15}$'
    #     return re.match(pattern, phone) is not None

    def save_receipt(self, content):
        """Save receipt to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Receipt"
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Success", f"Receipt saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save receipt: {e}")
