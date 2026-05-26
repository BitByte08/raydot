from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database import get_db
from models.models import User, SeatLog, Seat, Room
from schemas.schemas import (
    PasswordResetRequest,
    UserCreateRequest,
    BlacklistRequest,
    SeatLogResponse,
)
from utils.auth import get_current_admin, get_current_user
from utils.password import hash_pin, verify_pin

router = APIRouter(tags=["users"])


# --- Student endpoints ---

@router.get("/api/user/{student_id}")
async def get_user(student_id: str, db: AsyncSession = Depends(get_db)):
    """Get user profile by student_id."""
    result = await db.execute(select(User).where(User.student_id == student_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return {
        "id": user.id,
        "student_id": user.student_id,
        "name": user.name,
        "email": user.email,
        "password_set": user.password_set,
        "blacklist": user.blacklist,
        "blacklist_until": user.blacklist_until,
    }


@router.post("/api/user/{student_id}/password/reset")
async def reset_password(
    student_id: str,
    body: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reset student PIN with current PIN verification."""
    result = await db.execute(select(User).where(User.student_id == student_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    if not verify_pin(body.current_pin, user.pin):
        raise HTTPException(status_code=401, detail="현재 비밀번호가 일치하지 않습니다.")

    if len(body.new_pin) != 4 or not body.new_pin.isdigit():
        raise HTTPException(status_code=400, detail="PIN은 4자리 숫자여야 합니다.")

    user.pin = hash_pin(body.new_pin)
    await db.commit()

    return {"success": True, "message": "비밀번호가 변경되었습니다."}


@router.get("/api/user/{student_id}/logs")
async def get_user_logs(
    student_id: str,
    range: str = Query("30d", pattern=r"^\d+d$"),
    db: AsyncSession = Depends(get_db),
):
    """Get seat usage logs for a student."""
    result = await db.execute(select(User).where(User.student_id == student_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    days = int(range.rstrip("d"))
    since = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(SeatLog, Seat)
        .join(Seat, SeatLog.seat_id == Seat.id)
        .where(SeatLog.user_id == user.id, SeatLog.check_in >= since)
        .order_by(SeatLog.check_in.desc())
    )
    rows = result.all()

    logs = []
    for seat_log, seat in rows:
        logs.append({
            "date": seat_log.check_in.strftime("%Y-%m-%d"),
            "check_in_time": seat_log.check_in.isoformat(),
            "check_out_time": seat_log.check_out.isoformat() if seat_log.check_out else None,
            "seat_id": seat.id,
            "seat_number": seat.number,
            "pass_type": seat_log.pass_type,
        })

    return logs


# --- Admin user endpoints ---

@router.post("/api/admin/user/create")
async def admin_create_user(
    body: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """Admin: create a new student user."""
    result = await db.execute(select(User).where(User.student_id == body.student_id))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="이미 존재하는 학번입니다.")

    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")

    user = User(
        student_id=body.student_id,
        name=body.name,
        email=body.email,
        password_set=bool(body.pin),
    )
    if body.pin:
        user.pin = hash_pin(body.pin)

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {"success": True, "user_id": user.id}


@router.get("/api/admin/users")
async def admin_list_users(
    grade: str = Query(None),
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """Admin: list all users with optional grade filter."""
    query = select(User)
    if grade:
        query = query.where(User.student_id.like(f"{grade}%"))
    query = query.order_by(User.student_id)

    result = await db.execute(query)
    users = result.scalars().all()

    return [
        {
            "id": u.id,
            "student_id": u.student_id,
            "name": u.name,
            "email": u.email,
            "blacklist": u.blacklist,
            "password_set": u.password_set,
        }
        for u in users
    ]


@router.get("/api/admin/user/{student_id}/logs")
async def admin_get_user_logs(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """Admin: get all logs for a specific user."""
    result = await db.execute(select(User).where(User.student_id == student_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    result = await db.execute(
        select(SeatLog, Seat)
        .join(Seat, SeatLog.seat_id == Seat.id)
        .where(SeatLog.user_id == user.id)
        .order_by(SeatLog.check_in.desc())
        .limit(100)
    )
    rows = result.all()

    return [
        {
            "date": sl.check_in.strftime("%Y-%m-%d"),
            "check_in_time": sl.check_in.isoformat(),
            "check_out_time": sl.check_out.isoformat() if sl.check_out else None,
            "seat_number": seat.number,
            "pass_type": sl.pass_type,
        }
        for sl, seat in rows
    ]


@router.post("/api/admin/user/{student_id}/blacklist")
async def add_blacklist(
    student_id: str,
    body: BlacklistRequest,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """Admin: add user to blacklist."""
    result = await db.execute(select(User).where(User.student_id == student_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    now = datetime.now(timezone.utc)
    if body.duration == "1w":
        until = now + timedelta(weeks=1)
    elif body.duration == "1m":
        until = now + timedelta(days=30)
    else:
        until = None  # permanent

    user.blacklist = True
    user.blacklist_until = until
    user.blacklist_reason = body.reason
    await db.commit()

    return {"success": True}


@router.delete("/api/admin/user/{student_id}/blacklist")
async def remove_blacklist(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """Admin: remove user from blacklist."""
    result = await db.execute(select(User).where(User.student_id == student_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    user.blacklist = False
    user.blacklist_until = None
    user.blacklist_reason = None
    await db.commit()

    return {"success": True}
