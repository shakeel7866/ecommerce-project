from app import app
from database.db import mysql

with app.app_context():

    cur = mysql.connection.cursor()

    # Purchase Returns Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS purchase_returns (
            id INT AUTO_INCREMENT PRIMARY KEY,
            purchase_id INT NOT NULL,
            supplier_id INT NOT NULL,
            invoice_no VARCHAR(100) NOT NULL,
            return_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
            reason VARCHAR(255),
            return_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Purchase Return Items Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS purchase_return_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            return_id INT NOT NULL,
            product_id INT NOT NULL,
            quantity INT NOT NULL,
            unit_price DECIMAL(12,2) NOT NULL DEFAULT 0,
            total_price DECIMAL(12,2) NOT NULL DEFAULT 0
        )
    """)

    mysql.connection.commit()

    print("Purchase Return tables created successfully!")

    cur.close()
