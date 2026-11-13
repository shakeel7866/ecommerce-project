from app import app
from database.db import mysql

with app.app_context():

    cur = mysql.connection.cursor()

    # Expense Categories Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS expense_categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            category_name VARCHAR(100) NOT NULL UNIQUE,
            description VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Expenses Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            category_id INT NOT NULL,
            amount DECIMAL(12,2) NOT NULL,
            expense_date DATE NOT NULL,
            description VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (category_id)
                REFERENCES expense_categories(id)
                ON DELETE CASCADE
        )
    """)

    mysql.connection.commit()

    print("Expense tables created successfully!")

    cur.close()
