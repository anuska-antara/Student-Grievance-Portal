import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="pes2ug23cs084",
        database="cgrs_db"
    )

