from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.models import QRCode, BoardNotify, BoardInquiry, Room, User, Admin
from schemas.schemas import (
    QRVerifyRequest,
    NotifyCreateRequest,
    NotifyUpdateRequest,
    InquiryCreateRequest,
    InquiryReplyRequest,
)
from utils.auth import get_current_admin
from utils.qr_signer import verify_qr_signature
from config import settings

router = APIRouter(tags=["qr-board"])


# --- QR endpoints ---

@router.get("/api/qr/{qr_id}")
async def get_qr(qr_id: int, db: AsyncSession = Depends(get_db)):
    """Get QR code details by ID."""
    result = await db.execute(select(QRCode).where(QRCode.id == qr_id))
    qr = result.scalar_one_or_none()
    if not qr:
        raise HTTPException(status_code=404, detail="QR 코드를 찾을 수 없습니다.")
    return {
        "id": qr.id,
        "qr_image_url": f"/api/qr/{qr.id}/image",
        "valid_until": qr.expires_at.isoformat() if qr.expires_at else None,
        "user_id": qr.user_id,
        "seat_id": qr.seat_id,
        "used": qr.used,
    }


@router.post("/api/qr/verify")
async def verify_qr(body: QRVerifyRequest, db: AsyncSession = Depends(get_db)):
    """Verify QR code — called by firmware when QR is scanned.
    Returns firmware-compatible response format."""
    # Verify HMAC signature
    sig_result = verify_qr_signature(body.qr_code)
    if not sig_result.get("valid"):
        return {"success": False}

    user_id = sig_result["user_id"]
    seat_id = sig_result["seat_id"]

    # Check if QR record exists and is not used
    result = await db.execute(select(QRCode).where(QRCode.code == body.qr_code))
    qr = result.scalar_one_or_none()

    if not qr:
        return {"success": False}

    if qr.used:
        return {"success": False}

    now = datetime.now(timezone.utc)
    if qr.expires_at and qr.expires_at < now:
        return {"success": False}

    # Mark QR as used
    qr.used = True
    qr.used_at = now
    await db.commit()

    # Get user name for firmware display
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    user_name = user.name if user else "Unknown"

    # Firmware-compatible response: {"success":true,"user_name":"...","duration":5}
    return {"success": True, "user_name": user_name, "duration": 5}


@router.get("/api/admin/qr")
async def admin_list_qr(
    status: str = Query(None),
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """Admin: list QR codes with optional status filter."""
    query = select(QRCode)
    if status == "used":
        query = query.where(QRCode.used == True)
    elif status == "unused":
        query = query.where(QRCode.used == False)

    result = await db.execute(query.order_by(QRCode.created_at.desc()).limit(100))
    qrs = result.scalars().all()

    return [
        {
            "id": q.id,
            "created_at": q.created_at.isoformat(),
            "user_id": q.user_id,
            "seat_id": q.seat_id,
            "used": q.used,
            "expires_at": q.expires_at.isoformat() if q.expires_at else None,
        }
        for q in qrs
    ]


@router.post("/api/admin/qr/revoke/{qr_id}")
async def revoke_qr(
    qr_id: int,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """Admin: revoke a QR code."""
    result = await db.execute(select(QRCode).where(QRCode.id == qr_id))
    qr = result.scalar_one_or_none()
    if not qr:
        raise HTTPException(status_code=404, detail="QR 코드를 찾을 수 없습니다.")
    qr.used = True
    qr.used_at = datetime.now(timezone.utc)
    await db.commit()
    return {"success": True}


# --- Board Notify endpoints ---

@router.get("/api/board/notify")
async def list_notifies(
    room_code: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Public: list notices, optionally filtered by room."""
    query = select(BoardNotify, Admin).join(Admin, BoardNotify.author_id == Admin.id, isouter=True)
    if room_code:
        room_result = await db.execute(select(Room).where(Room.code == room_code))
        room = room_result.scalar_one_or_none()
        if room:
            query = query.where(BoardNotify.room_id == room.id)

    query = query.order_by(BoardNotify.created_at.desc())
    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "id": n.id,
            "title": n.title,
            "content": n.content,
            "author": a.name if a else None,
            "created_at": n.created_at.isoformat(),
        }
        for n, a in rows
    ]


@router.post("/api/admin/board/notify")
async def create_notify(
    body: NotifyCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """Admin: create a notice."""
    notice = BoardNotify(
        title=body.title,
        content=body.content,
        author_id=admin.get("admin_id"),
        room_id=body.room_id,
    )
    db.add(notice)
    await db.commit()
    await db.refresh(notice)
    return {"success": True, "id": notice.id}


@router.put("/api/admin/board/notify/{notify_id}")
async def update_notify(
    notify_id: int,
    body: NotifyUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """Admin: update a notice."""
    result = await db.execute(select(BoardNotify).where(BoardNotify.id == notify_id))
    notice = result.scalar_one_or_none()
    if not notice:
        raise HTTPException(status_code=404, detail="공지사항을 찾을 수 없습니다.")
    if body.title:
        notice.title = body.title
    if body.content:
        notice.content = body.content
    await db.commit()
    return {"success": True}


@router.delete("/api/admin/board/notify/{notify_id}")
async def delete_notify(
    notify_id: int,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """Admin: delete a notice."""
    result = await db.execute(select(BoardNotify).where(BoardNotify.id == notify_id))
    notice = result.scalar_one_or_none()
    if not notice:
        raise HTTPException(status_code=404, detail="공지사항을 찾을 수 없습니다.")
    await db.delete(notice)
    await db.commit()
    return {"success": True}


# --- Board Inquiry endpoints ---

@router.get("/api/board/inquiry/{user_id}")
async def list_inquiries(user_id: int, db: AsyncSession = Depends(get_db)):
    """Public: list inquiries for a user."""
    result = await db.execute(
        select(BoardInquiry)
        .where(BoardInquiry.user_id == user_id)
        .order_by(BoardInquiry.created_at.desc())
    )
    inquiries = result.scalars().all()
    return [
        {
            "id": i.id,
            "content": i.content,
            "status": i.status,
            "reply": i.reply,
            "reply_at": i.reply_at.isoformat() if i.reply_at else None,
        }
        for i in inquiries
    ]


@router.post("/api/board/inquiry")
async def create_inquiry(body: InquiryCreateRequest, db: AsyncSession = Depends(get_db)):
    """Public: submit an inquiry."""
    inquiry = BoardInquiry(user_id=body.user_id, content=body.content)
    db.add(inquiry)
    await db.commit()
    return {"success": True}


@router.post("/api/admin/board/inquiry/{inquiry_id}/reply")
async def reply_inquiry(
    inquiry_id: int,
    body: InquiryReplyRequest,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """Admin: reply to an inquiry."""
    result = await db.execute(select(BoardInquiry).where(BoardInquiry.id == inquiry_id))
    inquiry = result.scalar_one_or_none()
    if not inquiry:
        raise HTTPException(status_code=404, detail="문의사항을 찾을 수 없습니다.")
    inquiry.reply = body.reply
    inquiry.reply_at = datetime.now(timezone.utc)
    inquiry.status = "answered"
    await db.commit()
    return {"success": True}


@router.delete("/api/admin/board/inquiry/{inquiry_id}")
async def delete_inquiry(
    inquiry_id: int,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """Admin: delete an inquiry."""
    result = await db.execute(select(BoardInquiry).where(BoardInquiry.id == inquiry_id))
    inquiry = result.scalar_one_or_none()
    if not inquiry:
        raise HTTPException(status_code=404, detail="문의사항을 찾을 수 없습니다.")
    await db.delete(inquiry)
    await db.commit()
    return {"success": True}
