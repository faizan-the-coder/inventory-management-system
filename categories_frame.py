
import customtkinter as ctk
import tkinter.messagebox as messagebox
import tkinter.ttk as ttk
import db

class CategoriesFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.create_widgets()
        self.load_categories()

    def create_widgets(self):
        """Create category management widgets"""
        # Title and controls
        self.title_frame = ctk.CTkFrame(self)
        self.title_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        self.title_label = ctk.CTkLabel(
            self.title_frame,
            text="Category Management",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(side="left", padx=20, pady=10)

        self.add_btn = ctk.CTkButton(
            self.title_frame,
            text="Add Category",
            command=self.add_category,
            width=120
        )
        self.add_btn.pack(side="right", padx=20, pady=10)

        # Categories table
        self.create_categories_table()

    def create_categories_table(self):
        """Create categories table"""
        self.table_frame = ctk.CTkFrame(self)
        self.table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)

        # Create Treeview for categories table
        columns = ("ID", "Name", "Description", "Created Date")
        self.categories_tree = ttk.Treeview(self.table_frame, columns=columns, show="headings", height=15)

        # Configure column headings and widths
        column_widths = {"ID": 50, "Name": 200, "Description": 400, "Created Date": 150}

        for col in columns:
            self.categories_tree.heading(col, text=col)
            self.categories_tree.column(col, width=column_widths.get(col, 100), minwidth=50)

        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.categories_tree.yview)
        h_scrollbar = ttk.Scrollbar(self.table_frame, orient="horizontal", command=self.categories_tree.xview)
        self.categories_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Grid the treeview and scrollbars
        self.categories_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        # Action buttons frame
        self.actions_frame = ctk.CTkFrame(self.table_frame)
        self.actions_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        self.edit_btn = ctk.CTkButton(
            self.actions_frame,
            text="Edit Selected",
            command=self.edit_category,
            width=120
        )
        self.edit_btn.pack(side="left", padx=10, pady=10)

        self.delete_btn = ctk.CTkButton(
            self.actions_frame,
            text="Delete Selected",
            command=self.delete_category,
            width=120,
            fg_color="red",
            hover_color="darkred"
        )
        self.delete_btn.pack(side="left", padx=(5, 10), pady=10)

        self.refresh_btn = ctk.CTkButton(
            self.actions_frame,
            text="Refresh",
            command=self.load_categories,
            width=80
        )
        self.refresh_btn.pack(side="right", padx=10, pady=10)

        # Bind double-click to edit
        self.categories_tree.bind("<Double-1>", lambda e: self.edit_category())

    def show_category_form(self, category_data=None):
        """Show category add/edit form"""
        # Create form window
        form_window = ctk.CTkToplevel(self)
        form_window.title("Add Category" if category_data is None else "Edit Category")
        form_window.geometry("380x350")
        form_window.transient(self)
        form_window.grab_set()

        # Form fields
        fields_frame = ctk.CTkFrame(form_window)
        fields_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Category ID
        ctk.CTkLabel(
            fields_frame,
            text="Category ID:"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=10,
            pady=10
        )

        category_id_entry = ctk.CTkEntry(
            fields_frame,
            width=200
        )
        category_id_entry.grid(
            row=0,
            column=1,
            padx=10,
            pady=10
        )
        category_id_entry.configure(state="readonly")

        # Name
        ctk.CTkLabel(fields_frame, text="Name:").grid(row=1, column=0, sticky="w", padx=10, pady=10)
        name_entry = ctk.CTkEntry(fields_frame, width=200)
        name_entry.grid(row=1, column=1, padx=10, pady=10)

        # Description
        ctk.CTkLabel(fields_frame, text="Description:").grid(row=2, column=0, sticky="nw", padx=10, pady=10)
        description_text = ctk.CTkTextbox(fields_frame, width=200, height=100)
        description_text.grid(row=2, column=1, padx=10, pady=10)

        if category_data is None:

            next_id = db.get_next_category_id()

            category_id_entry.configure(state="normal")
            category_id_entry.delete(0, "end")

            if next_id:
                category_id_entry.insert(0, str(next_id))

            category_id_entry.configure(state="readonly")

        # Fill form if editing
        if category_data:
            category_id_entry.configure(state="normal")
            category_id_entry.insert(
                0,
                str(category_data['category_id'])
            )
            category_id_entry.configure(state="readonly")

            name_entry.insert(
                0,
                category_data['name']
            )

            description_text.insert(
                "1.0",
                category_data['description'] or ''
            )
        # Buttons
        button_frame = ctk.CTkFrame(fields_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)

        def save_category():
            name = name_entry.get().strip()
            description = description_text.get("1.0", "end-1c").strip()

            if not name:
                messagebox.showerror("Error", "Category name is required")
                return

            try:
                if category_data:
                    success = db.update_category(category_data['category_id'], name, description)
                else:
                    success = db.add_category(name, description)

                if success:
                    messagebox.showinfo("Success", "Category saved successfully")
                    form_window.destroy()
                    self.load_categories()
                else:
                    messagebox.showerror("Error", "Failed to save category")
            except Exception as e:
                messagebox.showerror("Error", f"Error saving category: {e}")

        save_btn = ctk.CTkButton(
            button_frame,
            text="Save",
            command=save_category,
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

    def load_categories(self):
        """Load categories into table"""
        # Clear existing data
        for item in self.categories_tree.get_children():
            self.categories_tree.delete(item)

        # Load categories
        categories = db.get_all_categories()

        for category in categories:
            values = (
                category['category_id'],
                category['name'],
                category['description'] or '',
                category['created_at'].strftime('%Y-%m-%d') if category['created_at'] else ''
            )
            self.categories_tree.insert("", "end", values=values)

    def add_category(self):
        """Show add category form"""
        self.show_category_form()

    def edit_category(self):
        """Edit selected category"""
        selection = self.categories_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a category to edit")
            return

        # Get selected category data
        item = selection[0]
        values = self.categories_tree.item(item)['values']

        category_data = {
            'category_id': values[0],
            'name': values[1],
            'description': values[2]
        }

        self.show_category_form(category_data)

    def delete_category(self):
        """Delete selected category"""
        selection = self.categories_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a category to delete")
            return

        # Confirm deletion
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this category?\n\nNote: You cannot delete categories that have products."):
            item = selection[0]
            category_id = self.categories_tree.item(item)['values'][0]

            if db.delete_category(category_id):
                messagebox.showinfo("Success", "Category deleted successfully")
                self.load_categories()
            else:
                messagebox.showerror("Error", "Cannot delete category. It may have products associated with it.")
