import pymysql
import datetime
from config import DB_CONFIG, DATABASE_NAME
import auth


def get_connection():
    """Get database connection"""
    return pymysql.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DATABASE_NAME,
        charset=DB_CONFIG['charset'],
        autocommit=True
    )


def initialize_database():
    """Initialize database and tables if they don't exist"""
    try:
        # First, connect without specifying database to create it
        connection = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            charset=DB_CONFIG['charset']
        )

        with connection.cursor() as cursor:
            # Create database if not exists
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME}")
            cursor.execute(f"USE {DATABASE_NAME}")

            # Create tables
            create_tables(cursor)

            # Insert seed data
            insert_seed_data(cursor)

        connection.commit()
        print("Database initialized successfully")

    except Exception as e:
        print(f"Database initialization error: {e}")
    finally:
        if 'connection' in locals():
            connection.close()


def create_tables(cursor):
    """Create all required tables"""

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            role ENUM('Admin', 'Employee', 'Supplier') NOT NULL,
            password_hash VARCHAR(64) NOT NULL,
            salt VARCHAR(32) NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            phone VARCHAR(15),
            email VARCHAR(100) UNIQUE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Categories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            category_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Suppliers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            supplier_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            contact_person VARCHAR(100),
            phone VARCHAR(15),
            email VARCHAR(100),
            address TEXT,
            gstin VARCHAR(15),
            notes TEXT,
            user_id INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # Products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id INT AUTO_INCREMENT PRIMARY KEY,
            sku VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            category_id INT,
            supplier_id INT,
            unit_price DECIMAL(10,2) DEFAULT 0.00,
            cost_price DECIMAL(10,2) DEFAULT 0.00,
            stock_qty INT DEFAULT 0,
            reorder_level INT DEFAULT 10,
            barcode VARCHAR(50) UNIQUE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(category_id),
            FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
        )
    """)

    # Sales table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            sale_id INT AUTO_INCREMENT PRIMARY KEY,
            datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            employee_id INT NOT NULL,
            customer_name VARCHAR(100),
            customer_phone VARCHAR(20),
            customer_email VARCHAR(255),
            subtotal DECIMAL(10,2) DEFAULT 0.00,
            tax DECIMAL(10,2) DEFAULT 0.00,
            total DECIMAL(10,2) DEFAULT 0.00,
            profit DECIMAL(10,2) DEFAULT 0.00,
            FOREIGN KEY (employee_id) REFERENCES users(user_id)
        )
    """)

    # Sale items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sale_items (
            item_id INT AUTO_INCREMENT PRIMARY KEY,
            sale_id INT NOT NULL,
            product_id INT NOT NULL,
            qty INT NOT NULL,
            unit_price DECIMAL(10,2) NOT NULL,
            line_total DECIMAL(10,2) NOT NULL,
            FOREIGN KEY (sale_id) REFERENCES sales(sale_id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)

    # Purchase orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_orders (
            po_id INT AUTO_INCREMENT PRIMARY KEY,
            supplier_id INT NOT NULL,
            status ENUM('Ordered', 'Received', 'Cancelled') NOT NULL DEFAULT 'Ordered',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expected_date DATE,
            total_amount DECIMAL(10,2) DEFAULT 0.00,
            notes TEXT,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
        )
    """)

    # Purchase items table  
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_items (
            item_id INT AUTO_INCREMENT PRIMARY KEY,
            po_id INT NOT NULL,
            product_id INT NOT NULL,
            qty INT NOT NULL,
            unit_cost DECIMAL(10,2) NOT NULL,
            line_total DECIMAL(10,2) NOT NULL,
            FOREIGN KEY (po_id) REFERENCES purchase_orders(po_id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shop_info (
    id INT PRIMARY KEY CHECK (id = 1),
    name VARCHAR(255),
    address1 VARCHAR(255),
    address2 VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    gstin VARCHAR(50),
    upi_id VARCHAR(255),
    upi_name VARCHAR(255)
);

    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS supplier_users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  supplier_id INT NOT NULL,
  UNIQUE KEY unique_user_supplier (user_id, supplier_id),
  FOREIGN KEY (user_id) REFERENCES users(user_id),
  FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

    """)


def get_all_users():
    try:
        connection = get_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(
                "SELECT user_id, username, role, full_name, phone, email, is_active, created_at FROM users ORDER BY user_id DESC")
            return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching users: {e}")
        return []
    finally:
        if 'connection' in locals():
            connection.close()


def update_user(user_id, username, role, full_name, phone, email, is_active):
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            query = """
            UPDATE users
            SET role = %s, full_name = %s, phone = %s, email = %s, is_active = %s
            WHERE user_id = %s
            """
            cursor.execute(query, (role, full_name, phone, email, is_active, user_id))
            return True
    except Exception as e:
        print(f"Error updating user: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()


def insert_seed_data(cursor):
    """Insert default data"""

    # Check if seed data already exists
    cursor.execute("SELECT COUNT(*) as count FROM users")
    result = cursor.fetchone()
    if result[0] > 0:
        return  # Seed data already exists

    # Create default users with hashed passwords
    default_users = [
        ('admin', 'Admin@123', 'Admin', 'System Administrator', '9999999999', 'admin@company.com'),
        ('emp', 'Emp@123', 'Employee', 'Store Employee', '8888888888', 'emp@company.com'),
        ('supp', 'Supp@123', 'Supplier', 'Default Supplier', '7777777777', 'supp@company.com')
    ]

    for username, password, role, full_name, phone, email in default_users:
        salt = auth.generate_salt()
        password_hash = auth.hash_password(password, salt)
        cursor.execute("""
            INSERT INTO users (username, role, password_hash, salt, full_name, phone, email, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
        """, (username, role, password_hash, salt, full_name, phone, email))

    # Default categories
    categories = [
        ('Electronics', 'Electronic items and gadgets'),
        ('Clothing', 'Apparel and accessories'),
        ('Food & Beverages', 'Food items and drinks'),
        ('Stationery', 'Office and school supplies'),
        ('Home & Garden', 'Home improvement and garden items')
    ]

    for name, description in categories:
        cursor.execute("INSERT INTO categories (name, description) VALUES (%s, %s)", (name, description))

    # Default supplier
    cursor.execute("""
        INSERT INTO suppliers (name, contact_person, phone, email, address, user_id)
        VALUES ('ABC Suppliers Ltd', 'John Doe', '9876543210', 'john@abcsuppliers.com', 
                '123 Business St, City', 3)
    """)

    # Default products
    products = [
        ('SKU001', 'Laptop Computer', 1, 1, 45000.00, 42000.00, 10, 5, 'BC001'),
        ('SKU002', 'Cotton T-Shirt', 2, 1, 599.00, 350.00, 50, 10, 'BC002'),
        ('SKU003', 'Coffee Mug', 5, 1, 299.00, 200.00, 25, 5, 'BC003'),
        ('SKU004', 'Notebook Set', 4, 1, 150.00, 100.00, 100, 20, 'BC004')
    ]

    for sku, name, cat_id, sup_id, unit_price, cost_price, stock, reorder, barcode in products:
        cursor.execute("""
            INSERT INTO products (sku, name, category_id, supplier_id, unit_price, 
                                cost_price, stock_qty, reorder_level, barcode, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
        """, (sku, name, cat_id, sup_id, unit_price, cost_price, stock, reorder, barcode))


# CRUD Functions for Products
def get_all_products():
    """Get all products with category and supplier info"""
    try:
        connection = get_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            query = """
                SELECT p.*, c.name as category_name, s.name as supplier_name
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.category_id
                LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
                WHERE p.is_active = TRUE
                ORDER BY p.product_id DESC
            """
            cursor.execute(query)
            return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching products: {e}")
        return []
    finally:
        if 'connection' in locals():
            connection.close()


def get_product_by_id(product_id):
    """Get product by ID"""
    try:
        connection = get_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            query = "SELECT * FROM products WHERE product_id = %s"
            cursor.execute(query, (product_id,))
            return cursor.fetchone()
    except Exception as e:
        print(f"Error fetching product: {e}")
        return None
    finally:
        if 'connection' in locals():
            connection.close()


def search_products(search_term):
    """Search products by name, SKU, or barcode"""
    try:
        connection = get_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            query = """
                SELECT p.*, c.name as category_name, s.name as supplier_name
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.category_id
                LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
                WHERE p.is_active = TRUE AND (
                    p.name LIKE %s OR p.sku LIKE %s OR p.barcode LIKE %s
                )
                ORDER BY p.product_id DESC
            """
            search_pattern = f"%{search_term}%"
            cursor.execute(query, (search_pattern, search_pattern, search_pattern))
            return cursor.fetchall()
    except Exception as e:
        print(f"Error searching products: {e}")
        return []
    finally:
        if 'connection' in locals():
            connection.close()


def add_product(product_data):
    """Add new product"""
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            query = """
                INSERT INTO products (sku, name, category_id, supplier_id, unit_price, 
                                    cost_price, stock_qty, reorder_level, barcode, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                product_data['sku'], product_data['name'], product_data['category_id'],
                product_data['supplier_id'], product_data['unit_price'], product_data['cost_price'],
                product_data['stock_qty'], product_data['reorder_level'], product_data['barcode'],
                product_data['is_active']
            ))
            return cursor.lastrowid   # <-- the real, guaranteed-correct ID
    except Exception as e:
        print(f"Error adding product: {e}")
        return None
    finally:
        if 'connection' in locals():
            connection.close()


def update_product(product_id, product_data):
    """Update existing product"""
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            query = """
                UPDATE products SET sku = %s, name = %s, category_id = %s, supplier_id = %s,
                                  unit_price = %s, cost_price = %s, stock_qty = %s, 
                                  reorder_level = %s, barcode = %s, is_active = %s
                WHERE product_id = %s
            """
            cursor.execute(query, (
                product_data['sku'], product_data['name'], product_data['category_id'],
                product_data['supplier_id'], product_data['unit_price'], product_data['cost_price'],
                product_data['stock_qty'], product_data['reorder_level'], product_data['barcode'],
                product_data['is_active'], product_id
            ))
            return True
    except Exception as e:
        print(f"Error updating product: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()

def delete_user(user_id):
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            # Check if user is linked to any critical records that block deletion
            cursor.execute("SELECT COUNT(*) FROM sales WHERE employee_id = %s", (user_id,))
            count_sales = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM supplier_users WHERE user_id = %s", (user_id,))
            count_supplier_links = cursor.fetchone()[0]

            # Add checks for other linked tables as needed...

            if count_sales > 0 or count_supplier_links > 0:
                return False  # Cannot delete user due to linked records

            cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
            connection.commit()
            return True
    except Exception as e:
        print(f"Error deleting user: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()




def delete_product(product_id):
    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM products WHERE product_id = %s",
                (product_id,)
            )

        connection.commit()
        return True

    except Exception as e:
        print(f"Error deleting product: {e}")
        return False

    finally:
        if 'connection' in locals():
            connection.close()


def update_stock(product_id, quantity_change):
    """Update product stock quantity"""
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            query = "UPDATE products SET stock_qty = stock_qty + %s WHERE product_id = %s"
            cursor.execute(query, (quantity_change, product_id))
            return True
    except Exception as e:
        print(f"Error updating stock: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()


# CRUD Functions for Categories
def get_all_categories():
    """Get all categories"""
    try:
        connection = get_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            query = "SELECT * FROM categories ORDER BY category_id DESC"
            cursor.execute(query)
            return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching categories: {e}")
        return []
    finally:
        if 'connection' in locals():
            connection.close()


def add_category(name, description):
    """Add new category"""
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            query = "INSERT INTO categories (name, description) VALUES (%s, %s)"
            cursor.execute(query, (name, description))
            return True
    except Exception as e:
        print(f"Error adding category: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()


def update_category(category_id, name, description):
    """Update category"""
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            query = "UPDATE categories SET name = %s, description = %s WHERE category_id = %s"
            cursor.execute(query, (name, description, category_id))
            return True
    except Exception as e:
        print(f"Error updating category: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()


def delete_category(category_id):
    """Delete category"""
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            # Check if category is used by products
            cursor.execute("SELECT COUNT(*) as count FROM products WHERE category_id = %s", (category_id,))
            if cursor.fetchone()[0] > 0:
                return False  # Cannot delete category with products

            query = "DELETE FROM categories WHERE category_id = %s"
            cursor.execute(query, (category_id,))
            return True
    except Exception as e:
        print(f"Error deleting category: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()


# CRUD Functions for Suppliers
def get_all_suppliers():
    """Get all suppliers"""
    try:
        connection = get_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            query = "SELECT * FROM suppliers ORDER BY supplier_id DESC"
            cursor.execute(query)
            return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching suppliers: {e}")
        return []
    finally:
        if 'connection' in locals():
            connection.close()


def add_supplier(supplier_data):
    """Add new supplier"""
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            query = """
                INSERT INTO suppliers (name, contact_person, phone, email, address, gstin, notes, user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                supplier_data['name'], supplier_data['contact_person'], supplier_data['phone'],
                supplier_data['email'], supplier_data['address'], supplier_data['gstin'],
                supplier_data['notes'], supplier_data.get('user_id')
            ))
            return True
    except Exception as e:
        print(f"Error adding supplier: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()


def update_supplier(supplier_id, supplier_data):
    """
    Update supplier information based on supplier_id.

    Parameters:
        supplier_id (int): ID of the supplier to update.
        supplier_data (dict): Dictionary containing supplier fields to update, for example:
            {
                'name': str,
                'contact_person': str,
                'phone': str,
                'email': str,
                'address': str,
                'gstin': str,
                'notes': str,
                'user_id': int or None
            }

    Returns:
        bool: True if update successful, False otherwise.
    """
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            query = """
            UPDATE suppliers
            SET name = %s,
                contact_person = %s,
                phone = %s,
                email = %s,
                address = %s,
                gstin = %s,
                notes = %s,
                user_id = %s
            WHERE supplier_id = %s
            """
            cursor.execute(query, (
                supplier_data.get('name'),
                supplier_data.get('contact_person'),
                supplier_data.get('phone'),
                supplier_data.get('email'),
                supplier_data.get('address'),
                supplier_data.get('gstin'),
                supplier_data.get('notes'),
                supplier_data.get('user_id'),
                supplier_id
            ))
        return True
    except Exception as e:
        print(f"Error updating supplier: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()


def delete_supplier(supplier_id):
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            # Check if supplier is used by any product
            cursor.execute("SELECT COUNT(*) FROM products WHERE supplier_id = %s", (supplier_id,))
            count = cursor.fetchone()[0]
            if count > 0:
                return False  # Can't delete, products linked
            cursor.execute("DELETE FROM suppliers WHERE supplier_id = %s", (supplier_id,))
            return True
    except Exception as e:
        print(f"Error deleting supplier: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()


def get_shop_info():
    try:
        connection = get_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM shop_info WHERE id = 1")
            result = cursor.fetchone()
            return result if result else {}
    except Exception as e:
        print(f"Error fetching shop info: {e}")
        return {}
    finally:
        if 'connection' in locals():
            connection.close()


def undo_received_po(po_id):
    connection = None
    try:
        connection = get_connection()
        connection.autocommit(False)
        with connection.cursor(pymysql.cursors.DictCursor) as cur:
            # Check current status first
            cur.execute("SELECT status FROM purchase_orders WHERE po_id = %s FOR UPDATE", (po_id,))
            result = cur.fetchone()
            if not result or result['status'] != 'Received':
                return False

            # Change status back to 'Ordered' (or previous state)
            cur.execute("UPDATE purchase_orders SET status = 'Ordered' WHERE po_id = %s", (po_id,))

            # Get items in the PO
            cur.execute("SELECT product_id, qty FROM purchase_items WHERE po_id = %s", (po_id,))
            items = cur.fetchall()

            # Decrease stock quantities accordingly
            for item in items:
                cur.execute(
                    "UPDATE products SET stock_qty = GREATEST(stock_qty - %s, 0) WHERE product_id = %s",
                    (item['qty'], item['product_id'])
                )
            connection.commit()
            return True
    except Exception as e:
        if connection:
            try:
                connection.rollback()
            except Exception:
                pass
        print(f"Error undoing received PO: {e}")
        return False
    finally:
        if connection:
            connection.close()

def cancel_purchase_order(po_id):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("UPDATE purchase_orders SET status = 'Cancelled' WHERE po_id = %s", (po_id,))
            connection.commit()
            return True
    except Exception as e:
        print(f"Error cancelling purchase order: {e}")
        return False
    finally:
        connection.close()



def mark_po_received(po_id):
    connection = None
    try:
        connection = get_connection()
        connection.autocommit(False)
        with connection.cursor() as cur:
            # Check current status first to prevent duplicate stock increment
            cur.execute("SELECT status FROM purchase_orders WHERE po_id = %s FOR UPDATE", (po_id,))
            result = cur.fetchone()
            if not result or result[0] == 'Received':
                return False  # Already received or PO not found

            cur.execute("UPDATE purchase_orders SET status = 'Received' WHERE po_id = %s", (po_id,))
            cur.execute("SELECT product_id, qty FROM purchase_items WHERE po_id = %s", (po_id,))
            items = cur.fetchall()
            for item in items:
                product_id = item[0]  # first element of tuple
                qty = item[1]         # second element of tuple
                cur.execute("UPDATE products SET stock_qty = stock_qty + %s WHERE product_id = %s", (qty, product_id))
            connection.commit()
            return True
    except Exception as e:
        if connection:
            try:
                connection.rollback()
            except Exception:
                pass
        print(f"Error marking PO received: {e}")
        return False
    finally:
        if connection:
            connection.close()



def update_purchase_order(po_id, po_data, item_list):
    """
    Update purchase order and its items.

    Parameters:
        po_id (int): Purchase order ID to update.
        po_data (dict): Dictionary with purchase order fields:
            - supplier_id (int)
            - expected_date (str or date)
            - notes (str)
            - total_amount (float)
            - status (str)
        item_list (list): List of dicts with items:
            - sku (str)
            - qty (int)
            - unit_price (float)

    Returns:
        bool: True if success, False if any error
    """
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            # Update purchase_orders table
            update_po_query = """
                UPDATE purchase_orders
                SET supplier_id=%s, expected_date=%s, notes=%s, total_amount=%s, status=%s
                WHERE po_id=%s
            """
            cursor.execute(update_po_query, (
                po_data['supplier_id'],
                po_data['expected_date'],
                po_data['notes'],
                po_data['total_amount'],
                po_data['status'],
                po_id
            ))

            # Delete existing items for this PO
            cursor.execute("DELETE FROM purchase_items WHERE po_id=%s", (po_id,))

            # Insert new items
            insert_item_query = """
                INSERT INTO purchase_items (po_id, product_id, qty, unit_cost, line_total)
                VALUES (%s, %s, %s, %s, %s)
            """

            # Need to get product IDs by SKU for each item
            products = get_all_products()
            sku_to_id = {p['sku']: p['product_id'] for p in products}

            for item in item_list:
                product_id = sku_to_id.get(item['sku'])
                if product_id is None:
                    # Skip or raise error for invalid SKU
                    continue
                qty = item['qty']
                unit_cost = item['unit_price']
                line_total = qty * unit_cost
                cursor.execute(insert_item_query, (po_id, product_id, qty, unit_cost, line_total))

            connection.commit()
        return True

    except Exception as e:
        print(f"Error updating purchase order: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()


def get_purchase_orders_with_supplier():
    connection = get_connection()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute("""
                SELECT po.*, s.name AS supplier_name
                FROM purchase_orders po
                JOIN suppliers s ON po.supplier_id = s.supplier_id
                ORDER BY po.po_id DESC
            """)
            return cur.fetchall()
    finally:
        connection.close()


def get_purchase_items(po_id):
    connection = get_connection()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute("""
                SELECT pi.*, p.name AS product_name, p.sku
                FROM purchase_items pi
                JOIN products p ON pi.product_id = p.product_id
                WHERE pi.po_id = %s
            """, (po_id,))
            return cur.fetchall()
    finally:
        connection.close()


def add_purchase_order(po_data, item_list):
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            # Insert purchase order
            po_query = """
            INSERT INTO purchase_orders (supplier_id, status, expected_date, total_amount, notes)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(po_query, (
                po_data['supplier_id'],
                po_data['status'],
                po_data['expected_date'],
                po_data['total_amount'],
                po_data['notes']
            ))
            po_id = cursor.lastrowid
            # Insert items
            for item in item_list:
                item_query = """
                INSERT INTO purchase_items (po_id, product_id, qty, unit_cost, line_total)
                VALUES (%s, %s, %s, %s, %s)
                """
                # Lookup product_id by SKU or name if you need
                product_obj = next((p for p in get_all_products() if p['sku'] == item['sku']), None)
                if not product_obj:
                    continue
                cursor.execute(item_query, (
                po_id, product_obj['product_id'], item['qty'], item['unit_price'], item['qty'] * item['unit_price']))
        return po_id
    except Exception as e:
        print(f"Error creating PO: {e}")
        return None
    finally:
        if 'connection' in locals():
            connection.close()


def update_shop_info(shop_data):
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO shop_info (id, name, address1, address2, phone, email, gstin, upi_id, upi_name)
                VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    name = VALUES(name),
                    address1 = VALUES(address1),
                    address2 = VALUES(address2),
                    phone = VALUES(phone),
                    email = VALUES(email),
                    gstin = VALUES(gstin),
                    upi_id = VALUES(upi_id),
                    upi_name = VALUES(upi_name);
            """, (
                shop_data.get('name'),
                shop_data.get('address1'),
                shop_data.get('address2'),
                shop_data.get('phone'),
                shop_data.get('email'),
                shop_data.get('gstin'),
                shop_data.get('upi_id'),
                shop_data.get('upi_name')
            ))
        return True
    except Exception as e:
        print(f"Error updating shop info: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()


def get_sales_data_for_graph(start_date=None, end_date=None):
    """
    Fetch aggregated sales totals grouped by date for graphing.
    Optionally filter by date range.
    Returns list of dicts: [{'date': date_obj, 'total': Decimal}, ...]
    """
    try:
        connection = get_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            query = """
                SELECT DATE(datetime) AS date, 
                       SUM(total) AS total
                FROM sales
            """
            params = []

            if start_date and end_date:
                query += " WHERE DATE(datetime) BETWEEN %s AND %s"
                params = [start_date, end_date]

            query += " GROUP BY DATE(datetime) ORDER BY DATE(datetime)"

            cursor.execute(query, params)
            results = cursor.fetchall()
            return results

    except Exception as e:
        print(f"Error fetching sales data for graph: {e}")
        return []

    finally:
        if 'connection' in locals():
            connection.close()


# Sales functions
def create_sale(
        employee_id,
        customer_name,
        customer_phone,
        customer_email,
        items,
        subtotal,
        tax,
        total,
        total_profit):
    """Create a new sale record atomically"""
    connection = None
    try:
        connection = get_connection()
        connection.autocommit(False)

        with connection.cursor() as cursor:

            # Insert sale record
            sale_query = """
                INSERT INTO sales
                (
                    employee_id,
                    customer_name,
                    customer_phone,
                    customer_email,
                    subtotal,
                    tax,
                    total,
                    profit
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            cursor.execute(
                sale_query,
                (
                    employee_id,
                    customer_name,
                    customer_phone,
                    customer_email if customer_email else None,
                    subtotal,
                    tax,
                    total,
                    total_profit
                )
            )

            sale_id = cursor.lastrowid

            # Insert sale items and update stock in the same transaction
            for item in items:

                item_query = """
                    INSERT INTO sale_items
                    (
                        sale_id,
                        product_id,
                        qty,
                        unit_price,
                        line_total
                    )
                    VALUES (%s, %s, %s, %s, %s)
                """

                cursor.execute(
                    item_query,
                    (
                        sale_id,
                        item['product_id'],
                        item['qty'],
                        item['unit_price'],
                        item['line_total']
                    )
                )

                # Deduct stock directly within the transaction
                cursor.execute(
                    "UPDATE products SET stock_qty = stock_qty - %s WHERE product_id = %s",
                    (item['qty'], item['product_id'])
                )

            connection.commit()
            return sale_id

    except Exception as e:
        if connection:
            try:
                connection.rollback()
            except Exception:
                pass
        print(f"Error creating sale: {e}")
        return None

    finally:
        if connection:
            connection.close()
def get_sale_items(sale_id):
    """
    Fetch all items for a given sale, joined with product details.
    Returns a list of dicts like:
    [
        {'item_id': 1, 'product_name': 'Laptop', 'qty': 2, 'unit_price': 45000.00, 'line_total': 90000.00},
        ...
    ]
    """
    try:
        connection = get_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            query = """
                SELECT si.item_id, si.sale_id, si.product_id, p.name AS product_name,
                       si.qty, si.unit_price, si.line_total
                FROM sale_items si
                JOIN products p ON si.product_id = p.product_id
                WHERE si.sale_id = %s
            """
            cursor.execute(query, (sale_id,))
            return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching sale items: {e}")
        return []
    finally:
        if 'connection' in locals():
            connection.close()

def get_sale(sale_id):
    """Fetch sale header information"""

    try:
        connection = get_connection()

        with connection.cursor(
                pymysql.cursors.DictCursor) as cursor:

            cursor.execute("""
                SELECT *
                FROM sales
                WHERE sale_id = %s
            """, (sale_id,))

            return cursor.fetchone()

    except Exception as e:
        print(f"Error fetching sale: {e}")
        return None

    finally:
        if 'connection' in locals():
            connection.close()

def restore_sale_stock(sale_id):
    """
    Restore stock for all items in a sale
    """

    try:
        connection = get_connection()

        with connection.cursor(pymysql.cursors.DictCursor) as cursor:

            cursor.execute("""
                SELECT product_id, qty
                FROM sale_items
                WHERE sale_id=%s
            """, (sale_id,))

            items = cursor.fetchall()

            for item in items:

                cursor.execute("""
                    UPDATE products
                    SET stock_qty = stock_qty + %s
                    WHERE product_id = %s
                """, (
                    item["qty"],
                    item["product_id"]
                ))

        return True

    except Exception as e:
        print("Restore stock error:", e)
        return False

    finally:
        if 'connection' in locals():
            connection.close()

def update_sale(
        sale_id,
        customer_name,
        customer_phone,
        customer_email,
        items,
        subtotal,
        tax,
        total,
        total_profit):
    """Update sale record and items atomically"""
    connection = None
    try:
        connection = get_connection()
        connection.autocommit(False)

        with connection.cursor(pymysql.cursors.DictCursor) as cursor:

            # 1. Restore previous stock for this sale
            cursor.execute("""
                SELECT product_id, qty
                FROM sale_items
                WHERE sale_id = %s
            """, (sale_id,))
            old_items = cursor.fetchall()

            for item in old_items:
                cursor.execute("""
                    UPDATE products
                    SET stock_qty = stock_qty + %s
                    WHERE product_id = %s
                """, (item["qty"], item["product_id"]))

            # 2. Remove old items
            cursor.execute(
                "DELETE FROM sale_items WHERE sale_id=%s",
                (sale_id,)
            )

            # 3. Insert updated items and deduct stock
            for item in items:

                cursor.execute("""
                    INSERT INTO sale_items
                    (
                        sale_id,
                        product_id,
                        qty,
                        unit_price,
                        line_total
                    )
                    VALUES (%s,%s,%s,%s,%s)
                """, (
                    sale_id,
                    item["product_id"],
                    item["qty"],
                    item["unit_price"],
                    item["line_total"]
                ))

                cursor.execute("""
                    UPDATE products
                    SET stock_qty = stock_qty - %s
                    WHERE product_id = %s
                """, (
                    item["qty"],
                    item["product_id"]
                ))

            # 4. Update sale header
            cursor.execute("""
                UPDATE sales
                SET customer_name=%s,
                    customer_phone=%s,
                    customer_email=%s,
                    subtotal=%s,
                    tax=%s,
                    total=%s,
                    profit=%s
                WHERE sale_id=%s
            """, (
                customer_name,
                customer_phone,
                customer_email if customer_email else None,
                subtotal,
                tax,
                total,
                total_profit,
                sale_id
            ))

            connection.commit()
            return True

    except Exception as e:
        if connection:
            try:
                connection.rollback()
            except Exception:
                pass
        print("Update sale error:", e)
        return False

    finally:
        if connection:
            connection.close()
def get_sales_history(start_date=None, end_date=None):
    try:
        connection = get_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            query = """
                SELECT s.*, u.full_name as employee_name,
                       IFNULL(SUM(si.qty), 0) as items_count
                FROM sales s
                JOIN users u ON s.employee_id = u.user_id
                LEFT JOIN sale_items si ON s.sale_id = si.sale_id
            """
            params = []
            if start_date and end_date:
                query += " WHERE DATE(s.datetime) BETWEEN %s AND %s"
                params = [start_date, end_date]
            query += " GROUP BY s.sale_id ORDER BY s.sale_id DESC"
            cursor.execute(query, params)
            return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching sales history: {e}")
        return []
    finally:
        if 'connection' in locals():
            connection.close()


def get_low_stock_products():
    """Get products with stock below reorder level"""
    try:
        connection = get_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            query = """
                SELECT * FROM products 
                WHERE stock_qty <= reorder_level AND is_active = TRUE
                ORDER BY stock_qty ASC
            """
            cursor.execute(query)
            return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching low stock products: {e}")
        return []
    finally:
        if 'connection' in locals():
            connection.close()

def get_suppliers_for_user(user_id):
    connection = get_connection()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT s.*
                FROM suppliers s
                JOIN supplier_users su ON su.supplier_id = s.supplier_id
                WHERE su.user_id = %s
            """, (user_id,))
            return cursor.fetchall()
    finally:
        connection.close()

def assign_supplier_to_user(user_id, supplier_id):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # Prevent duplicate entries
            cursor.execute("SELECT id FROM supplier_users WHERE user_id=%s AND supplier_id=%s", (user_id, supplier_id))
            if cursor.fetchone() is None:
                cursor.execute("INSERT INTO supplier_users (user_id, supplier_id) VALUES (%s, %s)", (user_id, supplier_id))
                connection.commit()
            return True
    except Exception as e:
        print(f"Error assigning supplier to user: {e}")
        return False
    finally:
        connection.close()

def remove_suppliers_for_user(user_id):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM supplier_users WHERE user_id=%s", (user_id,))
            connection.commit()
            return True
    except Exception as e:
        print(f"Error removing suppliers for user: {e}")
        return False
    finally:
        connection.close()
def get_purchase_orders_for_suppliers(supplier_ids):
    if not supplier_ids:
        return []
    connection = get_connection()
    try:
        format_strings = ','.join(['%s'] * len(supplier_ids))
        query = f"""
            SELECT po.*, s.name AS supplier_name
            FROM purchase_orders po
            JOIN suppliers s ON s.supplier_id = po.supplier_id
            WHERE po.supplier_id IN ({format_strings})
            ORDER BY po.po_id DESC
        """
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(query, tuple(supplier_ids))
            return cursor.fetchall()
    finally:
        connection.close()

def get_user_by_username(username):
    connection = get_connection()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            return cursor.fetchone()
    finally:
        connection.close()


def get_next_product_id():
    """Get the next auto-increment ID for products (live, uncached read)"""
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            # Force MySQL to refresh table metadata instead of using
            # the cached information_schema value (default cache = 24h)
            cursor.execute("SET SESSION information_schema_stats_expiry = 0")

            cursor.execute("""
                SELECT AUTO_INCREMENT
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'products'
            """)
            result = cursor.fetchone()
            auto_inc = result[0] if result and result[0] else 1

            # Safety net: never show a number that's already taken,
            # in case the cache is still behind for any reason
            cursor.execute("SELECT MAX(product_id) FROM products")
            max_result = cursor.fetchone()
            max_id_next = (max_result[0] + 1) if max_result and max_result[0] else 1

            return max(auto_inc, max_id_next)

    except Exception as e:
        print(f"Error getting next product ID: {e}")
        return None
    finally:
        if 'connection' in locals():
            connection.close()

def get_next_category_id():
    """Get the next auto-increment ID for categories (live, uncached read)"""
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("SET SESSION information_schema_stats_expiry = 0")

            cursor.execute("""
                SELECT AUTO_INCREMENT
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'categories'
            """)
            result = cursor.fetchone()
            auto_inc = result[0] if result and result[0] else 1

            cursor.execute("SELECT MAX(category_id) FROM categories")
            max_result = cursor.fetchone()
            max_id_next = (max_result[0] + 1) if max_result and max_result[0] else 1

            return max(auto_inc, max_id_next)

    except Exception as e:
        print(f"Error getting next category ID: {e}")
        return None
    finally:
        if 'connection' in locals():
            connection.close()


def get_next_supplier_id():
    """Get the next auto-increment ID for suppliers (live, uncached read)"""
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("SET SESSION information_schema_stats_expiry = 0")

            cursor.execute("""
                SELECT AUTO_INCREMENT
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'suppliers'
            """)
            result = cursor.fetchone()
            auto_inc = result[0] if result and result[0] else 1

            cursor.execute("SELECT MAX(supplier_id) FROM suppliers")
            max_result = cursor.fetchone()
            max_id_next = (max_result[0] + 1) if max_result and max_result[0] else 1

            return max(auto_inc, max_id_next)

    except Exception as e:
        print(f"Error getting next supplier ID: {e}")
        return None
    finally:
        if 'connection' in locals():
            connection.close()


def get_next_po_id():
    """Get the next auto-increment ID for purchase orders (live, uncached read)"""
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("SET SESSION information_schema_stats_expiry = 0")

            cursor.execute("""
                SELECT AUTO_INCREMENT
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'purchase_orders'
            """)
            result = cursor.fetchone()
            auto_inc = result[0] if result and result[0] else 1

            cursor.execute("SELECT MAX(po_id) FROM purchase_orders")
            max_result = cursor.fetchone()
            max_id_next = (max_result[0] + 1) if max_result and max_result[0] else 1

            return max(auto_inc, max_id_next)

    except Exception as e:
        print(f"Error getting next PO ID: {e}")
        return None
    finally:
        if 'connection' in locals():
            connection.close()


def get_next_user_id():
    """Get the next auto-increment ID for users (live, uncached read)"""
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("SET SESSION information_schema_stats_expiry = 0")

            cursor.execute("""
                SELECT AUTO_INCREMENT
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'users'
            """)
            result = cursor.fetchone()
            auto_inc = result[0] if result and result[0] else 1

            cursor.execute("SELECT MAX(user_id) FROM users")
            max_result = cursor.fetchone()
            max_id_next = (max_result[0] + 1) if max_result and max_result[0] else 1

            return max(auto_inc, max_id_next)

    except Exception as e:
        print(f"Error getting next User ID: {e}")
        return None
    finally:
        if 'connection' in locals():
            connection.close()

def get_next_sale_id():
    """Get the next auto-increment ID for sales (live, uncached read)"""
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("SET SESSION information_schema_stats_expiry = 0")

            cursor.execute("""
                SELECT AUTO_INCREMENT
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'sales'
            """)
            result = cursor.fetchone()
            auto_inc = result[0] if result and result[0] else 1

            cursor.execute("SELECT MAX(sale_id) FROM sales")
            max_result = cursor.fetchone()
            max_id_next = (max_result[0] + 1) if max_result and max_result[0] else 1

            return max(auto_inc, max_id_next)
    except Exception as e:
        print(f"Error getting next sale ID: {e}")
        return None

    finally:
        if 'connection' in locals():
            connection.close()