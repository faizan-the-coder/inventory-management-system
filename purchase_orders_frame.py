
import customtkinter as ctk
import tkinter.messagebox as messagebox
import tkinter.ttk as ttk
import db
from datetime import datetime

class PurchaseOrdersFrame(ctk.CTkFrame):
    def __init__(self, parent,supplier_ids=None):
        super().__init__(parent)
        self.parent = parent
        # If admin, do not filter by supplier_ids
        if self.parent.current_user['role'] == 'Admin':
            self.supplier_ids = None  # Or empty to load all
        else:

            self.supplier_ids = supplier_ids or []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.create_widgets()
        self.po_tree.bind("<<TreeviewSelect>>", lambda e: self.update_received_button())

        self.load_purchase_orders()
        self.update_received_button()

    def create_widgets(self):
        """Create purchase order management widgets"""
        # Title and controls
        title_frame = ctk.CTkFrame(self)
        title_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        self.title_label = ctk.CTkLabel(
            title_frame,
            text="Purchase Orders",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(side="left", padx=20, pady=10)

        # Create PO button (Admin only)
        if self.parent.current_user['role'] == 'Admin':
            create_btn = ctk.CTkButton(
                title_frame,
                text="Create PO",
                command=self.create_purchase_order,
                width=100
            )
            create_btn.pack(side="right", padx=20, pady=10)

        # Purchase Orders table
        self.create_po_table()

        # Action buttons
        self.create_action_buttons()

    def create_po_table(self):
        """Create purchase orders table"""
        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Create Treeview
        columns = ("PO ID", "Supplier", "Status", "Created Date", "Expected Date", "Total Amount", "Notes")
        self.po_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        # Configure columns
        column_widths = {"PO ID": 80, "Supplier": 150, "Status": 100, "Created Date": 120, 
                        "Expected Date": 120, "Total Amount": 120, "Notes": 200}

        for col in columns:
            self.po_tree.heading(col, text=col)
            self.po_tree.column(col, width=column_widths.get(col, 100), minwidth=50)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.po_tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=self.po_tree.xview)
        self.po_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        self.po_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        # Bind double-click to view details
        self.po_tree.bind("<Double-1>", self.view_po_details)

    def create_action_buttons(self):
        """Create action buttons"""
        actions_frame = ctk.CTkFrame(self)
        actions_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)

        # Edit button (Admin only)
        if self.parent.current_user['role'] == 'Admin':
            edit_btn = ctk.CTkButton(
                actions_frame,
                text="Edit Selected",
                command=self.edit_purchase_order,
                width=120
            )
            edit_btn.pack(side="left", padx=10, pady=10)

        # Mark as Received button (for suppliers and admin)
        if self.parent.current_user['role'] in ['Admin', 'Supplier']:
            if self.parent.current_user['role'] == 'Admin':
                text = "Mark as Received"
            else:
                text = "Mark as Delivered"
            self.received_btn = ctk.CTkButton(
                actions_frame,
                text=text,
                command=self.mark_received,
                width=120,
                fg_color="green",
                hover_color="darkgreen"
            )
            self.received_btn.pack(side="left", padx=(5, 10), pady=10)

        if self.parent.current_user['role'] in ['Admin', 'Supplier']:
            self.cancel_btn = ctk.CTkButton(
                actions_frame,
                text="Cancel Order",
                command=self.cancel_order,
                width=120,
                fg_color="red",
                hover_color="darkred"
            )
            self.cancel_btn.pack(side="left", padx=(5, 10), pady=10)

        # Refresh button
        refresh_btn = ctk.CTkButton(
            actions_frame,
            text="Refresh",
            command=self.load_purchase_orders,
            width=80
        )
        refresh_btn.pack(side="right", padx=10, pady=10)

    def update_received_button(self):
        selection = self.po_tree.selection()
        if not selection:
            if self.parent.current_user['role'] == 'Admin':
                text = "Mark as Received"
            else:
                text = "Mark as Delivered"
            self.received_btn.configure(text=text, command=self.mark_received, fg_color="green")
            return

        po_id = self.po_tree.item(selection[0])['values'][0]
        po = next((p for p in self.purchase_orders_cache if p['po_id'] == po_id), None)
        if po is None:
            self.received_btn.configure(text="Mark as Received", command=self.mark_received, fg_color="green")
            return
        if po['status'] == 'Cancelled':
            # Disable both buttons
            self.received_btn.configure(state="disabled")
            self.cancel_btn.configure(state="disabled")
            return

            # Enable cancel button unless already cancelled
        self.cancel_btn.configure(state="normal")
        self.received_btn.configure(state="normal")
        if po['status'] == 'Received':
            if self.parent.current_user['role'] == 'Admin':
                self.received_btn.configure(text="Undo Received", command=self.undo_received, fg_color="red")
            else:
                self.received_btn.configure(text="Undo Delivered", command=self.undo_received, fg_color="red")
        else:
            if self.parent.current_user['role'] == 'Admin':
                self.received_btn.configure(text="Mark as Received", command=self.mark_received, fg_color="green")
            else:
                self.received_btn.configure(text="Mark as Delivered", command=self.mark_received, fg_color="green")

    def load_purchase_orders(self):
        if self.supplier_ids:  # filter only if there are supplier ids
            self.purchase_orders_cache = db.get_purchase_orders_for_suppliers(self.supplier_ids)
        else:
            self.purchase_orders_cache = db.get_purchase_orders_with_supplier()  # load all


        self.po_tree.delete(*self.po_tree.get_children())
        for po in self.purchase_orders_cache:
            status_display = po['status']
            # Highlight Cancelled status, e.g., prefix or suffix with emoji
            if po['status'] == 'Cancelled':
                status_display = "❌ Cancelled"
            elif po['status'] == 'Ordered':
                status_display = "⏳ Ordered"
            elif po['status'] == 'Received':
                status_display = "✅ Received"
            else:
                status_display = po['status']

            self.po_tree.insert(
                "",
                "end",
                values=(
                    po['po_id'],
                    po['supplier_name'],
                    status_display,
                    po['created_at'].strftime('%Y-%m-%d'),
                    po['expected_date'].strftime('%Y-%m-%d') if po['expected_date'] else "",
                    f"₹{po['total_amount']:,.2f}",
                    po['notes'] or ""
                )
            )


    def create_purchase_order(self):
        po_window = ctk.CTkToplevel()
        po_window.title("Create Purchase Order")
        po_window.geometry("700x650")
        po_window.transient(self)
        po_window.grab_set()

        form_frame = ctk.CTkFrame(po_window)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        form_frame.grid_columnconfigure(1, weight=1)

        input_width = 350  # A balanced width for inputs and treeviews

        # PO ID
        ctk.CTkLabel(
            form_frame,
            text="PO ID:"
        ).grid(row=0, column=0, sticky="w", padx=10, pady=5)

        po_id_entry = ctk.CTkEntry(
            form_frame,
            width=input_width
        )
        po_id_entry.grid(
            row=0,
            column=1,
            sticky="ew", pady=(0, 8)
        )

        po_id_entry.insert(
            0,
            str(db.get_next_po_id())
        )

        po_id_entry.configure(state="readonly")

        # Supplier
        ctk.CTkLabel(form_frame, text="Supplier:", anchor="w", font=ctk.CTkFont(weight="bold")) \
            .grid(row=1, column=0, sticky="w", pady=(0, 8))
        suppliers = db.get_all_suppliers()
        supplier_combo = ctk.CTkComboBox(form_frame, values=[s['name'] for s in suppliers], width=input_width)
        supplier_combo.grid(row=1, column=1, sticky="ew", pady=(0, 8))

        # Expected Date
        ctk.CTkLabel(form_frame, text="Expected Date:", anchor="w", font=ctk.CTkFont(weight="bold")) \
            .grid(row=2, column=0, sticky="w", pady=(0, 8))
        expected_date_entry = ctk.CTkEntry(form_frame, placeholder_text="YYYY-MM-DD", width=input_width)
        expected_date_entry.grid(row=2, column=1, sticky="ew", pady=(0, 8))

        # Notes
        ctk.CTkLabel(form_frame, text="Notes:", anchor="w", font=ctk.CTkFont(weight="bold")) \
            .grid(row=3, column=0, sticky="nw", pady=(0, 8))
        notes_text = ctk.CTkTextbox(form_frame, width=input_width, height=80)
        notes_text.grid(row=3, column=1, sticky="ew", pady=(0, 8))

        # Products Label
        ctk.CTkLabel(form_frame, text="Select Products:", anchor="w", font=ctk.CTkFont(weight="bold")) \
            .grid(row=4, column=0, sticky="nw", pady=(15, 8))

        # Products List Treeview
        product_frame = ctk.CTkFrame(form_frame)
        product_frame.grid(row=4, column=1, sticky="nsew", pady=(15, 8))
        product_frame.grid_columnconfigure(0, weight=1)
        product_frame.grid_rowconfigure(0, weight=1)

        product_columns = ("Name", "SKU", "Price")
        products_tree = ttk.Treeview(product_frame, columns=product_columns, show="headings", height=7)
        for col in product_columns:
            width = 200 if col == "Name" else 80
            products_tree.heading(col, text=col)
            products_tree.column(col, width=width, anchor="center")
        products_tree.grid(row=0, column=0, sticky="nsew")

        vsb = ttk.Scrollbar(product_frame, orient="vertical", command=products_tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        products_tree.configure(yscrollcommand=vsb.set)

        # Load products
        for p in db.get_all_products():
            products_tree.insert("", "end", values=(p['name'], p['sku'], f"₹{p['unit_price']:.2f}"))

        # Quantity input and Add button container
        qty_add_frame = ctk.CTkFrame(form_frame)
        qty_add_frame.grid(row=5, column=1, sticky="w", pady=(0, 15))

        ctk.CTkLabel(qty_add_frame, text="Quantity:", width=80).pack(side="left")
        qty_entry = ctk.CTkEntry(qty_add_frame, width=80)
        qty_entry.pack(side="left", padx=(5, 20))

        add_btn = ctk.CTkButton(qty_add_frame, text="Add Product", width=120)
        add_btn.pack(side="left")

        # PO Items Treeview
        po_items_frame = ctk.CTkFrame(form_frame)
        po_items_frame.grid(row=6, column=1, sticky="nsew", pady=(0, 8))
        po_items_frame.grid_columnconfigure(0, weight=1)
        po_items_frame.grid_rowconfigure(0, weight=1)

        po_columns = ("Name", "SKU", "Unit Price", "Quantity", "Line Total")
        po_items_tree = ttk.Treeview(po_items_frame, columns=po_columns, show="headings", height=7)
        for col, width in zip(po_columns, (200, 80, 90, 80, 90)):
            po_items_tree.heading(col, text=col)
            po_items_tree.column(col, width=width, anchor="center")
        po_items_tree.grid(row=0, column=0, sticky="nsew")

        vsb_po = ttk.Scrollbar(po_items_frame, orient="vertical", command=po_items_tree.yview)
        vsb_po.grid(row=0, column=1, sticky="ns")
        po_items_tree.configure(yscrollcommand=vsb_po.set)

        # Remove item button
        remove_btn = ctk.CTkButton(form_frame, text="Remove Selected Item", width=150)
        remove_btn.grid(row=7, column=1, sticky="w")

        # Button functionality
        def add_product_to_po():
            sel = products_tree.selection()
            if not sel:
                messagebox.showerror("Error", "Please select a product to add.")
                return
            try:
                qty = int(qty_entry.get())
                if qty <= 0:
                    raise ValueError
            except:
                messagebox.showerror("Error", "Please enter a valid quantity (> 0).")
                return

            item = products_tree.item(sel[0])["values"]
            sku = item[1]
            price_str = item[2].replace("₹", "").replace(",", "")
            price = float(price_str)

            # Check if already added
            for iid in po_items_tree.get_children():
                vals = po_items_tree.item(iid)["values"]
                if vals[1] == sku:
                    new_qty = int(vals[3]) + qty
                    new_total = round(new_qty * price, 2)
                    po_items_tree.item(iid, values=(vals[0], sku, f"₹{price:.2f}", str(new_qty), f"₹{new_total:.2f}"))
                    qty_entry.delete(0, "end")
                    return

            total = round(qty * price, 2)
            po_items_tree.insert("", "end", values=(item[0], sku, f"₹{price:.2f}", str(qty), f"₹{total:.2f}"))
            qty_entry.delete(0, "end")

        def remove_selected():
            items = po_items_tree.selection()
            if not items:
                messagebox.showerror("Error", "Please select item(s) to remove.")
                return
            for i in items:
                po_items_tree.delete(i)

        add_btn.configure(command=add_product_to_po)
        remove_btn.configure(command=remove_selected)

        # Save and Cancel buttons
        btn_frame = ctk.CTkFrame(form_frame)
        btn_frame.grid(row=8, column=1, columnspan=2, sticky="ew", pady=(20, 0))
        btn_frame.grid_columnconfigure(0, weight=1)

        save_btn = ctk.CTkButton(btn_frame, text="Save Purchase Order", width=150)
        save_btn.grid(row=0, column=0, sticky="w", padx=20)

        cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", width=150, command=po_window.destroy)
        cancel_btn.grid(row=0, column=1, sticky="e", padx=20)

        def save_po():
            supplier_name = supplier_combo.get()
            if not supplier_name:
                messagebox.showerror("Error", "Please select a supplier.")
                return

            supplier_obj = next((s for s in suppliers if s['name'] == supplier_name), None)
            if not supplier_obj:
                messagebox.showerror("Error", "Invalid supplier selected.")
                return
            supplier_id = supplier_obj['supplier_id']

            expected_date = expected_date_entry.get().strip()
            notes = notes_text.get("0.0", "end").strip()

            po_items = []
            for iid in po_items_tree.get_children():
                vals = po_items_tree.item(iid)['values']
                try:
                    qty = int(vals[3])
                    if qty <= 0:
                        raise ValueError
                except:
                    messagebox.showerror("Error", f"Invalid quantity for product {vals[0]}")
                    return
                price_str = vals[2].replace("₹", "").replace(",", "")
                price = float(price_str)
                po_items.append({'sku': vals[1], 'unit_price': price, 'qty': qty})

            if not po_items:
                messagebox.showerror("Error", "Please add at least one product with quantity.")
                return

            total_amount = sum(item['unit_price'] * item['qty'] for item in po_items)

            po_data = {
                'supplier_id': supplier_id,
                'status': 'Ordered',
                'expected_date': expected_date,
                'notes': notes,
                'total_amount': total_amount
            }

            po_id = db.add_purchase_order(po_data, po_items)
            if po_id:
                messagebox.showinfo("Success", f"Purchase Order #{po_id} created successfully!")
                po_window.destroy()
                self.load_purchase_orders()
            else:
                messagebox.showerror("Error", "Failed to create purchase order.")

        save_btn.configure(command=save_po)

    def undo_received(self):
        selection = self.po_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a purchase order to undo received")
            return
        po_id = self.po_tree.item(selection[0])['values'][0]
        if messagebox.askyesno("Confirm",
                               f"Undo receiving of Purchase Order #{po_id}? This will reduce stock accordingly."):
            success = db.undo_received_po(po_id)
            if success:
                messagebox.showinfo("Success", "Purchase order receiving undone")
                self.load_purchase_orders()
                self.update_received_button()
            else:
                messagebox.showerror("Error", "Failed to undo receiving")

    def cancel_order(self):
        selection = self.po_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a purchase order to cancel")
            return

        po_id = self.po_tree.item(selection[0])['values'][0]
        po = next((p for p in self.purchase_orders_cache if p['po_id'] == po_id), None)

        if po and po['status'] == 'Cancelled':
            messagebox.showinfo("Info", "This order is already cancelled.")
            return
        if po and po['status'] == 'Received':
            messagebox.showwarning("Warning", "Cannot cancel a received order.")
            return

        if messagebox.askyesno("Confirm", f"Are you sure you want to cancel Purchase Order #{po_id}?"):
            success = db.cancel_purchase_order(po_id)
            if success:
                messagebox.showinfo("Success", "Purchase order cancelled")
                self.load_purchase_orders()
                self.update_received_button()
            else:
                messagebox.showerror("Error", "Failed to cancel purchase order")

    def mark_received(self):
        selection = self.po_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a purchase order to mark as received")
            return
        po_id = self.po_tree.item(selection[0])['values'][0]
        if messagebox.askyesno("Confirm", f"Mark Purchase Order #{po_id} as received?"):
            db.mark_po_received(po_id)  # Update PO status in database
            messagebox.showinfo("Success", "Purchase order marked received")
            self.load_purchase_orders()
            self.update_received_button()

    def view_po_details(self, event):
        selection = self.po_tree.selection()
        if not selection:
            return

        po_id = self.po_tree.item(selection[0])['values'][0]

        # Fetch purchase order and items
        po_record = None
        for po in self.purchase_orders_cache:
            if po['po_id'] == po_id:
                po_record = po
                break
        if not po_record:
            po_record = next((po for po in db.get_purchase_orders_with_supplier() if po['po_id'] == po_id), None)
        po_items = db.get_purchase_items(po_id)

        # Create details window with nicer layout
        details_window = ctk.CTkToplevel(self)
        details_window.title(f"Purchase Order #{po_id} Details")
        details_window.geometry("700x500")
        details_window.transient(self)
        details_window.grab_set()

        container = ctk.CTkFrame(details_window)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        header = ctk.CTkLabel(container, text=f"Purchase Order #{po_id}",
                              font=ctk.CTkFont(size=20, weight="bold"))
        header.pack(pady=(0, 10))

        # Display PO summary info
        info_frame = ctk.CTkFrame(container)
        info_frame.pack(fill="x", pady=(0, 15))

        def add_info(label_text, value_text):
            frame = ctk.CTkFrame(info_frame)
            frame.pack(anchor="w", pady=2, fill="x")

            label = ctk.CTkLabel(frame, text=label_text + ":", width=150, anchor="w", font=ctk.CTkFont(weight="bold"))
            label.pack(side="left")
            value = ctk.CTkLabel(frame, text=value_text, anchor="w")
            value.pack(side="left", fill="x", expand=True)

        add_info("Supplier", po_record['supplier_name'])
        add_info("Status", po_record['status'])
        add_info("Created Date", po_record['created_at'].strftime('%Y-%m-%d'))
        add_info("Expected Date",
                 po_record['expected_date'].strftime('%Y-%m-%d') if po_record['expected_date'] else "-")
        add_info("Total Amount", f"₹{po_record['total_amount']:,.2f}")
        add_info("Notes", po_record['notes'] or "-")

        # Items Label
        items_label = ctk.CTkLabel(container, text="Items", font=ctk.CTkFont(size=16, weight="bold"))
        items_label.pack(anchor="w", pady=(10, 0))

        # Items list in a scrollable frame
        items_frame = ctk.CTkScrollableFrame(container, height=200)
        items_frame.pack(fill="both", expand=True,pady=(10,0))

        for item in po_items:
            item_text = f"{item['product_name']} | Qty: {item['qty']} | Unit Price: ₹{item['unit_cost']:.2f} | Total: ₹{item['line_total']:.2f}"
            label = ctk.CTkLabel(items_frame, text=item_text, anchor="w", padx=10)
            label.pack(fill="x", pady=2)

    def edit_purchase_order(self):
        selection = self.po_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an order")
            return

        po_id = self.po_tree.item(selection[0])['values'][0]
        po_record = next((po for po in db.get_purchase_orders_with_supplier() if po['po_id'] == po_id), None)
        if not po_record:
            messagebox.showerror("Error", "Failed to load order details")
            return
        # Disable editing if status is Cancelled
        if po_record['status'] == 'Cancelled':
            messagebox.showinfo("Info", "Cancelled orders cannot be edited.")
            return
        po_items = db.get_purchase_items(po_id)

        def save_changes():
            selected_supplier_name = supplier_combo.get()
            selected_supplier = next((s for s in db.get_all_suppliers() if s['name'] == selected_supplier_name), None)
            if not selected_supplier:
                messagebox.showerror("Error", "Please select a valid supplier")
                return

            expected_date = expected_date_entry.get()
            notes = notes_text.get("0.0", "end").strip()

            updated_items = []
            for iid in products_tree.get_children():
                vals = products_tree.item(iid)['values']
                if vals[3]:
                    try:
                        qty = int(vals[3])
                        if qty <= 0:
                            raise ValueError
                    except:
                        messagebox.showerror("Error", f"Invalid quantity for product {vals[0]}")
                        return
                    idx = next((i for i, p in enumerate(populated_products) if p['sku'] == vals[1]), None)
                    if idx is None:
                        messagebox.showerror("Error", f"Product {vals[0]} mismatch")
                        return
                    updated_items.append({
                        'sku': vals[1],
                        'unit_price': populated_products[idx]['unit_price'],
                        'qty': qty
                    })
            if not updated_items:
                messagebox.showerror("Error", "Add at least one product with quantity")
                return

            total_amount = sum(item['unit_price'] * item['qty'] for item in updated_items)

            po_data = {
                'supplier_id': selected_supplier['supplier_id'],
                'expected_date': expected_date,
                'notes': notes,
                'total_amount': total_amount,
                'status': po_record['status']
            }

            success = db.update_purchase_order(po_id, po_data, updated_items)
            if success:
                messagebox.showinfo("Success", "Order updated successfully")
                edit_win.destroy()
                self.load_purchase_orders()
            else:
                messagebox.showerror("Error", "Failed to update order")

        edit_win = ctk.CTkToplevel(self)
        edit_win.title(f"Edit Purchase Order #{po_id}")
        edit_win.geometry("700x600")
        edit_win.transient(self)
        edit_win.grab_set()

        frame = ctk.CTkFrame(edit_win, corner_radius=10, border_width=2, border_color="gray80")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(3, weight=1)

        # PO ID
        ctk.CTkLabel(
            frame,
            text="PO ID:",
            font=ctk.CTkFont(weight="bold")
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=6,
            padx=10
        )

        po_id_entry = ctk.CTkEntry(
            frame,
            width=350
        )

        po_id_entry.grid(
            row=0,
            column=1,
            sticky="ew",
            pady=6,
            padx=10
        )

        po_id_entry.insert(
            0,
            str(po_record["po_id"])
        )

        po_id_entry.configure(
            state="readonly"
        )

        # Supplier Label + Combo
        ctk.CTkLabel(frame, text="Supplier:", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, sticky="w", pady=6,padx=10)
        suppliers = db.get_all_suppliers()
        supplier_combo = ctk.CTkComboBox(frame, values=[s['name'] for s in suppliers], width=350)
        supplier_combo.grid(row=1, column=1, sticky="ew", pady=6,padx=10)
        supplier_combo.set(po_record['supplier_name'])

        # Expected Date Label + Entry
        ctk.CTkLabel(frame, text="Expected Date:", font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, sticky="w",
                                                                                         pady=6,padx=10)
        expected_date_entry = ctk.CTkEntry(frame, width=350)
        expected_date_entry.grid(row=2, column=1, sticky="ew", pady=6,padx=10)
        expected_date_entry.insert(0, po_record['expected_date'].strftime('%Y-%m-%d') if po_record[
            'expected_date'] else "")

        # Notes Label + Textbox
        ctk.CTkLabel(frame, text="Notes:", font=ctk.CTkFont(weight="bold")).grid(row=3, column=0, sticky="nw", pady=6,padx=10)
        notes_text = ctk.CTkTextbox(frame, width=350, height=80)
        notes_text.grid(row=3, column=1, sticky="ew", pady=6,padx=10)
        if po_record['notes']:
            notes_text.insert("0.0", po_record['notes'])

        # Products Label
        ctk.CTkLabel(frame, text="Products:", font=ctk.CTkFont(weight="bold")).grid(row=4, column=0, sticky="nw",
                                                                                    pady=6,padx=10)

        # Products Treeview
        products_tree = ttk.Treeview(frame, columns=("Name", "SKU", "Price", "Qty"), show='headings', height=10)
        products_tree.grid(row=4, column=1, sticky="nsew", pady=6,padx=10)
        # Scrollbar for products_tree
        vsb = ttk.Scrollbar(frame, orient="vertical", command=products_tree.yview)
        vsb.grid(row=4, column=2, sticky="ns", pady=6,padx=(0,10))
        products_tree.configure(yscrollcommand=vsb.set)

        for col, width in zip(("Name", "SKU", "Price", "Qty"), (200, 80, 90, 70)):
            products_tree.heading(col, text=col)
            products_tree.column(col, width=width, anchor='center')

        populated_products = db.get_all_products()
        for p in populated_products:
            products_tree.insert('', 'end', values=(p['name'], p['sku'], f"₹{p['unit_price']:.2f}", ""))

        # Set quantities in tree from existing PO items
        for item in po_items:
            for iid in products_tree.get_children():
                vals = products_tree.item(iid)['values']
                if len(vals) > 1 and vals[1] == item['sku']:
                    products_tree.set(iid, 'Qty', str(item['qty']))
                    break

        def on_double_click(event):
            # Identify the clicked cell
            region = products_tree.identify("region", event.x, event.y)
            if region != "cell":
                return

            col = products_tree.identify_column(event.x)
            rowid = products_tree.identify_row(event.y)

            # Only allow editing Qty column (#4)
            if col != '#4' or not rowid:
                return

            current_val = products_tree.set(rowid, "Qty")

            # Popup small edit window
            popup = ctk.CTkToplevel(edit_win)
            popup.title("Edit Quantity")
            popup.geometry("250x150")
            popup.transient(edit_win)
            popup.grab_set()

            ctk.CTkLabel(popup, text="Enter new quantity:", font=ctk.CTkFont(weight="bold")).pack(pady=10)
            qty_var = ctk.StringVar(value=current_val)
            qty_entry = ctk.CTkEntry(popup, textvariable=qty_var, width=100)
            qty_entry.pack(pady=5)
            qty_entry.focus()

            def save_and_close():
                try:
                    val = int(qty_var.get())
                    if val < 0:
                        raise ValueError
                    products_tree.set(rowid, column="Qty", value=str(val))
                    popup.destroy()
                except ValueError:
                    messagebox.showerror("Invalid input", "Please enter a valid non-negative integer.")

            ctk.CTkButton(popup, text="Save", command=save_and_close).pack(pady=10)

            # Bind Enter key
            qty_entry.bind("<Return>", lambda e: save_and_close())

        # Bind the double-click event to the handler
        products_tree.bind("<Double-1>", on_double_click)

        # Buttons Frame
        btn_frame = ctk.CTkFrame(frame)
        btn_frame.grid(row=5, column=1, pady=15, sticky='ew',padx=10)
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        save_btn = ctk.CTkButton(btn_frame, text='Save Changes', width=150, command=save_changes)
        save_btn.grid(row=0, column=0, sticky='w')

        cancel_btn = ctk.CTkButton(btn_frame, text='Cancel', width=150, command=edit_win.destroy)
        cancel_btn.grid(row=0, column=1, sticky='e')




