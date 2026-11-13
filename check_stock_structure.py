from app import app
from database.db import mysql

with app.app_context():

    cur = mysql.connection.cursor()

    cur.execute("DESCRIBE stock_history")

    for row in cur.fetchall():
        print(row)

    cur.close()
