from app import app
from database.db import mysql

with app.app_context():
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT id, product_id, transaction_type, remarks
        FROM stock_history
        WHERE remarks LIKE %s
    """, ("Sales Return%",))

    print(cur.fetchall())

    cur.close()
