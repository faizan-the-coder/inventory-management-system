
import customtkinter as ctk
import tkinter.messagebox as messagebox
import tkinter.ttk as ttk
from tkinter import filedialog
import db
import csv
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from billing_frame import BillingFrame

class SalesFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.create_widgets()
        self.load_sales()

    def create_widgets(self):
        """Create sales management widgets"""
        # Title
        self.title_label = ctk.CTkLabel(
            self,
            text="Sales History",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=10)

        # Filters
        self.create_filters()

        # Sales table
        self.create_sales_table()

        # Summary
        self.create_summary()



    def edit_invoice(self, sale_id, details_window):

        self.parent.edit_sale_id = sale_id

        details_window.destroy()

        self.parent.show_frame(BillingFrame)



    def create_filters(self):
        """Create filter controls"""
        filters_frame = ctk.CTkFrame(self)
        filters_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

        # Date filters
        ctk.CTkLabel(filters_frame, text="From Date:").grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.from_date = ctk.CTkEntry(filters_frame, placeholder_text="YYYY-MM-DD", width=120)
        self.from_date.grid(row=0, column=1, padx=(0, 10), pady=10)

        ctk.CTkLabel(filters_frame, text="To Date:").grid(row=0, column=2, padx=10, pady=10, sticky="w")

        self.to_date = ctk.CTkEntry(filters_frame, placeholder_text="YYYY-MM-DD", width=120)
        self.to_date.grid(row=0, column=3, padx=(0, 10), pady=10)

        # Buttons
        filter_btn = ctk.CTkButton(
            filters_frame,
            text="Filter",
            command=self.filter_sales,
            width=80
        )
        filter_btn.grid(row=0, column=4, padx=10, pady=10)

        clear_btn = ctk.CTkButton(
            filters_frame,
            text="Clear",
            command=self.clear_filters,
            width=60
        )
        clear_btn.grid(row=0, column=5, padx=(5, 10), pady=10)

        # Quick filters
        today_btn = ctk.CTkButton(
            filters_frame,
            text="Today",
            command=self.filter_today,
            width=60
        )
        today_btn.grid(row=0, column=6, padx=(5, 10), pady=10)

        week_btn = ctk.CTkButton(
            filters_frame,
            text="This Week",
            command=self.filter_week,
            width=80
        )
        week_btn.grid(row=0, column=7, padx=(5, 10), pady=10)

        month_btn = ctk.CTkButton(
            filters_frame,
            text="This Month",
            command=self.filter_month,
            width=80
        )
        month_btn.grid(row=0, column=8, padx=(5, 10), pady=10)

        # Export button
        export_btn = ctk.CTkButton(
            filters_frame,
            text="Export CSV",
            command=self.export_csv,
            width=80
        )
        export_btn.grid(row=0, column=9, padx=(20, 10), pady=10)

    def create_sales_table(self):
        """Create sales table"""
        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Create Treeview
        columns = ("Sale ID", "Date", "Employee", "Items", "Subtotal", "Tax", "Total","Profit")
        self.sales_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        # Configure columns
        column_widths = {"Sale ID": 80, "Date": 120, "Employee": 120, "Items": 60, 
                        "Subtotal": 100, "Tax": 80, "Total": 100,"Profit":100}

        for col in columns:
            self.sales_tree.heading(col, text=col)
            self.sales_tree.column(col, width=column_widths.get(col, 100), minwidth=50)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.sales_tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=self.sales_tree.xview)
        self.sales_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        self.sales_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        # Bind double-click to view details
        self.sales_tree.bind("<Double-1>", self.view_sale_details)

    def create_summary(self):
        """Create sales summary"""
        summary_frame = ctk.CTkFrame(self)
        summary_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)

        # Summary labels
        ctk.CTkLabel(summary_frame, text="Summary:", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=20, pady=10)

        self.total_sales_label = ctk.CTkLabel(summary_frame, text="Total Sales: ₹0.00", font=ctk.CTkFont(size=14))
        self.total_sales_label.pack(side="left", padx=20, pady=10)

        self.total_profit_label = ctk.CTkLabel(summary_frame, text="Total Profit: ₹0.00", font=ctk.CTkFont(size=14))
        self.total_profit_label.pack(side="left", padx=20, pady=10)

        self.transaction_count_label = ctk.CTkLabel(summary_frame, text="Transactions: 0", font=ctk.CTkFont(size=14))
        self.transaction_count_label.pack(side="left", padx=20, pady=10)

        self.avg_sale_label = ctk.CTkLabel(summary_frame, text="Avg Sale: ₹0.00", font=ctk.CTkFont(size=14))
        self.avg_sale_label.pack(side="left", padx=20, pady=10)

        graph_btn = ctk.CTkButton(summary_frame, text="View Graph", command=self.show_sales_graph)
        graph_btn.pack(side="right", padx=20)



    def show_sales_graph(self):
        # Grab date inputs
        from_date_str = self.from_date.get().strip()
        to_date_str = self.to_date.get().strip()
        start_date = None
        end_date = None
        try:
            if from_date_str:
                start_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            if to_date_str:
                end_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
        except ValueError:
            messagebox.showerror("Error", "Invalid date format, please use YYYY-MM-DD")
            return
        # Fetch sales data from db
        sales_data = db.get_sales_data_for_graph(start_date,end_date)  # Your DB method

        # Prepare data for plotting
        dates = [entry['date'].strftime('%Y-%m-%d') for entry in sales_data]
        totals = [float(entry['total']) for entry in sales_data]

        # Create figure and axes
        figure, ax = plt.subplots(figsize=(8, 4))
        ax.plot(dates, totals, marker='o', linestyle='-')
        ax.set_title('Sales Over Time')
        ax.set_xlabel('Date')
        ax.set_ylabel('Total Sales')
        ax.grid(True)
        figure.autofmt_xdate()

        # Create Tkinter window for the graph
        graph_win = ctk.CTkToplevel()
        graph_win.title("Sales Graph")
        graph_win.geometry("900x500")
        graph_win.grab_set()
        # graph_win.deiconify()  # Ensure window is not minimized
        # graph_win.lift()  # Bring to front
        # graph_win.focus_force()  # Focus on this window

        # Create Matplotlib canvas and embed inside Tk window
        canvas = FigureCanvasTkAgg(figure, master=graph_win)
        canvas.draw()
        canvas.get_tk_widget().pack(side='top', fill='both', expand=1)

        # Add Matplotlib's interactive toolbar for zoom, pan, save
        toolbar = NavigationToolbar2Tk(canvas, graph_win)
        toolbar.update()
        toolbar.pack(side='top', fill='x')

        # Optional: handle closing matplotlib loop on window close
        def on_close():
            plt.close(figure)
            graph_win.destroy()

        graph_win.protocol("WM_DELETE_WINDOW", on_close)

    def load_sales(self, start_date=None, end_date=None):
        """Load sales data"""
        # Clear existing data
        for item in self.sales_tree.get_children():
            self.sales_tree.delete(item)

        # Get sales data
        sales = db.get_sales_history(start_date, end_date)

        total_amount = 0
        total_profit = 0  # Initialize total profit accumulator
        transaction_count = len(sales)

        for sale in sales:
            # Get item count for this sale
            item_count = sale.get('items_count', 0)
            profit = sale.get("profit", 0)

            values = (
                sale['sale_id'],
                sale['datetime'].strftime('%Y-%m-%d %H:%M'),
                sale['employee_name'],
                item_count,
                f"₹{sale['subtotal']:.2f}",
                f"₹{sale['tax']:.2f}",
                f"₹{sale['total']:.2f}",
                f"₹{profit:.2f}"  # Display profit here
            )
            self.sales_tree.insert("", "end", values=values)

            total_amount += sale['total']
            total_profit += profit  # Accumulate total profit

        # Update summary
        avg_sale = total_amount / transaction_count if transaction_count > 0 else 0

        self.total_sales_label.configure(text=f"Total Sales: ₹{total_amount:,.2f}")
        self.total_profit_label.configure(text=f"Total Profit: ₹{total_profit:,.2f}")
        self.transaction_count_label.configure(text=f"Transactions: {transaction_count}")
        self.avg_sale_label.configure(text=f"Avg Sale: ₹{avg_sale:,.2f}")

    def filter_sales(self):
        """Filter sales by date range"""
        from_date_str = self.from_date.get().strip()
        to_date_str = self.to_date.get().strip()

        start_date = None
        end_date = None

        try:
            if from_date_str:
                start_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            if to_date_str:
                end_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
        except ValueError:
            messagebox.showerror("Error", "Please enter dates in YYYY-MM-DD format")
            return

        self.load_sales(start_date, end_date)

    def clear_filters(self):
        """Clear filters and reload all sales"""
        self.from_date.delete(0, 'end')
        self.to_date.delete(0, 'end')
        self.load_sales()

    def filter_today(self):
        """Filter today's sales"""
        today = datetime.now().date()
        self.from_date.delete(0, 'end')
        self.from_date.insert(0, today.strftime('%Y-%m-%d'))
        self.to_date.delete(0, 'end')
        self.to_date.insert(0, today.strftime('%Y-%m-%d'))
        self.filter_sales()

    def filter_week(self):
        """Filter this week's sales"""
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())

        self.from_date.delete(0, 'end')
        self.from_date.insert(0, week_start.strftime('%Y-%m-%d'))
        self.to_date.delete(0, 'end')
        self.to_date.insert(0, today.strftime('%Y-%m-%d'))
        self.filter_sales()

    def filter_month(self):
        """Filter this month's sales"""
        today = datetime.now().date()
        month_start = today.replace(day=1)

        self.from_date.delete(0, 'end')
        self.from_date.insert(0, month_start.strftime('%Y-%m-%d'))
        self.to_date.delete(0, 'end')
        self.to_date.insert(0, today.strftime('%Y-%m-%d'))
        self.filter_sales()

    def view_sale_details(self, event):
        """View detailed sale information"""

        selection = self.sales_tree.selection()
        if not selection:
            return

        sale_id = self.sales_tree.item(selection[0])['values'][0]

        sale = db.get_sale(sale_id)

        # Create window
        details_window = ctk.CTkToplevel(self)
        details_window.title(f"🧾 Sale Details - {sale_id}")
        details_window.geometry("800x700")
        details_window.transient(self)
        details_window.grab_set()

        # =========================
        # Header
        # =========================
        header_frame = ctk.CTkFrame(
            details_window,
            corner_radius=12,
            fg_color="#2B2B2B"
        )
        header_frame.pack(
            fill="x",
            padx=20,
            pady=(20, 10)
        )

        header_label = ctk.CTkLabel(
            header_frame,
            text=f"🧾 Sale Details - Invoice #{sale_id}",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        )
        header_label.pack(
            side="left",
            padx=15,
            pady=12
        )

        edit_btn = ctk.CTkButton(
            header_frame,
            text="✏ Edit Invoice",
            command=lambda: self.edit_invoice(
                sale_id,
                details_window
            ),
            width=150,
            height=38,
            fg_color="#0EA5A4",
            hover_color="#0B8C8A",
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            )
        )
        edit_btn.pack(
            side="right",
            padx=15,
            pady=10
        )

        # =========================
        # Main Container
        # =========================
        main_frame = ctk.CTkFrame(
            details_window,
            corner_radius=15
        )
        main_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 15)
        )

        values = self.sales_tree.item(selection[0])['values']

        # =========================
        # Top Info Section
        # =========================
        top_frame = ctk.CTkFrame(
            main_frame,
            fg_color="transparent"
        )
        top_frame.pack(
            fill="x",
            padx=10,
            pady=10
        )

        top_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # -------------------------
        # Sale Information
        # -------------------------
        sale_frame = ctk.CTkFrame(top_frame)
        sale_frame.grid(
            row=0,
            column=0,
            padx=5,
            sticky="nsew"
        )

        ctk.CTkLabel(
            sale_frame,
            text="Sale Information",
            font=ctk.CTkFont(
                size=15,
                weight="bold"
            )
        ).pack(anchor="w", padx=10, pady=(10, 5))

        sale_info = [
            ("Sale ID", values[0]),
            ("Date", values[1]),
            ("Employee", values[2]),
            ("Items", values[3])
        ]

        for label, value in sale_info:
            ctk.CTkLabel(
                sale_frame,
                text=f"{label}: {value}",
                anchor="w"
            ).pack(
                fill="x",
                padx=10,
                pady=2
            )

        # -------------------------
        # Customer Information
        # -------------------------
        customer_frame = ctk.CTkFrame(top_frame)
        customer_frame.grid(
            row=0,
            column=1,
            padx=5,
            sticky="nsew"
        )

        ctk.CTkLabel(
            customer_frame,
            text="Customer Information",
            font=ctk.CTkFont(
                size=15,
                weight="bold"
            )
        ).pack(anchor="w", padx=10, pady=(10, 5))

        customer_name = (
            sale.get("customer_name")
            if sale and sale.get("customer_name")
            else "Walk-in Customer"
        )

        customer_phone = (
            sale.get("customer_phone")
            if sale and sale.get("customer_phone")
            else "-"
        )

        customer_email = (
            sale.get("customer_email")
            if sale and sale.get("customer_email")
            else "Not Provided"
        )

        customer_info = [
            ("Name", customer_name),
            ("Phone", customer_phone),
            ("Email", customer_email)
        ]

        for label, value in customer_info:
            ctk.CTkLabel(
                customer_frame,
                text=f"{label}: {value}",
                anchor="w"
            ).pack(
                fill="x",
                padx=10,
                pady=2
            )

        # -------------------------
        # Financial Summary
        # -------------------------
        summary_frame = ctk.CTkFrame(top_frame)
        summary_frame.grid(
            row=0,
            column=2,
            padx=5,
            sticky="nsew"
        )

        ctk.CTkLabel(
            summary_frame,
            text="Financial Summary",
            font=ctk.CTkFont(
                size=15,
                weight="bold"
            )
        ).pack(anchor="w", padx=10, pady=(10, 5))

        financial_info = [
            ("Subtotal", f"{values[4]}"),
            ("Tax", f"{values[5]}"),
            ("Total", f"{values[6]}"),
            ("Profit", f"{values[7]}")
        ]

        for label, value in financial_info:
            ctk.CTkLabel(
                summary_frame,
                text=f"{label}: {value}",
                anchor="w"
            ).pack(
                fill="x",
                padx=10,
                pady=2
            )

        # =========================
        # Sale Items Label
        # =========================
        ctk.CTkLabel(
            main_frame,
            text="🛍 Sale Items",
            font=ctk.CTkFont(
                size=16,
                weight="bold"
            )
        ).pack(
            anchor="w",
            padx=15,
            pady=(5, 5)
        )

        # =========================
        # Tree Frame
        # =========================
        tree_frame = ctk.CTkFrame(
            main_frame,
            corner_radius=10
        )
        tree_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(0, 10)
        )

        columns = (
            "Product Name",
            "Quantity",
            "Unit Price",
            "Line Total"
        )

        items_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings"
        )

        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background="#2E2E2E",
            foreground="white",
            rowheight=28,
            fieldbackground="#2E2E2E"
        )

        style.configure(
            "Treeview.Heading",
            background="#404040",
            foreground="white",
            font=("Segoe UI", 10, "bold")
        )

        for col in columns:
            items_tree.heading(col, text=col)
            items_tree.column(
                col,
                anchor="center",
                width=180
            )

        y_scroll = ttk.Scrollbar(
            tree_frame,
            orient="vertical",
            command=items_tree.yview
        )

        items_tree.configure(
            yscrollcommand=y_scroll.set
        )

        y_scroll.pack(
            side="right",
            fill="y"
        )

        items_tree.pack(
            fill="both",
            expand=True
        )

        sale_items = db.get_sale_items(sale_id)

        for item in sale_items:
            items_tree.insert(
                "",
                "end",
                values=(
                    item.get("product_name", ""),
                    item.get("qty", 0),
                    f"₹{item.get('unit_price', 0):.2f}",
                    f"₹{item.get('line_total', 0):.2f}"
                )
            )


    def export_csv(self):
        """Export sales data to CSV"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Sales Data"
        )

        if not filename:
            return

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)

                # Write headers
                headers = ["Sale ID", "Date", "Employee", "Items", "Subtotal", "Tax", "Total","Profit"]
                writer.writerow(headers)

                # Write data
                for item in self.sales_tree.get_children():
                    values = self.sales_tree.item(item)['values']
                    writer.writerow(values)

            messagebox.showinfo("Success", f"Sales data exported to {filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {e}")
