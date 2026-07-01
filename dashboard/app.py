import csv
import io
from datetime import date

from flask import Flask, jsonify, render_template, request, Response

import db
from config import DASHBOARD_HOST, DASHBOARD_PORT, DASHBOARD_DEBUG, KNOWN_SOURCES

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/reports")
def api_reports():
    search = request.args.get("search", "").strip()
    source = request.args.get("source", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    sort_field = request.args.get("sort_field", "date").strip()
    sort_order = request.args.get("sort_order", "desc").strip()

    try:
        rows = db.fetch_reports(
            search=search or None,
            source=source or None,
            start_date=start_date or None,
            end_date=end_date or None,
            sort_field=sort_field,
            sort_order=sort_order,
        )
        return jsonify({"ok": True, "reports": rows})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/api/sources")
def api_sources():
    try:
        sources = db.fetch_sources()
        if not sources:
            sources = KNOWN_SOURCES
        return jsonify({"ok": True, "sources": sources})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc), "sources": KNOWN_SOURCES}), 200


@app.route("/api/stats")
def api_stats():
    try:
        stats = db.fetch_stats()
        return jsonify({"ok": True, "stats": stats})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/api/reports", methods=["POST"])
def api_add_report():
    payload = request.get_json(silent=True) or {}

    pdf_name = (payload.get("pdf_name") or "").strip()
    source = (payload.get("source") or "").strip()
    pdf_link = (payload.get("pdf_link") or "").strip()
    category = (payload.get("category") or "").strip() or None
    upload_date = (payload.get("upload_date") or "").strip() or None

    errors = {}
    if not pdf_name:
        errors["pdf_name"] = "Document name is required"
    if not source:
        errors["source"] = "Source is required"
    if not pdf_link:
        errors["pdf_link"] = "PDF link is required"

    if errors:
        return jsonify({"ok": False, "errors": errors}), 400

    try:
        new_id = db.insert_report(
            source=source,
            pdf_name=pdf_name,
            pdf_link=pdf_link,
            category=category,
            upload_date=upload_date,
        )
        return jsonify({"ok": True, "id": new_id})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/api/export.csv")
def api_export_csv():
    search = request.args.get("search", "").strip()
    source = request.args.get("source", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    sort_field = request.args.get("sort_field", "date").strip()
    sort_order = request.args.get("sort_order", "desc").strip()

    try:
        rows = db.fetch_reports(
            search=search or None,
            source=source or None,
            start_date=start_date or None,
            end_date=end_date or None,
            sort_field=sort_field,
            sort_order=sort_order,
        )
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Sr No", "Document Name", "Source", "Category", "Upload Date", "PDF Link"])
    for idx, row in enumerate(rows, start=1):
        writer.writerow([
            idx,
            row["pdf_name"],
            row["source"],
            row.get("category") or "",
            row["upload_date"],
            row["pdf_link"],
        ])

    output = buffer.getvalue()
    filename = f"ISEC_PDF_Catalog_Export_{date.today().isoformat()}.csv"

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


if __name__ == "__main__":
    app.run(host=DASHBOARD_HOST, port=DASHBOARD_PORT, debug=DASHBOARD_DEBUG)
