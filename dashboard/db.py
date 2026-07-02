from datetime import date, timedelta

import mysql.connector

from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME


def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )


def fetch_reports(search=None, source=None, start_date=None, end_date=None,
                   sort_field="upload_date", sort_order="desc"):
    sort_columns = {
        "id": "id",
        "pdf_name": "pdf_name",
        "source": "source",
        "date": "upload_date",
    }
    column = sort_columns.get(sort_field, "upload_date")
    order = "ASC" if str(sort_order).lower() == "asc" else "DESC"

    where = []
    params = []

    if search:
        where.append("(pdf_name LIKE %s OR source LIKE %s OR category LIKE %s)")
        term = f"%{search}%"
        params.extend([term, term, term])

    if source and source != "All Sources":
        where.append("source = %s")
        params.append(source)

    if start_date:
        where.append("upload_date >= %s")
        params.append(start_date)

    if end_date:
        where.append("upload_date <= %s")
        params.append(end_date)

    sql = "SELECT id, upload_date, source, pdf_link, pdf_name, category FROM store_pdf"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += f" ORDER BY {column} {order}, id {order}"

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    for row in rows:
        if row.get("upload_date") is not None:
            row["upload_date"] = row["upload_date"].strftime("%Y-%m-%d")

    return rows


def fetch_reports_by_ids(ids):
    if not ids:
        return []

    placeholders = ",".join(["%s"] * len(ids))
    sql = (
        "SELECT id, upload_date, source, pdf_link, pdf_name, category "
        f"FROM store_pdf WHERE id IN ({placeholders})"
    )

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, ids)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    for row in rows:
        if row.get("upload_date") is not None:
            row["upload_date"] = row["upload_date"].strftime("%Y-%m-%d")

    return rows


def fetch_sources():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT source FROM store_pdf ORDER BY source")
    rows = [r[0] for r in cursor.fetchall()]
    cursor.close()
    conn.close()
    return rows


def fetch_stats():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM store_pdf")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT source) FROM store_pdf")
    total_sources = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM store_pdf WHERE upload_date = %s", (date.today(),))
    today_count = cursor.fetchone()[0]

    week_ago = date.today() - timedelta(days=7)
    cursor.execute("SELECT COUNT(*) FROM store_pdf WHERE upload_date >= %s", (week_ago,))
    week_count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return {
        "total": total,
        "total_sources": total_sources,
        "today": today_count,
        "this_week": week_count,
    }


def insert_report(source, pdf_name, pdf_link, category, upload_date=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO store_pdf (upload_date, source, pdf_link, pdf_name, category)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (upload_date or date.today(), source, pdf_link, pdf_name, category),
    )

    conn.commit()
    new_id = cursor.lastrowid

    cursor.close()
    conn.close()
    return new_id
