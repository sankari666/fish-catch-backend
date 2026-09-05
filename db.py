import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Sivuselva@666",
    database="fishrepo"
)

def get_cursor(dictionary=False):
    return db.cursor(dictionary=dictionary)