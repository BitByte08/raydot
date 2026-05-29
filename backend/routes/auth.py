from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from database import get_db
from models import User, Admin
from schemas import (
    StudentLoginRequest, StudentLoginResponse,
    PasswordInitialRequest, PasswordFindRequest,
    AdminSignUpRequest, AdminLoginRequest, AdminLoginResponse,
    AdminPinVerifyRequest, AdminPinSetRequest,
    AdminCreateByAdminRequest, AdminResponse,
    CardLinkRequest,
)
from utils.password import verify_pin, hash_pin, verify_admin_password, hash_admin_password
from utils.auth import create_access_token, create_admin_token, get_current_admin
from utils.email import send_email
from config import settings

router = APIRouter(prefix="/api", tags=["auth"])


# --- Student Auth ---

@router.post("/auth/login", response_model=StudentLoginResponse)
async def student_login(body: StudentLoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(
            or_(User.student_id == body.student_id, User.card_number == body.student_id)
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    if not user.password_set or not user.pin:
        raise HTTPException(status_code=400, detail="비밀번호를 먼저 설정해주세요.")
    if not verify_pin(body.pin, user.pin):
        raise HTTPException(status_code=401, detail="비밀번호가 틀렸습니다.")

    # Check blacklist
    is_blacklisted = False
    if user.blacklist:
        if user.blacklist_until and user.blacklist_until < datetime.now(timezone.utc):
            # Blacklist expired, clear it
            user.blacklist = False
            user.blacklist_until = None
            user.blacklist_reason = None
            await db.commit()
        else:
            is_blacklisted = True

    token = create_access_token({
        "user_id": user.id,
        "student_id": user.student_id,
    })

    return StudentLoginResponse(
        success=True,
        user={
            "id": user.id,
            "student_id": user.student_id,
            "name": user.name,
            "email": user.email,
        },
        blacklist=is_blacklisted,
        token=token,
    )


@router.post("/auth/password/initial")
async def password_initial(body: PasswordInitialRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.student_id == body.student_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    if user.password_set:
        raise HTTPException(status_code=400, detail="이미 비밀번호가 설정되어 있습니다.")

    user.pin = hash_pin(body.pin)
    user.password_set = True
    await db.commit()
    return {"success": True, "message": "비밀번호가 설정되었습니다."}


@router.post("/auth/password/find")
async def password_find(body: PasswordFindRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.student_id == body.student_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # Send reset email
    token = create_access_token({"student_id": user.student_id}, expires_minutes=30)
    reset_url = f"http://localhost:3000/password/reset?token={token}"
    send_email(
        to=user.email,
        subject="Raydot 비밀번호 재설정",
        body=f'<p>비밀번호 재설정 링크: <a href="{reset_url}">{reset_url}</a></p>',
    )
    return {"success": True, "message": "이메일로 재설정 링크가 발송되었습니다."}


# --- Card Link (barcode registration) ---

@router.post("/auth/link-card")
async def link_card(body: CardLinkRequest, db: AsyncSession = Depends(get_db)):
    """Link a scanned card_number to an existing user by student_id."""
    # Check if this card_number is already linked to someone
    result = await db.execute(select(User).where(User.card_number == body.card_number))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="이미 등록된 카드입니다.")

    # Find user by actual student_id
    result = await db.execute(select(User).where(User.student_id == body.student_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="해당 학번의 사용자를 찾을 수 없습니다.")

    user.card_number = body.card_number
    await db.commit()

    return {
        "success": True,
        "message": "학생증이 등록되었습니다.",
        "user": {
            "id": user.id,
            "student_id": user.student_id,
            "name": user.name,
        },
    }


# --- Admin Auth ---

@router.post("/admin/sign-up")
async def admin_sign_up(body: AdminSignUpRequest, db: AsyncSession = Depends(get_db)):
    if not body.email.endswith(f"@{settings.SCHOOL_EMAIL_DOMAIN}"):
        raise HTTPException(status_code=400, detail="학교 이메일만 사용 가능합니다.")

    result = await db.execute(select(Admin).where(Admin.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")

    admin = Admin(
        email=body.email,
        password_hash=hash_admin_password(body.password),
        name=body.email.split("@")[0],
        verified=False,
        verification_code=body.code,
    )
    db.add(admin)
    await db.commit()
    return {"success": True, "message": "관리자 계정이 생성되었습니다. 이메일을 인증해주세요."}


@router.post("/admin/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Admin).where(Admin.verification_code == token))
    admin = result.scalar_one_or_none()
    if not admin:
        raise HTTPException(status_code=400, detail="유효하지 않은 인증 코드입니다.")
    admin.verified = True
    await db.commit()
    return {"success": True, "message": "이메일 인증이 완료되었습니다."}


@router.post("/admin/login", response_model=AdminLoginResponse)
async def admin_login(body: AdminLoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Admin).where(Admin.email == body.email))
    admin = result.scalar_one_or_none()
    if not admin:
        raise HTTPException(status_code=404, detail="관리자를 찾을 수 없습니다.")
    if not admin.verified:
        raise HTTPException(status_code=403, detail="이메일 인증이 필요합니다.")
    if not verify_admin_password(body.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="비밀번호가 틀렸습니다.")

    token = create_admin_token({"admin_id": admin.id, "role": admin.role})
    return AdminLoginResponse(
        token=token,
        admin={
            "id": admin.id,
            "name": admin.name,
            "email": admin.email,
            "role": admin.role,
        },
    )


@router.post("/admin/verify-pin")
async def admin_verify_pin(body: AdminPinVerifyRequest, db: AsyncSession = Depends(get_db)):
    """Public endpoint for the kiosk to gate admin-only screens behind any admin's 4-digit PIN."""
    result = await db.execute(select(Admin).where(Admin.pin.is_not(None), Admin.verified.is_(True)))
    for admin in result.scalars().all():
        if verify_pin(body.pin, admin.pin):
            return {"success": True, "admin": {"id": admin.id, "name": admin.name}}
    raise HTTPException(status_code=401, detail="PIN이 일치하지 않습니다.")


@router.post("/admin/pin")
async def admin_set_pin(
    body: AdminPinSetRequest,
    db: AsyncSession = Depends(get_db),
    current=Depends(get_current_admin),
):
    if len(body.pin) != 4 or not body.pin.isdigit():
        raise HTTPException(status_code=400, detail="PIN은 숫자 4자리여야 합니다.")
    result = await db.execute(select(Admin).where(Admin.id == current["admin_id"]))
    admin = result.scalar_one_or_none()
    if not admin:
        raise HTTPException(status_code=404, detail="관리자를 찾을 수 없습니다.")
    admin.pin = hash_pin(body.pin)
    await db.commit()
    return {"success": True}


@router.get("/admin/admins", response_model=list[AdminResponse])
async def admin_list(db: AsyncSession = Depends(get_db), current=Depends(get_current_admin)):
    result = await db.execute(select(Admin).order_by(Admin.id))
    return [
        AdminResponse(
            id=a.id, email=a.email, name=a.name, role=a.role,
            verified=a.verified, has_pin=bool(a.pin),
        )
        for a in result.scalars().all()
    ]


@router.post("/admin/admins", response_model=AdminResponse)
async def admin_create(
    body: AdminCreateByAdminRequest,
    db: AsyncSession = Depends(get_db),
    current=Depends(get_current_admin),
):
    """Admin-issued admin creation: pre-verified (no email step), optional starting PIN."""
    if not body.email.endswith(f"@{settings.SCHOOL_EMAIL_DOMAIN}"):
        raise HTTPException(status_code=400, detail="학교 이메일만 사용 가능합니다.")
    exists = await db.execute(select(Admin).where(Admin.email == body.email))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")
    if body.pin is not None and (len(body.pin) != 4 or not body.pin.isdigit()):
        raise HTTPException(status_code=400, detail="PIN은 숫자 4자리여야 합니다.")
    admin = Admin(
        email=body.email,
        password_hash=hash_admin_password(body.password),
        name=body.name or body.email.split("@")[0],
        role=body.role,
        verified=True,
        pin=hash_pin(body.pin) if body.pin else None,
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return AdminResponse(
        id=admin.id, email=admin.email, name=admin.name, role=admin.role,
        verified=admin.verified, has_pin=bool(admin.pin),
    )


@router.delete("/admin/admins/{admin_id}")
async def admin_delete(
    admin_id: int,
    db: AsyncSession = Depends(get_db),
    current=Depends(get_current_admin),
):
    if admin_id == current["admin_id"]:
        raise HTTPException(status_code=400, detail="자기 자신은 삭제할 수 없습니다.")
    result = await db.execute(select(Admin).where(Admin.id == admin_id))
    admin = result.scalar_one_or_none()
    if not admin:
        raise HTTPException(status_code=404, detail="관리자를 찾을 수 없습니다.")
    await db.delete(admin)
    await db.commit()
    return {"success": True}
