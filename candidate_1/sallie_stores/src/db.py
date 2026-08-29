from __future__ import annotations

import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv  #type: ignore

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def get_connection():
    missing = [
        key
        for key in ["DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT"]
        if not os.getenv(key)
    ]
    if missing:
        raise ValueError(f"Missing DB env vars: {', '.join(missing)}")

    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )
    conn.autocommit = False
    return conn


def read_schema_sql(schema_path: str | Path | None = None) -> str:
    schema_file = (
        Path(schema_path)
        if schema_path
        else Path(__file__).resolve().parents[1] / "db" / "schema.sql"
    )
    return schema_file.read_text(encoding="utf-8")


def apply_schema(conn, schema_path: str | Path | None = None) -> None:
    schema_sql = read_schema_sql(schema_path)
    with conn.cursor() as cur:
        cur.execute(schema_sql)
    conn.commit()

