import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, async_session
from models.models import User, Admin, Room, Seat
from config import settings


async def seed():
    await init_db()

    async with async_session() as session:
        # Seed admin user
        from utils.password import hash_admin_password
        admin = Admin(
            email="admin@school.edu",
            password_hash=hash_admin_password("admin123"),
            name="관리자",
            role="superadmin",
            verified=True,
        )
        session.add(admin)

        # Seed room
        room = Room(code="R001", name="제1정독실")
        session.add(room)
        await session.commit()
        await session.refresh(room)

        # Seed seats
        for i in range(1, 21):
            seat = Seat(room_id=room.id, number=f"A{i:02d}")
            session.add(seat)

        # Seed test student
        from utils.password import hash_pin
        student = User(
            student_id="2024001",
            name="테스트학생",
            email="test@school.edu",
            pin=hash_pin("1234"),
            password_set=True,
        )
        session.add(student)

        await session.commit()
        print("Database seeded successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
