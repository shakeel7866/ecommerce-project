from app import app
from database.db import mysql

with app.app_context():

    cur = mysql.connection.cursor()

    cur.execute("SELECT DATABASE()")

    print("Connected Database:", cur.fetchone())

    cur.close()
