from app import app
from database.db import mysql

with app.app_context():

    cur = mysql.connection.cursor()

    cur.execute("""
        ALTER TABLE stock_history
        MODIFY transaction_type
        ENUM(
            'Purchase',
            'Sale',
            'Sales Return',
            'Purchase Return',
            'Adjustment'
        )
        NOT NULL
    """)

    mysql.connection.commit()

    print("Purchase Return ENUM added successfully!")

    cur.close()
