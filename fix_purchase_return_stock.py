from app import app
from database.db import mysql

with app.app_context():

    cur = mysql.connection.cursor()

    cur.execute("""
        UPDATE stock_history
        SET transaction_type = %s
        WHERE remarks LIKE %s
        AND transaction_type = %s
    """, (
        "Purchase Return",
        "Purchase Return Invoice : %",
        ""
    ))

    mysql.connection.commit()

    print("Purchase Return Stock History fixed!")
    print("Rows updated:", cur.rowcount)

    cur.close()
