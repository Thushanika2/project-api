from datetime import datetime

from flask import jsonify, request

from app.extensions import db
from app.models.track_model import Track
from app.utils.csv_utils import parse_csv_file, rows_to_csv_response
from app.utils.pdf_utils import table_pdf_response


def _validate_track_payload(data, track_id=None):
    errors = []
    name = (data.get("name") or "").strip()
    if not name:
        errors.append("Name is required.")
    elif len(name) > 255:
        errors.append("Name must be 255 characters or fewer.")

    if name:
        query = Track.query.filter_by(name=name)
        if track_id:
            query = query.filter(Track.id != track_id)
        if query.first():
            errors.append("Track name already exists.")

    return errors


def create_track(data):
    errors = _validate_track_payload(data)
    if errors:
        return {"errors": errors}, 400

    try:
        track = Track(
            name=data["name"].strip(),
            description=(data.get("description") or "").strip() or None,
        )
        db.session.add(track)
        db.session.commit()
        return {"message": "Track created.", "track": track.to_dict()}, 201
    except Exception:
        db.session.rollback()
        raise


def get_tracks():
    tracks = Track.query.order_by(Track.name).all()
    return {"tracks": [t.to_dict() for t in tracks]}, 200


def get_track(track_id):
    track = db.session.get(Track, track_id)
    if not track:
        return {"error": "Track not found."}, 404
    return {"track": track.to_dict()}, 200


def update_track(track_id, data):
    track = db.session.get(Track, track_id)
    if not track:
        return {"error": "Track not found."}, 404

    errors = _validate_track_payload(data, track_id=track_id)
    if errors:
        return {"errors": errors}, 400

    try:
        track.name = data["name"].strip()
        track.description = (data.get("description") or "").strip() or None
        db.session.commit()
        return {"message": "Track updated.", "track": track.to_dict()}, 200
    except Exception:
        db.session.rollback()
        raise


def delete_track(track_id):
    track = db.session.get(Track, track_id)
    if not track:
        return {"error": "Track not found."}, 404

    try:
        db.session.delete(track)
        db.session.commit()
        return {"message": "Track deleted."}, 200
    except Exception:
        db.session.rollback()
        raise


def export_tracks_csv():
    tracks = Track.query.order_by(Track.name).all()
    headers = ["name", "description"]
    rows = [[t.name, t.description or ""] for t in tracks]
    date_str = datetime.now().strftime("%Y-%m-%d")
    return rows_to_csv_response(f"tracks-{date_str}.csv", headers, rows)


def export_tracks_pdf():
    tracks = Track.query.order_by(Track.name).all()
    headers = ["Name", "Description"]
    rows = [[t.name, t.description or ""] for t in tracks]
    date_str = datetime.now().strftime("%Y-%m-%d")
    return table_pdf_response(f"tracks-{date_str}.pdf", "Track Catalog", headers, rows)


def import_tracks_csv(file):
    rows, header_errors = parse_csv_file(file, ["name"])
    if header_errors:
        return {"errors": header_errors}, 400

    created = 0
    skipped = 0
    row_errors = []

    for i, row in enumerate(rows, start=2):
        data = {"name": row.get("name", ""), "description": row.get("description", "")}
        errors = _validate_track_payload(data)
        if errors:
            row_errors.append({"row": i, "message": "; ".join(errors)})
            continue

        if Track.query.filter_by(name=data["name"].strip()).first():
            skipped += 1
            continue

        track = Track(
            name=data["name"].strip(),
            description=data["description"].strip() or None,
        )
        db.session.add(track)
        created += 1

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return {"created": created, "skipped": skipped, "errors": row_errors}, 200
