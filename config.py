import os
from dotenv import load_dotenv

load_dotenv()


class Config:

    SECRET_KEY = os.environ.get("SECRET_KEY", "techstore-secret-key-2026")

    MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")

    MYSQL_USER = os.environ.get("MYSQL_USER", "root")

    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")

    MYSQL_DB = os.environ.get("MYSQL_DB", "ecommerce_db")

    MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))

    MYSQL_SSL_CA = os.environ.get("MYSQL_SSL_CA", "")
