from datetime import datetime

from sqlalchemy import func

from app.extensions import db
from app.models.agenda_item_model import AgendaItem
from app.models.session_model import Session
from app.models.track_model import Track
from app.utils.csv_utils import parse_csv_file, rows_to_csv_response
from app.utils.pdf_utils import document_pdf_response, table_pdf_response


def _parse_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _get_or_create_track(track_name):
    name = track_name.strip()
    track = Track.query.filter_by(name=name).first()
    if not track:
        track = Track(name=name)
        db.session.add(track)
        db.session.flush()
    return track


def _validate_session_payload(data, session_id=None):
    errors = []
    title = (data.get("title") or "").strip()
    speaker = (data.get("speaker") or "").strip()
    room = (data.get("room") or "").strip()
    track_id = data.get("track_id")
    track_name = (data.get("track_name") or "").strip()
    start_time = _parse_datetime(data.get("start_time"))
    end_time = _parse_datetime(data.get("end_time"))
    capacity = data.get("capacity")

    if not title:
        errors.append("Title is required.")
    if not speaker:
        errors.append("Speaker is required.")
    if not room:
        errors.append("Room is required.")
    if not track_id and not track_name:
        errors.append("Track is required.")
    if track_id and not db.session.get(Track, track_id):
        errors.append("Track not found.")
    if not start_time:
        errors.append("Valid start_time is required.")
    if not end_time:
        errors.append("Valid end_time is required.")
    if start_time and end_time and start_time >= end_time:
        errors.append("End time must be after start time.")
    if capacity is None or capacity == "":
        errors.append("Capacity is required.")
    else:
        try:
            capacity = int(capacity)
            if capacity < 1:
                errors.append("Capacity must be at least 1.")
        except (TypeError, ValueError):
            errors.append("Capacity must be a positive integer.")

    return errors


def create_session(data, organizer_id):
    errors = _validate_session_payload(data)
    if errors:
        return {"errors": errors}, 400

    try:
        track_id = data.get("track_id")
        if not track_id and data.get("track_name"):
            track = _get_or_create_track(data["track_name"])
            track_id = track.id

        session = Session(
            track_id=track_id,
            organizer_id=organizer_id,
            title=data["title"].strip(),
            speaker=data["speaker"].strip(),
            description=(data.get("description") or "").strip() or None,
            start_time=_parse_datetime(data["start_time"]),
            end_time=_parse_datetime(data["end_time"]),
            room=data["room"].strip(),
            capacity=int(data["capacity"]),
        )
        db.session.add(session)
        db.session.commit()
        return {"message": "Session created.", "session": session.to_dict(include_track=True)}, 201
    except Exception:
        db.session.rollback()
        raise


def get_sessions():
    from flask import request

    query = Session.query
    track_id = request.args.get("track_id", type=int)
    speaker = request.args.get("speaker", "").strip()
    from_time = request.args.get("from", "").strip()
    to_time = request.args.get("to", "").strip()

    if track_id:
        query = query.filter(Session.track_id == track_id)
    if speaker:
        query = query.filter(Session.speaker.ilike(f"%{speaker}%"))
    if from_time:
        parsed = _parse_datetime(from_time)
        if parsed:
            query = query.filter(Session.start_time >= parsed)
    if to_time:
        parsed = _parse_datetime(to_time)
        if parsed:
            query = query.filter(Session.end_time <= parsed)

    sessions = query.order_by(Session.start_time).all()
    return {"sessions": [s.to_dict(include_track=True) for s in sessions]}, 200


def get_session(session_id):
    session = db.session.get(Session, session_id)
    if not session:
        return {"error": "Session not found."}, 404
    return {"session": session.to_dict(include_track=True)}, 200


def update_session(session_id, data):
    session = db.session.get(Session, session_id)
    if not session:
        return {"error": "Session not found."}, 404

    errors = _validate_session_payload(data, session_id=session_id)
    if errors:
        return {"errors": errors}, 400

    try:
        track_id = data.get("track_id")
        if not track_id and data.get("track_name"):
            track = _get_or_create_track(data["track_name"])
            track_id = track.id

        session.track_id = track_id
        session.title = data["title"].strip()
        session.speaker = data["speaker"].strip()
        session.description = (data.get("description") or "").strip() or None
        session.start_time = _parse_datetime(data["start_time"])
        session.end_time = _parse_datetime(data["end_time"])
        session.room = data["room"].strip()
        session.capacity = int(data["capacity"])
        db.session.commit()
        return {"message": "Session updated.", "session": session.to_dict(include_track=True)}, 200
    except Exception:
        db.session.rollback()
        raise


def delete_session(session_id):
    session = db.session.get(Session, session_id)
    if not session:
        return {"error": "Session not found."}, 404

    try:
        db.session.delete(session)
        db.session.commit()
        return {"message": "Session deleted."}, 200
    except Exception:
        db.session.rollback()
        raise


def export_session_pdf(session_id):
    session = db.session.get(Session, session_id)
    if not session:
        return {"error": "Session not found."}, 404

    sections = [
        ("Title", session.title),
        ("Speaker", session.speaker),
        ("Track", session.track.name if session.track else ""),
        ("Start", session.start_time.strftime("%Y-%m-%d %H:%M") if session.start_time else ""),
        ("End", session.end_time.strftime("%Y-%m-%d %H:%M") if session.end_time else ""),
        ("Room", session.room),
        ("Capacity", str(session.capacity)),
        ("Enrolled", str(session.enrolled_count)),
        ("Description", session.description or ""),
    ]
    return document_pdf_response(f"session-{session_id}.pdf", session.title, sections)


def export_sessions_csv():
    sessions = Session.query.order_by(Session.start_time).all()
    headers = ["title", "speaker", "track_name", "description", "start_time", "end_time", "room", "capacity"]
    rows = [
        [
            s.title,
            s.speaker,
            s.track.name if s.track else "",
            s.description or "",
            s.start_time.strftime("%Y-%m-%dT%H:%M") if s.start_time else "",
            s.end_time.strftime("%Y-%m-%dT%H:%M") if s.end_time else "",
            s.room,
            s.capacity,
        ]
        for s in sessions
    ]
    date_str = datetime.now().strftime("%Y-%m-%d")
    return rows_to_csv_response(f"sessions-{date_str}.csv", headers, rows)


def export_sessions_pdf():
    sessions = Session.query.order_by(Session.start_time).all()
    headers = ["Title", "Speaker", "Track", "Start", "End", "Room", "Capacity", "Enrolled"]
    rows = [
        [
            s.title,
            s.speaker,
            s.track.name if s.track else "",
            s.start_time.strftime("%H:%M") if s.start_time else "",
            s.end_time.strftime("%H:%M") if s.end_time else "",
            s.room,
            s.capacity,
            s.enrolled_count,
        ]
        for s in sessions
    ]
    date_str = datetime.now().strftime("%Y-%m-%d")
    return table_pdf_response(f"sessions-{date_str}.pdf", "Event Schedule", headers, rows)


def import_sessions_csv(file, organizer_id):
    rows, header_errors = parse_csv_file(
        file,
        ["title", "speaker", "track_name", "start_time", "end_time", "room", "capacity"],
    )
    if header_errors:
        return {"errors": header_errors}, 400

    created = 0
    skipped = 0
    row_errors = []

    for i, row in enumerate(rows, start=2):
        data = {
            "title": row.get("title", ""),
            "speaker": row.get("speaker", ""),
            "track_name": row.get("track_name", ""),
            "description": row.get("description", ""),
            "start_time": row.get("start_time", ""),
            "end_time": row.get("end_time", ""),
            "room": row.get("room", ""),
            "capacity": row.get("capacity", ""),
        }
        errors = _validate_session_payload(data)
        if errors:
            row_errors.append({"row": i, "message": "; ".join(errors)})
            continue

        title = data["title"].strip()
        if Session.query.filter_by(title=title).first():
            skipped += 1
            continue

        try:
            track = _get_or_create_track(data["track_name"])
            session = Session(
                track_id=track.id,
                organizer_id=organizer_id,
                title=title,
                speaker=data["speaker"].strip(),
                description=data["description"].strip() or None,
                start_time=_parse_datetime(data["start_time"]),
                end_time=_parse_datetime(data["end_time"]),
                room=data["room"].strip(),
                capacity=int(data["capacity"]),
            )
            db.session.add(session)
            created += 1
        except Exception as exc:
            row_errors.append({"row": i, "message": str(exc)})

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return {"created": created, "skipped": skipped, "errors": row_errors}, 200


def get_sessions_popularity():
    results = (
        db.session.query(Session, func.count(AgendaItem.id).label("registration_count"))
        .outerjoin(AgendaItem, Session.id == AgendaItem.session_id)
        .group_by(Session.id)
        .order_by(func.count(AgendaItem.id).desc())
        .all()
    )
    sessions = []
    for session, count in results:
        data = session.to_dict(include_track=True)
        data["registration_count"] = count
        sessions.append(data)
    return {"sessions": sessions}, 200
