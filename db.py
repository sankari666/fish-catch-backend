import os
import mysql.connector

db = None


def get_connection():
    global db

    if db is None:
        db = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            ssl_disabled=False
        )
    else:
        try:
            db.ping(reconnect=True, attempts=3, delay=2)
        except mysql.connector.Error:
            db = mysql.connector.connect(
                host=os.getenv("DB_HOST"),
                port=int(os.getenv("DB_PORT", "3306")),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME"),
                ssl_disabled=False
            )

    return db


def get_cursor(dictionary=False):
    return get_connection().cursor(dictionary=dictionary)