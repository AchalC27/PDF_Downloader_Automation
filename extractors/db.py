from datetime import date
import mysql.connector


def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Achal@27",
        database="file_downloader"
    )


def pdf_exists(source, pdf_name):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 1
        FROM store_pdf
        WHERE source = %s
        AND pdf_name = %s
        LIMIT 1
    """, (source, pdf_name))

    exists = cursor.fetchone() is not None

    cursor.close()
    conn.close()

    return exists

def save_pdf(source, pdf_name, pdf_link, category=None):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO store_pdf
            (upload_date, source, pdf_link, pdf_name, category)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            date.today(),
            source,
            pdf_link,
            pdf_name,
            category
        ))

        conn.commit()

    except mysql.connector.errors.IntegrityError as exc:
        if exc.errno == 1062:
            return False
        raise

    finally:
        cursor.close()
        conn.close()

    return True