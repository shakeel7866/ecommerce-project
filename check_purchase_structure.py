from app import app
from database.db import mysql

with app.app_context():

    cur = mysql.connection.cursor()

    print("===== PURCHASES TABLE =====")

    cur.execute("DESCRIBE purchases")

    for row in cur.fetchall():
        print(row)

    print("\n===== PURCHASE ITEMS TABLE =====")

    cur.execute("DESCRIBE purchase_items")

    for row in cur.fetchall():
        print(row)

    cur.close()
