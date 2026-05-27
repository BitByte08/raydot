from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.models import Room, Seat, SeatLog, QRCode, User, DoorLog
from schemas.schemas import (
    CheckInRequest,
    CheckInResponse,
    CheckOutRequest,
    SeatMoveRequest,
    RoomCreateRequest,
    RoomSeatsUpdateRequest,
    SeatDisableRequest,
    KioskRegisterRequest,
    DoorRegisterRequest,
    DoorCommandRequest,
)
from utils.auth import get_current_admin, get_current_user
from utils.qr_signer import generate_qr_code
from utils.email import send_email

router = APIRouter(tags=["rooms"])


# --- Public room/seat endpoints ---

@router.get("/api/room/{room_code}/seats")
async def get_room_seats(room_code: str, db: AsyncSession = Depends(get_db)):
    """Get all seats with their current status for a room."""
    result = await db.execute(select(Room).where(Room.code == room_code))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="정독실을 찾을 수 없습니다.")

    result = await db.execute(select(Seat).where(Seat.room_id == room.id))
    seats = result.scalars().all()

    seat_list = []
    for seat in seats:
        if seat.disabled:
            status = "disabled"
            user_id = None
            user_name = None
        else:
            # Check for active seat log (check_in exists, check_out is null)
            log_result = await db.execute(
                select(SeatLog, User)
                .join(User, SeatLog.user_id == User.id)
                .where(SeatLog.seat_id == seat.id, SeatLog.check_out.is_(None))
                .order_by(SeatLog.check_in.desc())
                .limit(1)
            )
            active_log = log_result.first()
            if active_log:
                status = "occupied"
                user_id = active_log.User.id
                user_name = active_log.User.name
            else:
                status = "empty"
                user_id = None
                user_name = None

        seat_list.append({
            "id": seat.id,
            "number": seat.number,
            "status": status,
            "user_id": user_id,
            "user_name": user_name,
        })

    return {"seats": seat_list}


@router.post("/api/room/{room_code}/check-in", response_model=CheckInResponse)
async def check_in(room_code: str, body: CheckInRequest, db: AsyncSession = Depends(get_db)):
    """Check in to a seat — creates seat log and QR code."""
    result = await db.execute(select(Room).where(Room.code == room_code))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="정독실을 찾을 수 없습니다.")

    result = await db.execute(select(Seat).where(Seat.id == body.seat_id))
    seat = result.scalar_one_or_none()
    if not seat or seat.room_id != room.id:
        raise HTTPException(status_code=404, detail="좌석을 찾을 수 없습니다.")

    if seat.disabled:
        raise HTTPException(status_code=400, detail="사용 불가능한 좌석입니다.")

    # Check if seat already occupied
    log_result = await db.execute(
        select(SeatLog).where(SeatLog.seat_id == seat.id, SeatLog.check_out.is_(None))
    )
    if log_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="이미 사용 중인 좌석입니다.")

    # Check if user already has an active seat
    active_result = await db.execute(
        select(SeatLog).where(SeatLog.user_id == body.user_id, SeatLog.check_out.is_(None))
    )
    if active_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="이미 다른 좌석을 사용 중입니다.")

    # Create seat log
    now = datetime.now(timezone.utc)
    seat_log = SeatLog(
        seat_id=seat.id,
        user_id=body.user_id,
        check_in=now,
        pass_type=body.pass_type,
    )
    db.add(seat_log)
    await db.flush()

    # Generate QR code
    qr_string = generate_qr_code(body.user_id, seat.id)
    expires_at = now + timedelta(minutes=30)

    qr_record = QRCode(
        code=qr_string,
        user_id=body.user_id,
        seat_id=seat.id,
        expires_at=expires_at,
    )
    db.add(qr_record)
    await db.commit()

    # Send QR to student email
    user_result = await db.execute(select(User).where(User.id == body.user_id))
    user = user_result.scalar_one_or_none()
    if user and user.email:
        import qrcode
        from io import BytesIO
        import base64

        # Generate QR code image as base64 for email
        qr_img = qrcode.make(qr_string)
        buf = BytesIO()
        qr_img.save(buf, "PNG")
        qr_b64 = base64.b64encode(buf.getvalue()).decode()

        send_email(
            to=user.email,
            subject=f"[Raydot] 입장 QR 코드 - {seat.number}",
            body=f"""
            <div style="text-align:center; padding:20px;">
                <h2>정독실 입장 QR 코드</h2>
                <p>{user.name}님, 입실이 완료되었습니다.</p>
                <p>좌석: {seat.number} | 유효시간: 30분</p>
                <img src="data:image/png;base64,{qr_b64}" style="width:200px;height:200px;" />
                <p style="color:#999; font-size:12px;">정독실 입장 시 이 QR을 스캔하세요</p>
            </div>
            """,
        )

    return CheckInResponse(
        success=True,
        qr_code=qr_string,
        expires_at=expires_at,
    )


@router.post("/api/room/{room_code}/check-out")
async def check_out(room_code: str, body: CheckOutRequest, db: AsyncSession = Depends(get_db)):
    """Check out from a seat."""
    result = await db.execute(
        select(SeatLog).where(
            SeatLog.seat_id == body.seat_id,
            SeatLog.user_id == body.user_id,
            SeatLog.check_out.is_(None),
        )
    )
    seat_log = result.scalar_one_or_none()
    if not seat_log:
        raise HTTPException(status_code=404, detail="활성 입실 기록을 찾을 수 없습니다.")

    seat_log.check_out = datetime.now(timezone.utc)
    await db.commit()

    return {"success": True}


@router.post("/api/room/{room_code}/seat/move")
async def move_seat(room_code: str, body: SeatMoveRequest, db: AsyncSession = Depends(get_db)):
    """Move from one seat to another."""
    # Verify target seat is available
    result = await db.execute(select(Seat).where(Seat.id == body.to_seat_id))
    target_seat = result.scalar_one_or_none()
    if not target_seat or target_seat.disabled:
        raise HTTPException(status_code=400, detail="이동할 좌석을 사용할 수 없습니다.")

    # Check target not occupied
    target_log = await db.execute(
        select(SeatLog).where(SeatLog.seat_id == body.to_seat_id, SeatLog.check_out.is_(None))
    )
    if target_log.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="이미 사용 중인 좌석입니다.")

    # Close current seat log
    current_log_result = await db.execute(
        select(SeatLog).where(
            SeatLog.seat_id == body.from_seat_id,
            SeatLog.user_id == body.user_id,
            SeatLog.check_out.is_(None),
        )
    )
    current_log = current_log_result.scalar_one_or_none()
    if not current_log:
        raise HTTPException(status_code=404, detail="현재 입실 기록을 찾을 수 없습니다.")

    current_log.check_out = datetime.now(timezone.utc)

    # Create new seat log
    new_log = SeatLog(
        seat_id=body.to_seat_id,
        user_id=body.user_id,
        check_in=datetime.now(timezone.utc),
        pass_type=current_log.pass_type,
    )
    db.add(new_log)
    await db.commit()

    return {"success": True}


# --- Admin room/seat endpoints ---

@router.get("/api/admin/rooms")
async def admin_list_rooms(
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """Admin: list all rooms."""
    result = await db.execute(select(Room))
    rooms = result.scalars().all()
    return [
        {
            "id": r.id,
            "code": r.code,
            "name": r.name,
            "kiosk_id": r.kiosk_id,
            "door_id": r.door_id,
        }
        for r in rooms
    ]


@router.post("/api/admin/room/create")
async def admin_create_room(
    body: RoomCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """Admin: create a room with seats."""
    result = await db.execute(select(Room).where(Room.code == body.code))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="이미 존재하는 정독실 코드입니다.")

    room = Room(code=body.code, name=body.name)
    db.add(room)
    await db.flush()

    for seat_data in body.seats:
        seat = Seat(
            room_id=room.id,
            number=seat_data.get("number", ""),
            disabled=not seat_data.get("enabled", True),
        )
        db.add(seat)

    await db.commit()
    return {"success": True, "room_id": room.id}


@router.put("/api/admin/room/{room_code}/seats")
async def admin_update_seats(
    room_code: str,
    body: RoomSeatsUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """Admin: update seat layout for a room."""
    result = await db.execute(select(Room).where(Room.code == room_code))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="정독실을 찾을 수 없습니다.")

    # Delete existing seats and recreate
    result = await db.execute(select(Seat).where(Seat.room_id == room.id))
    existing = result.scalars().all()
    for s in existing:
        await db.delete(s)

    for seat_data in body.seats:
        seat = Seat(
            room_id=room.id,
            number=seat_data.get("number", ""),
            disabled=not seat_data.get("enabled", True),
        )
        db.add(seat)

    await db.commit()
    return {"success": True}


@router.get("/api/admin/room/{room_code}/seat/{seat_id}")
async def admin_get_seat(
    room_code: str,
    seat_id: int,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """Admin: get seat detail."""
    result = await db.execute(select(Seat).where(Seat.id == seat_id))
    seat = result.scalar_one_or_none()
    if not seat:
        raise HTTPException(status_code=404, detail="좌석을 찾을 수 없습니다.")
    return {"id": seat.id, "number": seat.number, "disabled": seat.disabled, "room_id": seat.room_id}


@router.put("/api/admin/room/{room_code}/seat/{seat_id}/disable")
async def admin_toggle_seat(
    room_code: str,
    seat_id: int,
    body: SeatDisableRequest,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """Admin: enable/disable a seat."""
    result = await db.execute(select(Seat).where(Seat.id == seat_id))
    seat = result.scalar_one_or_none()
    if not seat:
        raise HTTPException(status_code=404, detail="좌석을 찾을 수 없습니다.")
    seat.disabled = body.disabled
    await db.commit()
    return {"success": True}


@router.get("/api/admin/room/{room_code}/seat/{seat_id}/logs")
async def admin_seat_logs(
    room_code: str,
    seat_id: int,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """Admin: get seat usage history."""
    result = await db.execute(
        select(SeatLog, User)
        .join(User, SeatLog.user_id == User.id)
        .where(SeatLog.seat_id == seat_id)
        .order_by(SeatLog.check_in.desc())
        .limit(50)
    )
    rows = result.all()
    return [
        {
            "check_in": sl.check_in.isoformat(),
            "check_out": sl.check_out.isoformat() if sl.check_out else None,
            "user_name": u.name,
            "student_id": u.student_id,
            "pass_type": sl.pass_type,
        }
        for sl, u in rows
    ]


# --- Kiosk management ---

@router.post("/api/room/{room_code}/kiosk/register")
async def kiosk_auto_register(
    room_code: str,
    body: KioskRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Public: kiosk auto-registers with room."""
    result = await db.execute(select(Room).where(Room.code == room_code))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="정독실을 찾을 수 없습니다.")
    room.kiosk_id = body.kiosk_id
    await db.commit()
    return {"success": True}


@router.post("/api/admin/room/{room_code}/kiosk/register")
async def register_kiosk(
    room_code: str,
    body: KioskRegisterRequest,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """Admin: link kiosk to room."""
    result = await db.execute(select(Room).where(Room.code == room_code))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="정독실을 찾을 수 없습니다.")
    room.kiosk_id = body.kiosk_id
    await db.commit()
    return {"success": True}


@router.get("/api/admin/room/{room_code}/kiosk/status")
async def kiosk_status(room_code: str, db: AsyncSession = Depends(get_db)):
    """Get kiosk connection status."""
    result = await db.execute(select(Room).where(Room.code == room_code))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="정독실을 찾을 수 없습니다.")
    return {"connected": bool(room.kiosk_id), "kiosk_id": room.kiosk_id}


# --- Door management ---

@router.post("/api/admin/room/{room_code}/door/register")
async def register_door(
    room_code: str,
    body: DoorRegisterRequest,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """Admin: link door to room."""
    result = await db.execute(select(Room).where(Room.code == room_code))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="정독실을 찾을 수 없습니다.")
    room.door_id = body.door_id
    await db.commit()
    return {"success": True}


@router.get("/api/admin/room/{room_code}/door/status")
async def door_status(room_code: str, db: AsyncSession = Depends(get_db)):
    """Get door lock status."""
    result = await db.execute(select(Room).where(Room.code == room_code))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="정독실을 찾을 수 없습니다.")
    return {"connected": bool(room.door_id), "lock_state": "locked"}


@router.get("/api/admin/room/{room_code}/door/logs")
async def door_logs(
    room_code: str,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """Admin: get door event logs."""
    result = await db.execute(select(Room).where(Room.code == room_code))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="정독실을 찾을 수 없습니다.")

    result = await db.execute(
        select(DoorLog, User)
        .join(User, DoorLog.user_id == User.id, isouter=True)
        .where(DoorLog.room_id == room.id)
        .order_by(DoorLog.timestamp.desc())
        .limit(50)
    )
    rows = result.all()
    return [
        {
            "time": dl.timestamp.isoformat(),
            "event": dl.event,
            "user_id": dl.user_id,
            "user_name": u.name if u else None,
        }
        for dl, u in rows
    ]


@router.post("/api/room/{room_code}/door/command")
async def door_command(
    room_code: str,
    body: DoorCommandRequest,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """Admin: send door open/close command."""
    result = await db.execute(select(Room).where(Room.code == room_code))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="정독실을 찾을 수 없습니다.")

    # Log the door command event
    door_log = DoorLog(room_id=room.id, event=body.command)
    db.add(door_log)
    await db.commit()

    # MQTT publish will be handled by the MQTT service
    return {"success": True, "command": body.command}


# --- Public room list (no auth required, for kiosk) ---

@router.get("/api/rooms")
async def public_list_rooms(db: AsyncSession = Depends(get_db)):
    """Public: list all rooms without auth. Used by kiosk."""
    result = await db.execute(select(Room))
    rooms = result.scalars().all()
    return [
        {
            "id": r.id,
            "code": r.code,
            "name": r.name,
            "kiosk_id": r.kiosk_id,
            "door_id": r.door_id,
        }
        for r in rooms
    ]
