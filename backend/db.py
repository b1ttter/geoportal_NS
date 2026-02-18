import psycopg2
import os

def get_connection():
    return psycopg2.connect(
        host="postgis",
        port=5432,
        database="gis",
        user="gisuser",
        password="gispass"
    )
