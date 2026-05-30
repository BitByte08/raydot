from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


# --- Auth schemas ---

class StudentLoginRequest(BaseModel):
    student_id: str
    pin: str


class StudentLoginResponse(BaseModel):
    success: bool
    user: Optional[dict] = None
    blacklist: bool = False
    token: Optional[str] = None


class PasswordInitialRequest(BaseModel):
    student_id: str
    pin: str


class PasswordFindRequest(BaseModel):
    student_id: str


class PasswordResetRequest(BaseModel):
    current_pin: str
    new_pin: str


class AdminSignUpRequest(BaseModel):
    code: str
    email: str
    password: str


class AdminLoginRequest(BaseModel):
    email: str
    password: str


class AdminLoginResponse(BaseModel):
    token: str
    admin: dict


class AdminPinVerifyRequest(BaseModel):
    pin: str


class AdminPinSetRequest(BaseModel):
    pin: str


class AdminCreateByAdminRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None
    role: str = "staff"
    pin: Optional[str] = None


class AdminResponse(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    role: str
    verified: bool
    has_pin: bool

    class Config:
        from_attributes = True


# --- User schemas ---

class UserResponse(BaseModel):
    id: int
    student_id: str
    name: str
    email: str
    password_set: bool
    blacklist: bool
    blacklist_until: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserCreateRequest(BaseModel):
    email: str
    student_id: str
    name: str
    pin: Optional[str] = None


class BlacklistRequest(BaseModel):
    duration: str  # "1w", "1m", "permanent"
    reason: str


# --- Room / Seat schemas ---

class SeatResponse(BaseModel):
    id: int
    number: str
    status: str  # "empty", "occupied", "disabled"
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    pos_x: Optional[int] = None
    pos_y: Optional[int] = None
    disabled: bool = False


class SeatsResponse(BaseModel):
    seats: List[SeatResponse]


class CheckInRequest(BaseModel):
    seat_id: int
    user_id: int
    pass_type: str = "daily"  # daily, weekly, monthly


class CheckInResponse(BaseModel):
    success: bool
    qr_code: Optional[str] = None
    expires_at: Optional[datetime] = None


class CheckOutRequest(BaseModel):
    seat_id: int
    user_id: int
    pin: Optional[str] = None


class SeatMoveRequest(BaseModel):
    from_seat_id: int
    to_seat_id: int
    user_id: int


class RoomCreateRequest(BaseModel):
    code: str
    name: str
    seats: List[dict]  # [{number: "A01", enabled: true}, ...]


class RoomSeatsUpdateRequest(BaseModel):
    seats: List[dict]


class SeatDisableRequest(BaseModel):
    disabled: bool


# --- Card Link schemas ---

class CardLinkRequest(BaseModel):
    student_id: str
    card_number: str


class CardLinkResponse(BaseModel):
    success: bool
    user: Optional[dict] = None
    message: str = ""


# --- Kiosk / Door schemas ---

class KioskRegisterRequest(BaseModel):
    kiosk_id: str


class DoorRegisterRequest(BaseModel):
    door_id: str


class DoorCommandRequest(BaseModel):
    command: str  # "open", "close"
    param: Optional[int] = None  # duration in seconds


# --- QR schemas ---

class QRVerifyRequest(BaseModel):
    qr_code: str


class QRVerifyResponse(BaseModel):
    valid: bool
    user_id: Optional[int] = None
    seat_id: Optional[int] = None
    expires_at: Optional[datetime] = None


# --- Board schemas ---

class NotifyCreateRequest(BaseModel):
    title: str
    content: str
    room_id: Optional[int] = None


class NotifyUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class InquiryCreateRequest(BaseModel):
    user_id: int
    content: str


class InquiryReplyRequest(BaseModel):
    reply: str


class NotifyResponse(BaseModel):
    id: int
    title: str
    content: Optional[str] = None
    author: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class InquiryResponse(BaseModel):
    id: int
    content: str
    status: str
    reply: Optional[str] = None
    reply_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Log schemas ---

class SeatLogResponse(BaseModel):
    date: str
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    seat_id: Optional[int] = None
    seat_number: Optional[str] = None


class DoorLogResponse(BaseModel):
    id: int
    time: datetime
    event: str
    user_id: Optional[int] = None
    user_name: Optional[str] = None
