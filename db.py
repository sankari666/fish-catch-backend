import os
import mysql.connector
from flask import g


def get_db():
    if "db" not in g:
        g.db = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE"),
        )

    return g.db


def get_cursor(dictionary=False):
    return get_db().cursor(dictionary=dictionary)


def close_db(exception=None):
    db = g.pop("db", None)

    if db is not None and db.is_connected():
        db.close()