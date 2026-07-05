"""Seed demo data for the Conference Scheduler viva demo."""

from datetime import datetime

from app import create_app
from app.extensions import db
from app.models.agenda_item_model import AgendaItem
from app.models.session_model import Session
from app.models.track_model import Track
from app.models.user_model import User


def seed():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        organizer = User(
            email="organizer@confsched.test",
            full_name="Event Organizer",
            role="organizer",
        )
        organizer.set_password("Admin123")

        alice = User(
            email="alice@confsched.test",
            full_name="Alice Chen",
            role="attendee",
        )
        alice.set_password("Alice123")

        bob = User(
            email="bob@confsched.test",
            full_name="Bob Martinez",
            role="attendee",
        )
        bob.set_password("Bob123")

        db.session.add_all([organizer, alice, bob])
        db.session.flush()

        tracks = [
            Track(name="Engineering", description="Deep technical talks"),
            Track(name="Design", description="UX and product design"),
            Track(name="Data & AI", description="Data science and ML"),
            Track(name="Product", description="Product strategy"),
            Track(name="Career", description="Career growth"),
        ]
        db.session.add_all(tracks)
        db.session.flush()

        track_map = {t.name: t for t in tracks}
        event_day = datetime(2026, 9, 10)

        sessions_data = [
            ("Scaling GraphQL at the Edge", "Priya Nair", "Engineering", "Lessons from serving 1B requests/day", 9, 0, 9, 45, "Hall A", 120),
            ("Designing for Trust", "Sam Okafor", "Design", "Building trust into onboarding flows", 9, 0, 9, 45, "Hall B", 80),
            ("Real-time ML Pipelines", "Jordan Lee", "Data & AI", "Streaming inference at scale", 10, 0, 10, 45, "Hall C", 100),
            ("Roadmaps That Ship", "Mia Torres", "Product", "Aligning teams around outcomes", 10, 0, 10, 45, "Hall D", 90),
            ("From IC to Lead", "Alex Kim", "Career", "Making the transition", 11, 0, 11, 45, "Hall E", 60),
            ("Zero-Downtime Deploys", "Chris Park", "Engineering", "Blue-green in production", 11, 0, 11, 45, "Hall A", 100),
            ("Design Systems at Scale", "Nina Patel", "Design", "Tokens, components, governance", 14, 0, 14, 45, "Hall B", 75),
            ("LLMs in Production", "Ravi Singh", "Data & AI", "Evals, guardrails, cost control", 14, 0, 14, 45, "Hall C", 118),
        ]

        sessions = []
        for title, speaker, track_name, desc, sh, sm, eh, em, room, cap in sessions_data:
            session = Session(
                track_id=track_map[track_name].id,
                organizer_id=organizer.id,
                title=title,
                speaker=speaker,
                description=desc,
                start_time=event_day.replace(hour=sh, minute=sm),
                end_time=event_day.replace(hour=eh, minute=em),
                room=room,
                capacity=cap,
            )
            sessions.append(session)

        db.session.add_all(sessions)
        db.session.flush()

        llm_session = next(s for s in sessions if s.title == "LLMs in Production")
        for _ in range(117):
            filler = User(
                email=f"filler{_}@confsched.test",
                full_name=f"Filler {_}",
                role="attendee",
            )
            filler.set_password("pass")
            db.session.add(filler)
            db.session.flush()
            db.session.add(AgendaItem(user_id=filler.id, session_id=llm_session.id))

        bob_sessions = [s for s in sessions if s.title in ("Real-time ML Pipelines", "Roadmaps That Ship")]
        for s in bob_sessions:
            db.session.add(AgendaItem(user_id=bob.id, session_id=s.id))

        db.session.commit()
        print("Seed complete.")
        print("Organizer: organizer@confsched.test / Admin123")
        print("Alice:     alice@confsched.test / Alice123")
        print("Bob:       bob@confsched.test / Bob123")


if __name__ == "__main__":
    seed()
