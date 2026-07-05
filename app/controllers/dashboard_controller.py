from datetime import datetime

from flask_jwt_extended import current_user
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.agenda_item_model import AgendaItem
from app.models.session_model import Session
from app.models.track_model import Track
from app.utils import overlaps
from app.utils.pdf_utils import document_pdf_response


def _attendee_clash_count(user_id):
    items = (
        AgendaItem.query.filter_by(user_id=user_id)
        .join(Session)
        .options(joinedload(AgendaItem.session))
        .all()
    )
    count = 0
    for i, item_a in enumerate(items):
        for item_b in items[i + 1 :]:
            sa, sb = item_a.session, item_b.session
            if sa and sb and overlaps(sa.start_time, sa.end_time, sb.start_time, sb.end_time):
                count += 1
    return count


def get_dashboard():
    if current_user.role == "organizer":
        track_count = Track.query.count()
        session_count = Session.query.count()
        total_registrations = AgendaItem.query.count()
        return {
            "dashboard": {
                "role": "organizer",
                "tracks": track_count,
                "sessions": session_count,
                "total_registrations": total_registrations,
            }
        }, 200

    now = datetime.now()
    items = (
        AgendaItem.query.filter_by(user_id=current_user.id)
        .join(Session)
        .options(joinedload(AgendaItem.session))
        .all()
    )
    upcoming = sum(1 for item in items if item.session and item.session.start_time >= now)
    clash_count = _attendee_clash_count(current_user.id)

    return {
        "dashboard": {
            "role": "attendee",
            "agenda_items": len(items),
            "upcoming_sessions": upcoming,
            "clashes": clash_count,
        }
    }, 200


def export_dashboard_pdf():
    data, _ = get_dashboard()
    dashboard = data["dashboard"]
    sections = [("Role", dashboard["role"])]

    if dashboard["role"] == "organizer":
        sections.extend(
            [
                ("Tracks", str(dashboard["tracks"])),
                ("Sessions", str(dashboard["sessions"])),
                ("Total registrations", str(dashboard["total_registrations"])),
            ]
        )
    else:
        sections.extend(
            [
                ("Agenda items", str(dashboard["agenda_items"])),
                ("Upcoming sessions", str(dashboard["upcoming_sessions"])),
                ("Time clashes", str(dashboard["clashes"])),
            ]
        )

    date_str = datetime.now().strftime("%Y-%m-%d")
    return document_pdf_response(
        f"dashboard-{date_str}.pdf",
        f"Dashboard — {current_user.full_name}",
        sections,
    )
