from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(20), unique=True, nullable=False, index=True)
    card_number = Column(String(64), unique=True, nullable=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    pin = Column(String(255), nullable=True)  # bcrypt hashed
    password_set = Column(Boolean, default=False)
    blacklist = Column(Boolean, default=False)
    blacklist_until = Column(DateTime, nullable=True)
    blacklist_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    seat_logs = relationship("SeatLog", back_populates="user")
    qr_codes = relationship("QRCode", back_populates="user")
    inquiries = relationship("BoardInquiry", back_populates="user")


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=True)
    role = Column(String(20), default="staff")  # staff, manager, superadmin
    verified = Column(Boolean, default=False)
    verification_code = Column(String(100), nullable=True)
    pin = Column(String(255), nullable=True)  # bcrypt hashed 4-digit kiosk PIN
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    notices = relationship("BoardNotify", back_populates="author")


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=True)
    kiosk_id = Column(String(50), nullable=True)
    door_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    seats = relationship("Seat", back_populates="room", cascade="all, delete-orphan")
    door_logs = relationship("DoorLog", back_populates="room", cascade="all, delete-orphan")
    notices = relationship("BoardNotify", back_populates="room", cascade="all, delete-orphan")


class Seat(Base):
    __tablename__ = "seats"
    __table_args__ = (UniqueConstraint("room_id", "number", name="uq_room_seat"),)

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    number = Column(String(10), nullable=False)
    disabled = Column(Boolean, default=False)

    room = relationship("Room", back_populates="seats")
    seat_logs = relationship("SeatLog", back_populates="seat", cascade="all, delete-orphan")
    qr_codes = relationship("QRCode", back_populates="seat")


class SeatLog(Base):
    __tablename__ = "seat_logs"

    id = Column(Integer, primary_key=True, index=True)
    seat_id = Column(Integer, ForeignKey("seats.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    check_in = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    check_out = Column(DateTime, nullable=True)
    pass_type = Column(String(20), nullable=True)  # daily, weekly, monthly
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    seat = relationship("Seat", back_populates="seat_logs")
    user = relationship("User", back_populates="seat_logs")


class QRCode(Base):
    __tablename__ = "qr_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seat_id = Column(Integer, ForeignKey("seats.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=True)
    used = Column(Boolean, default=False)
    used_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="qr_codes")
    seat = relationship("Seat", back_populates="qr_codes")


class DoorLog(Base):
    __tablename__ = "door_logs"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    event = Column(String(20), nullable=False)  # open, close
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    room = relationship("Room", back_populates="door_logs")
    user = relationship("User")


class BoardNotify(Base):
    __tablename__ = "board_notify"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    author_id = Column(Integer, ForeignKey("admins.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    room = relationship("Room", back_populates="notices")
    author = relationship("Admin", back_populates="notices")


class BoardInquiry(Base):
    __tablename__ = "board_inquiry"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(String(20), default="pending")  # pending, answered
    reply = Column(Text, nullable=True)
    reply_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="inquiries")
