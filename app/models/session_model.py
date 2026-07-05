from app.extensions import db
from app.models.agenda_item_model import AgendaItem
from app.utils import utc_now


class Session(db.Model):
    __tablename__ = "sessions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    track_id = db.Column(db.Integer, db.ForeignKey("tracks.id"), nullable=False)
    organizer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    speaker = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    room = db.Column(db.String(255), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)

    agenda_items = db.relationship("AgendaItem", backref="session", lazy="dynamic")

    @property
    def enrolled_count(self):
        return self.agenda_items.count()

    @property
    def is_full(self):
        return self.enrolled_count >= self.capacity

    def to_dict(self, include_track=False):
        data = {
            "id": self.id,
            "track_id": self.track_id,
            "organizer_id": self.organizer_id,
            "title": self.title,
            "speaker": self.speaker,
            "description": self.description,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "room": self.room,
            "capacity": self.capacity,
            "enrolled_count": self.enrolled_count,
            "is_full": self.is_full,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_track and self.track:
            data["track"] = self.track.to_dict()
        return data
