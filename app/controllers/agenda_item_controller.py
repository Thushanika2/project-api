from datetime import datetime

from flask_jwt_extended import current_user
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.agenda_item_model import AgendaItem
from app.models.session_model import Session
from app.utils import overlaps
from app.utils.csv_utils import parse_csv_file, rows_to_csv_response
from app.utils.pdf_utils import document_pdf_response, table_pdf_response


def _find_overlap_warning(user_id, session):
    existing_items = (
        AgendaItem.query.filter_by(user_id=user_id)
        .options(joinedload(AgendaItem.session))
        .all()
    )
    for item in existing_items:
        other = item.session
        if other and overlaps(session.start_time, session.end_time, other.start_time, other.end_time):
            start = other.start_time.strftime("%H:%M") if other.start_time else ""
            end = other.end_time.strftime("%H:%M") if other.end_time else ""
            return f"This session overlaps with '{other.title}' ({start}–{end})."
    return None


def _detect_clashes(agenda_items):
    clashes = []
    items = sorted(agenda_items, key=lambda a: a.session.start_time if a.session else datetime.min)
    for i, item_a in enumerate(items):
        for item_b in items[i + 1 :]:
            sa, sb = item_a.session, item_b.session
            if sa and sb and overlaps(sa.start_time, sa.end_time, sb.start_time, sb.end_time):
                clashes.append(
                    {
                        "session_a_id": sa.id,
                        "session_b_id": sb.id,
                        "message": f"'{sa.title}' overlaps with '{sb.title}'.",
                    }
                )
    return clashes


def get_agenda():
    items = (
        AgendaItem.query.filter_by(user_id=current_user.id)
        .join(Session)
        .options(joinedload(AgendaItem.session).joinedload(Session.track))
        .order_by(Session.start_time)
        .all()
    )
    clashes = _detect_clashes(items)
    return {
        "agenda_items": [item.to_dict(include_session=True) for item in items],
        "clashes": clashes,
    }, 200


def create_agenda_item(data):
    session_id = data.get("session_id")
    if not session_id:
        return {"error": "session_id is required."}, 400

    session = db.session.get(Session, session_id)
    if not session:
        return {"error": "Session not found."}, 404

    existing = AgendaItem.query.filter_by(user_id=current_user.id, session_id=session_id).first()
    if existing:
        return {"error": "Session already in your agenda."}, 409

    if session.is_full:
        return {"error": "Session is full."}, 409

    warning = _find_overlap_warning(current_user.id, session)

    try:
        item = AgendaItem(user_id=current_user.id, session_id=session_id)
        db.session.add(item)
        db.session.commit()
        response = {
            "message": "Session added to agenda.",
            "agenda_item": item.to_dict(include_session=True),
        }
        if warning:
            response["warning"] = warning
        return response, 201
    except Exception:
        db.session.rollback()
        raise


def delete_agenda_item(agenda_item_id):
    item = db.session.get(AgendaItem, agenda_item_id)
    if not item:
        return {"error": "Agenda item not found."}, 404
    if item.user_id != current_user.id:
        return {"error": "Insufficient permissions."}, 403

    try:
        db.session.delete(item)
        db.session.commit()
        return {"message": "Session removed from agenda."}, 200
    except Exception:
        db.session.rollback()
        raise


def export_agenda_csv():
    items = (
        AgendaItem.query.filter_by(user_id=current_user.id)
        .join(Session)
        .options(joinedload(AgendaItem.session))
        .order_by(Session.start_time)
        .all()
    )
    headers = ["session_title"]
    rows = [[item.session.title] for item in items if item.session]
    date_str = datetime.now().strftime("%Y-%m-%d")
    return rows_to_csv_response(f"agenda-{date_str}.csv", headers, rows)


def export_agenda_pdf():
    items = (
        AgendaItem.query.filter_by(user_id=current_user.id)
        .join(Session)
        .options(joinedload(AgendaItem.session).joinedload(Session.track))
        .order_by(Session.start_time)
        .all()
    )
    clashes = _detect_clashes(items)
    clash_notes = [c["message"] for c in clashes]

    sections = [("Attendee", current_user.full_name)]
    for item in items:
        s = item.session
        if not s:
            continue
        time_str = ""
        if s.start_time and s.end_time:
            time_str = f"{s.start_time.strftime('%Y-%m-%d %H:%M')} – {s.end_time.strftime('%H:%M')}"
        sections.append((s.title, f"{time_str} | {s.room} | {s.track.name if s.track else ''}"))

    if clash_notes:
        sections.append(("Clash warnings", "; ".join(clash_notes)))

    date_str = datetime.now().strftime("%Y-%m-%d")
    return document_pdf_response(f"agenda-{date_str}.pdf", "My Agenda", sections)


def import_agenda_csv(file):
    rows, header_errors = parse_csv_file(file, ["session_title"])
    if header_errors:
        return {"errors": header_errors}, 400

    created = 0
    skipped = 0
    row_errors = []
    warnings = []

    for i, row in enumerate(rows, start=2):
        title = (row.get("session_title") or "").strip()
        if not title:
            row_errors.append({"row": i, "message": "session_title is required."})
            continue

        session = Session.query.filter(Session.title.ilike(title)).first()
        if not session:
            row_errors.append({"row": i, "message": f"Session '{title}' not found."})
            continue

        existing = AgendaItem.query.filter_by(user_id=current_user.id, session_id=session.id).first()
        if existing:
            skipped += 1
            continue

        if session.is_full:
            row_errors.append({"row": i, "message": "Session is full."})
            continue

        warning = _find_overlap_warning(current_user.id, session)
        item = AgendaItem(user_id=current_user.id, session_id=session.id)
        db.session.add(item)
        created += 1
        if warning:
            warnings.append({"row": i, "message": warning})

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return {"created": created, "skipped": skipped, "errors": row_errors, "warnings": warnings}, 200
