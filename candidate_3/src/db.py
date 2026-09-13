# src/db.py
"""
File used to manage the Postgres connection.
No business logic here — just open/close cleanly, credentials from .env.
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Open a new Postgres connection using credentials from .env."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )