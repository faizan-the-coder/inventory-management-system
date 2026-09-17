
import customtkinter as ctk
import tkinter.messagebox as messagebox
import tkinter.ttk as ttk
import db
import re

class SuppliersFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.create_widgets()
        self.load_suppliers()

    def create_widgets(self):
        """Create supplier management widgets"""
        # Title and controls
        self.title_frame = ctk.CTkFrame(self)
        self.title_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        self.title_label = ctk.CTkLabel(
            self.title_frame,
            text="Supplier Management",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(side="left", padx=20, pady=10)

        self.add_btn = ctk.CTkButton(
            self.title_frame,
            text="Add Supplier",
            command=self.add_supplier,
            width=120
        )
        self.add_btn.pack(side="right", padx=20, pady=10)

        # Suppliers table
        self.create_suppliers_table()

    def create_suppliers_table(self):
        """Create suppliers table"""
        self.table_frame = ctk.CTkFrame(self)
        self.table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)

        # Create Treeview for suppliers table
        columns = ("ID", "Name", "Contact Person", "Phone", "Email", "GSTIN", "Created Date")
        self.suppliers_tree = ttk.Treeview(self.table_frame, columns=columns, show="headings", height=15)

        # Configure column headings and widths
        column_widths = {"ID": 50, "Name": 150, "Contact Person": 120, "Phone": 100, 
                        "Email": 180, "GSTIN": 120, "Created Date": 100}

        for col in columns:
            self.suppliers_tree.heading(col, text=col)
            self.suppliers_tree.column(col, width=column_widths.get(col, 100), minwidth=50)

        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.suppliers_tree.yview)
        h_scrollbar = ttk.Scrollbar(self.table_frame, orient="horizontal", command=self.suppliers_tree.xview)
        self.suppliers_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Grid the treeview and scrollbars
        self.suppliers_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        # Action buttons frame
        self.actions_frame = ctk.CTkFrame(self.table_frame)
        self.actions_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        self.edit_btn = ctk.CTkButton(
            self.actions_frame,
            text="Edit Selected",
            command=self.edit_supplier,
            width=120
        )
        self.edit_btn.pack(side="left", padx=10, pady=10)

        self.delete_btn = ctk.CTkButton(
            self.actions_frame,
            text="Delete Selected",
            command=self.delete_supplier,
            width=120,
            fg_color="red",
            hover_color="darkred"
        )
        self.delete_btn.pack(side="left", padx=(5, 10), pady=10)

        self.refresh_btn = ctk.CTkButton(
            self.actions_frame,
            text="Refresh",
            command=self.load_suppliers,
            width=80
        )
        self.refresh_btn.pack(side="right", padx=10, pady=10)

        # Bind double-click to edit
        self.suppliers_tree.bind("<Double-1>", lambda e: self.edit_supplier())

    def show_supplier_form(self, supplier_data=None):
        """Show supplier add/edit form"""
        # Create form window
        form_window = ctk.CTkToplevel(self)
        form_window.title("Add Supplier" if supplier_data is None else "Edit Supplier")
        form_window.geometry("500x550")
        form_window.transient(self)
        form_window.grab_set()

        # Form fields
        fields_frame = ctk.CTkFrame(form_window)
        fields_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Supplier ID
        ctk.CTkLabel(fields_frame, text="Supplier ID:").grid(
            row=0, column=0, sticky="w", padx=10, pady=10
        )

        supplier_id_entry = ctk.CTkEntry(fields_frame, width=300)
        supplier_id_entry.grid(
            row=0, column=1, padx=10, pady=10
        )
        supplier_id_entry.configure(state="readonly")

        # Name
        ctk.CTkLabel(fields_frame, text="Name:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        name_entry = ctk.CTkEntry(fields_frame, width=300)
        name_entry.grid(row=1, column=1, padx=10, pady=5)

        # Contact Person
        ctk.CTkLabel(fields_frame, text="Contact Person:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        contact_entry = ctk.CTkEntry(fields_frame, width=300)
        contact_entry.grid(row=2, column=1, padx=10, pady=5)

        # Phone
        ctk.CTkLabel(fields_frame, text="Phone:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        phone_entry = ctk.CTkEntry(fields_frame, width=300)
        phone_entry.grid(row=3, column=1, padx=10, pady=5)

        # Email
        ctk.CTkLabel(fields_frame, text="Email:").grid(row=4, column=0, sticky="w", padx=10, pady=5)
        email_entry = ctk.CTkEntry(fields_frame, width=300)
        email_entry.grid(row=4, column=1, padx=10, pady=5)

        # Address
        ctk.CTkLabel(fields_frame, text="Address:").grid(row=5, column=0, sticky="nw", padx=10, pady=5)
        address_text = ctk.CTkTextbox(fields_frame, width=300, height=80)
        address_text.grid(row=5, column=1, padx=10, pady=5)

        # GSTIN
        ctk.CTkLabel(fields_frame, text="GSTIN:").grid(row=6, column=0, sticky="w", padx=10, pady=5)
        gstin_entry = ctk.CTkEntry(fields_frame, width=300)
        gstin_entry.grid(row=6, column=1, padx=10, pady=5)

        # Notes
        ctk.CTkLabel(fields_frame, text="Notes:").grid(row=7, column=0, sticky="nw", padx=10, pady=5)
        notes_text = ctk.CTkTextbox(fields_frame, width=300, height=80)
        notes_text.grid(row=7, column=1, padx=10, pady=5)

        if supplier_data is None:
            # Add mode
            supplier_id_entry.configure(state="normal")
            supplier_id_entry.delete(0, "end")
            supplier_id_entry.insert(
                0,
                str(db.get_next_supplier_id())
            )
            supplier_id_entry.configure(state="readonly")

        else:
            # Edit mode
            supplier_id_entry.configure(state="normal")
            supplier_id_entry.delete(0, "end")
            supplier_id_entry.insert(
                0,
                str(supplier_data["supplier_id"])
            )
            supplier_id_entry.configure(state="readonly")

            name_entry.insert(0, supplier_data.get('name') or '')
            name_entry.configure(state="disabled")  # Disable name editing

            contact_entry.insert(0, supplier_data.get('contact_person') or '')
            phone_entry.insert(0, supplier_data.get('phone') or '')
            email_entry.insert(0, supplier_data.get('email') or '')

            address_text.insert(
                "1.0",
                supplier_data.get('address') or ''
            )

            gstin_entry.insert(
                0,
                supplier_data.get('gstin') or ''
            )

            notes_text.insert(
                "1.0",
                supplier_data.get('notes') or ''
            )
        # Buttons
        button_frame = ctk.CTkFrame(fields_frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=20)

        def save_supplier():
            name = name_entry.get().strip()
            phone=phone_entry.get().strip()
            email=email_entry.get().strip()
            gstin=gstin_entry.get().strip()

            if not name:
                messagebox.showerror("Error", "Supplier name is required")
                return

            # Phone validation
            if not re.fullmatch(r"\d{10}", phone):
                messagebox.showerror("Error", "Phone must be exactly 10 digits")
                return

            # Email validation
            if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email):
                messagebox.showerror("Error", "Invalid email format")
                return


            # Uniqueness check
            all_suppliers = db.get_all_suppliers()
            for s in all_suppliers:
                supplier_id = supplier_data['supplier_id'] if supplier_data else None
                if supplier_data is not None and s['supplier_id'] == supplier_id:
                    continue  # Skip self!
                if s['name'].lower() == name.lower():
                    messagebox.showerror("Error", "Supplier name already exists")
                    return
                if gstin and s['gstin'] == gstin:
                    messagebox.showerror("Error", "GSTIN already exists")
                    return
                if s['email'].lower() == email.lower():
                    messagebox.showerror("Error", "Supplier email already exists")
                    return
                if s['phone'] == phone:
                    messagebox.showerror("Error", "Supplier phone already exists")
                    return

            supplier_info = {
                'name': name,
                'contact_person': contact_entry.get().strip(),
                'phone': phone,
                'email': email,
                'address': address_text.get("1.0", "end-1c").strip(),
                'gstin': gstin,
                'notes': notes_text.get("1.0", "end-1c").strip(),
                'user_id': None  # Not linking to user for now
            }

            try:
                if supplier_data:
                    # Update existing supplier
                    success = db.update_supplier(supplier_data['supplier_id'], supplier_info)
                else:
                    # Add new supplier
                    success = db.add_supplier(supplier_info)

                if success:
                    messagebox.showinfo("Success", "Supplier saved successfully")
                    form_window.destroy()
                    self.load_suppliers()
                else:
                    messagebox.showerror("Error", "Failed to save supplier")
            except Exception as e:
                messagebox.showerror("Error", f"Error saving supplier: {e}")

        save_btn = ctk.CTkButton(
            button_frame,
            text="Save",
            command=save_supplier,
            width=100
        )
        save_btn.pack(side="left", padx=10, pady=10)

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=form_window.destroy,
            width=100
        )
        cancel_btn.pack(side="left", padx=10, pady=10)

    def load_suppliers(self):
        """Load suppliers into table"""
        # Clear existing data
        for item in self.suppliers_tree.get_children():
            self.suppliers_tree.delete(item)

        # Load suppliers
        suppliers = db.get_all_suppliers()

        for supplier in suppliers:
            values = (
                supplier['supplier_id'],
                supplier['name'],
                supplier['contact_person'] or '',
                supplier['phone'] or '',
                supplier['email'] or '',
                supplier['gstin'] or '',
                supplier['created_at'].strftime('%Y-%m-%d') if supplier['created_at'] else ''
            )
            self.suppliers_tree.insert("", "end", values=values)

    def add_supplier(self):
        """Show add supplier form"""
        self.show_supplier_form()

    def edit_supplier(self):
        """Edit selected supplier"""
        selection = self.suppliers_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a supplier to edit")
            return

        # Get selected supplier data
        item = selection[0]
        values = self.suppliers_tree.item(item)['values']

        # Get full supplier data from database
        supplier_id = values[0]
        suppliers = db.get_all_suppliers()
        supplier_data = next((s for s in suppliers if s['supplier_id'] == supplier_id), None)

        if supplier_data:
            self.show_supplier_form(supplier_data)

    def delete_supplier(self):
        selection = self.suppliers_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a supplier to delete")
            return
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete selected supplier?"):
            item = selection[0]
            supplier_id = self.suppliers_tree.item(item)['values'][0]
            success = False
            try:
                success = db.delete_supplier(supplier_id)
            except Exception as e:
                messagebox.showerror("Error", f"Error deleting supplier: {e}")
                return

            if success:
                messagebox.showinfo("Success", "Supplier deleted successfully")
                self.load_suppliers()
            else:
                messagebox.showerror("Error", "Cannot delete supplier: linked records")
