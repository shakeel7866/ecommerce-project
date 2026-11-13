from app import app
from database.db import mysql

with app.app_context():

    cur = mysql.connection.cursor()

    cur.execute("""
        UPDATE stock_history
        SET transaction_type = %s
        WHERE id = %s
    """, ("Sales Return", 4))

    mysql.connection.commit()

    print("Stock History record fixed!")
    print("Rows updated:", cur.rowcount)

    cur.close()
