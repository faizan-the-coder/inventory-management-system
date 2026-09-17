
import customtkinter as ctk
import tkinter.messagebox as messagebox
import tkinter.ttk as ttk
import db

class ProductsFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.create_widgets()
        self.load_products()

    def create_widgets(self):
        """Create product management widgets"""
        # Title and controls
        self.title_frame = ctk.CTkFrame(self)
        self.title_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

        self.title_label = ctk.CTkLabel(
            self.title_frame,
            text="Product Management",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(side="left", padx=20, pady=10)

        # Search and add controls
        self.search_entry = ctk.CTkEntry(
            self.title_frame,
            placeholder_text="Search products...",
            width=200
        )
        self.search_entry.pack(side="right", padx=(10, 0), pady=10)
        self.search_entry.bind("<KeyRelease>", self.on_search)

        self.search_btn = ctk.CTkButton(
            self.title_frame,
            text="Search",
            command=self.search_products,
            width=80
        )
        self.search_btn.pack(side="right", padx=(10, 0), pady=10)

        self.add_btn = ctk.CTkButton(
            self.title_frame,
            text="Add Product",
            command=self.add_product,
            width=120
        )
        self.add_btn.pack(side="right", padx=(10, 0), pady=10)

        # Products list
        self.create_products_table()

        # Product form (initially hidden)
        self.create_product_form()

    def generate_barcode(self):
        # For simplicity, generate unique barcode similar to SKU or leave blank for manual input
        import time
        return f"BAR{int(time.time())}"

    def create_products_table(self):
        """Create products table"""
        self.table_frame = ctk.CTkFrame(self)
        self.table_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 10))
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)

        # Create Treeview for products table
        columns = ("ID", "SKU", "Name", "Category", "Supplier", "Unit Price", "Stock", "Reorder Level", "Status")
        self.products_tree = ttk.Treeview(self.table_frame, columns=columns, show="headings", height=15)

        # Configure column headings and widths
        column_widths = {"ID": 50, "SKU": 80, "Name": 200, "Category": 120, "Supplier": 150, 
                        "Unit Price": 100, "Stock": 80, "Reorder Level": 100, "Status": 80}

        for col in columns:
            self.products_tree.heading(col, text=col)
            self.products_tree.column(col, width=column_widths.get(col, 100), minwidth=50)

        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.products_tree.yview)
        h_scrollbar = ttk.Scrollbar(self.table_frame, orient="horizontal", command=self.products_tree.xview)
        self.products_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Grid the treeview and scrollbars
        self.products_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        # Action buttons frame
        self.actions_frame = ctk.CTkFrame(self.table_frame)
        self.actions_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        self.edit_btn = ctk.CTkButton(
            self.actions_frame,
            text="Edit Selected",
            command=self.edit_product,
            width=120
        )
        self.edit_btn.pack(side="left", padx=10, pady=10)

        self.delete_btn = ctk.CTkButton(
            self.actions_frame,
            text="Delete Selected",
            command=self.delete_product,
            width=120,
            fg_color="red",
            hover_color="darkred"
        )
        self.delete_btn.pack(side="left", padx=(5, 10), pady=10)

        self.refresh_btn = ctk.CTkButton(
            self.actions_frame,
            text="Refresh",
            command=self.load_products,
            width=80
        )
        self.refresh_btn.pack(side="right", padx=10, pady=10)

        # Bind double-click to edit
        self.products_tree.bind("<Double-1>", lambda e: self.edit_product())

    def create_product_form(self):
        """Create product add/edit form"""
        self.form_window = None

    def show_product_form(self, product_data=None):
        """Show product add/edit form"""
        if self.form_window is not None:
            self.form_window.destroy()

        # Create form window
        self.form_window = ctk.CTkToplevel(self)
        self.form_window.title("Add Product" if product_data is None else "Edit Product")
        self.form_window.geometry("500x550")
        self.form_window.transient(self)
        self.form_window.grab_set()

        # Form fields
        fields_frame = ctk.CTkFrame(self.form_window)
        fields_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Product ID
        ctk.CTkLabel(
            fields_frame,
            text="Product ID:"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=10,
            pady=5
        )

        self.product_id_entry = ctk.CTkEntry(
            fields_frame,
            width=300
        )
        self.product_id_entry.grid(
            row=0,
            column=1,
            padx=10,
            pady=5
        )
        self.product_id_entry.configure(state="readonly")

        # SKU
        ctk.CTkLabel(fields_frame, text="SKU:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.sku_entry = ctk.CTkEntry(fields_frame, width=300)
        self.sku_entry.grid(row=1, column=1, padx=10, pady=5)


        # Name
        ctk.CTkLabel(fields_frame, text="Name:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.name_entry = ctk.CTkEntry(fields_frame, width=300)
        self.name_entry.grid(row=2, column=1, padx=10, pady=5)

        # Category
        ctk.CTkLabel(fields_frame, text="Category:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        categories = db.get_all_categories()
        category_values = [cat['name'] for cat in categories]
        self.category_combo = ctk.CTkComboBox(fields_frame, values=category_values, width=300)
        self.category_combo.grid(row=3, column=1, padx=10, pady=5)

        # Supplier
        ctk.CTkLabel(fields_frame, text="Supplier:").grid(row=4, column=0, sticky="w", padx=10, pady=5)
        suppliers = db.get_all_suppliers()
        supplier_values = [sup['name'] for sup in suppliers]
        self.supplier_combo = ctk.CTkComboBox(fields_frame, values=supplier_values, width=300)
        self.supplier_combo.grid(row=4, column=1, padx=10, pady=5)

        # Unit Price
        ctk.CTkLabel(fields_frame, text="Unit Price:").grid(row=5, column=0, sticky="w", padx=10, pady=5)
        self.unit_price_entry = ctk.CTkEntry(fields_frame, width=300)
        self.unit_price_entry.grid(row=5, column=1, padx=10, pady=5)

        # Cost Price
        ctk.CTkLabel(fields_frame, text="Cost Price:").grid(row=6, column=0, sticky="w", padx=10, pady=5)
        self.cost_price_entry = ctk.CTkEntry(fields_frame, width=300)
        self.cost_price_entry.grid(row=6, column=1, padx=10, pady=5)

        # Stock Quantity
        ctk.CTkLabel(fields_frame, text="Stock Qty:").grid(row=7, column=0, sticky="w", padx=10, pady=5)
        self.stock_entry = ctk.CTkEntry(fields_frame, width=300)
        self.stock_entry.grid(row=7, column=1, padx=10, pady=5)

        # Reorder Level
        ctk.CTkLabel(fields_frame, text="Reorder Level:").grid(row=8, column=0, sticky="w", padx=10, pady=5)
        self.reorder_entry = ctk.CTkEntry(fields_frame, width=300)
        self.reorder_entry.grid(row=8, column=1, padx=10, pady=5)

        # Barcode
        ctk.CTkLabel(fields_frame, text="Barcode:").grid(row=9, column=0, sticky="w", padx=10, pady=5)
        self.barcode_entry = ctk.CTkEntry(fields_frame, width=300)
        self.barcode_entry.grid(row=9, column=1, padx=10, pady=5)
        self.barcode_entry.configure(state="readonly")



        # Active status
        self.active_var = ctk.BooleanVar(value=True)
        self.active_checkbox = ctk.CTkCheckBox(fields_frame, text="Active", variable=self.active_var)
        self.active_checkbox.grid(row=10, column=1, sticky="w", padx=10, pady=5)

        # Buttons
        button_frame = ctk.CTkFrame(fields_frame)
        button_frame.grid(row=11, column=0, columnspan=2, pady=20)

        save_btn = ctk.CTkButton(
            button_frame,
            text="Save",
            command=lambda: self.save_product(product_data),
            width=100
        )
        save_btn.pack(side="left", padx=10, pady=10)

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.form_window.destroy,
            width=100
        )
        cancel_btn.pack(side="left", padx=10, pady=10)

        if product_data is None:
            next_id = db.get_next_product_id()

            self.product_id_entry.configure(state="normal")
            self.product_id_entry.delete(0, "end")

            if next_id:
                self.product_id_entry.insert(0, str(next_id))

            self.product_id_entry.configure(state="readonly")

            generated_barcode = self.generate_barcode()  # optional
            self.barcode_entry.configure(state="normal")
            self.barcode_entry.delete(0, "end")
            self.barcode_entry.insert(0, generated_barcode)
            self.barcode_entry.configure(state="readonly")
        else:
            # Existing product edit: populate fields from product_data
            self.fill_form(product_data, categories, suppliers)

    def fill_form(self, product_data, categories, suppliers):
        """Fill form with existing product data"""
        # SKU
        self.product_id_entry.configure(state="normal")
        self.product_id_entry.delete(0, "end")
        self.product_id_entry.insert(
            0,
            str(product_data["product_id"])
        )
        self.product_id_entry.configure(state="readonly")

        # SKU
        self.sku_entry.delete(0, "end")
        self.sku_entry.insert(
            0,
            product_data["sku"]
        )
        self.name_entry.insert(0, product_data['name'])

        # Set category
        if product_data['category_id']:
            category_name = next((cat['name'] for cat in categories if cat['category_id'] == product_data['category_id']), '')
            self.category_combo.set(category_name)

        # Set supplier
        if product_data['supplier_id']:
            supplier_name = next((sup['name'] for sup in suppliers if sup['supplier_id'] == product_data['supplier_id']), '')
            self.supplier_combo.set(supplier_name)

        self.unit_price_entry.insert(0, str(product_data['unit_price']))
        self.cost_price_entry.insert(0, str(product_data['cost_price']))
        self.stock_entry.insert(0, str(product_data['stock_qty']))
        self.reorder_entry.insert(0, str(product_data['reorder_level']))
        # Barcode
        self.barcode_entry.configure(state="normal")
        self.barcode_entry.insert(0, product_data['barcode'] or '')
        self.barcode_entry.configure(state="readonly")
        self.active_var.set(product_data['is_active'])

    def save_product(self, existing_product=None):
        """Save product (add or update)"""
        try:
            # Validate required fields
            if not all([self.sku_entry.get(), self.name_entry.get()]):
                messagebox.showerror("Error", "SKU and Name are required")
                return

            # Get form data
            categories = db.get_all_categories()
            suppliers = db.get_all_suppliers()

            category_id = None
            if self.category_combo.get():
                category_id = next((cat['category_id'] for cat in categories if cat['name'] == self.category_combo.get()), None)

            supplier_id = None
            if self.supplier_combo.get():
                supplier_id = next((sup['supplier_id'] for sup in suppliers if sup['name'] == self.supplier_combo.get()), None)

            product_data = {
                'sku': self.sku_entry.get(),
                'name': self.name_entry.get(),
                'category_id': category_id,
                'supplier_id': supplier_id,
                'unit_price': float(self.unit_price_entry.get() or 0),
                'cost_price': float(self.cost_price_entry.get() or 0),
                'stock_qty': int(self.stock_entry.get() or 0),
                'reorder_level': int(self.reorder_entry.get() or 0),
                'barcode': self.barcode_entry.get() or None,
                'is_active': self.active_var.get()
            }

            # Save product
            if existing_product:
                success = db.update_product(existing_product['product_id'], product_data)
                new_id = existing_product['product_id']
            else:
                new_id = db.add_product(product_data)
                success = new_id is not None

            if success:
                messagebox.showinfo("Success", f"Product saved successfully (ID #{new_id})")
                self.form_window.destroy()
                self.load_products()
            else:
                messagebox.showerror("Error", "Failed to save product")
        except ValueError as e:
            messagebox.showerror("Error", f"Please enter valid numeric values: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving product: {e}")

    def load_products(self):
        """Load products into table"""
        # Clear existing data
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)

        # Load products
        products = db.get_all_products()

        for product in products:
            status = "Active" if product['is_active'] else "Inactive"

            values = (
                product['product_id'],
                product['sku'],
                product['name'],
                product.get('category_name', ''),
                product.get('supplier_name', ''),
                f"₹{product['unit_price']:,.2f}",
                product['stock_qty'],
                product['reorder_level'],
                status
            )

            # Color code low stock items
            item_id = self.products_tree.insert("", "end", values=values)
            if product['stock_qty'] <= product['reorder_level']:
                self.products_tree.set(item_id, "Stock", f"{product['stock_qty']} ⚠️")

    def add_product(self):
        """Show add product form"""
        self.show_product_form()

    def edit_product(self):
        """Edit selected product"""
        selection = self.products_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a product to edit")
            return

        # Get selected product ID
        item = selection[0]
        product_id = self.products_tree.item(item)['values'][0]

        # Get product data
        product_data = db.get_product_by_id(product_id)
        if product_data:
            self.show_product_form(product_data)

    def delete_product(self):
        """Delete selected product"""
        selection = self.products_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a product to delete")
            return

        # Confirm deletion
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this product?"):
            item = selection[0]
            product_id = self.products_tree.item(item)['values'][0]

            if db.delete_product(product_id):
                messagebox.showinfo("Success", "Product deleted successfully")
                self.load_products()
            else:
                messagebox.showerror("Error", "Failed to delete product")

    def search_products(self):
        """Search products"""
        search_term = self.search_entry.get().strip()
        if not search_term:
            self.load_products()
            return

        # Clear existing data
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)

        # Search and load results
        products = db.search_products(search_term)

        for product in products:
            status = "Active" if product['is_active'] else "Inactive"

            values = (
                product['product_id'],
                product['sku'],
                product['name'],
                product.get('category_name', ''),
                product.get('supplier_name', ''),
                f"₹{product['unit_price']:,.2f}",
                product['stock_qty'],
                product['reorder_level'],
                status
            )

            item_id = self.products_tree.insert("", "end", values=values)
            if product['stock_qty'] <= product['reorder_level']:
                self.products_tree.set(item_id, "Stock", f"{product['stock_qty']} ⚠️")

    def on_search(self, event):
        """Handle search as user types"""
        # Optional: implement real-time search
        pass
