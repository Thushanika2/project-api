from app.extensions import db
from app.utils import utc_now


class AgendaItem(db.Model):
    __tablename__ = "agenda_items"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey("sessions.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)

    __table_args__ = (
        db.UniqueConstraint("user_id", "session_id", name="uq_user_session"),
    )

    def to_dict(self, include_session=False):
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_session and self.session:
            data["session"] = self.session.to_dict(include_track=True)
        return data
