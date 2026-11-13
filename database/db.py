import mysql.connector as mysql_connector


class CursorWrapper:
    def __init__(self, connection, cursor):
        self.connection = connection
        self.cursor = cursor

    def execute(self, operation, params=None):
        if params is None:
            return self.cursor.execute(operation)
        return self.cursor.execute(operation, params)

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    def fetchmany(self, size=None):
        if size is None:
            return self.cursor.fetchmany()
        return self.cursor.fetchmany(size)

    def close(self):
        try:
            self.cursor.close()
        finally:
            self.connection.close()

    def __getattr__(self, name):
        return getattr(self.cursor, name)


class ConnectionWrapper:
    def __init__(self, app):
        self.app = app
        self._connection = None

    def connect(self):
        if self._connection is None or not self._connection.is_connected():
            config = {
                "host": self.app.config.get("MYSQL_HOST", "localhost"),
                "user": self.app.config.get("MYSQL_USER", "root"),
                "password": self.app.config.get("MYSQL_PASSWORD", ""),
                "database": self.app.config.get("MYSQL_DB", ""),
                "port": int(self.app.config.get("MYSQL_PORT", 3306)),
            }

            ssl_ca = self.app.config.get("MYSQL_SSL_CA")

            if ssl_ca:
                config["ssl_ca"] = ssl_ca
                config["ssl_verify_cert"] = True
                config["ssl_verify_identity"] = True

            self._connection = mysql_connector.connect(**config)

        return self._connection

    def cursor(self, dictionary=False):
        connection = self.connect()

        cursor = connection.cursor(dictionary=dictionary)

        return CursorWrapper(connection, cursor)

    def commit(self):
        if self._connection and self._connection.is_connected():
            self._connection.commit()

    def rollback(self):
        if self._connection and self._connection.is_connected():
            self._connection.rollback()

    def close(self):
        if self._connection and self._connection.is_connected():
            self._connection.close()

        self._connection = None


class MySQL:
    def __init__(self):
        self.connection = None

    def init_app(self, app):
        self.app = app
        self.connection = ConnectionWrapper(app)


mysql = MySQL()
