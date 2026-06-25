import hashlib
import hmac
import json
import base64
import io
import secrets

import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime, cint, flt
from frappe.utils.file_manager import save_file

try:
    import qrcode
    from qrcode.image.svg import SvgImage
    HAS_QR = True
except ImportError:
    HAS_QR = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _get_secret_key(company: str) -> str:
    """دریافت یا تولید کلید امنیتی شرکت"""
    secret = frappe.db.get_value("Company", company, "qr_secret_key")
    if not secret:
        secret = secrets.token_hex(32)
        frappe.db.set_value("Company", company, "qr_secret_key", secret)
        frappe.db.commit()
    return secret


def _sign_qr_data(company: str, secret: str) -> str:
    """امضای داده QR با HMAC"""
    message = f"company:{company}"
    signature = hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()[:16]
    return signature


def _verify_qr_data(company: str, secret: str, signature: str) -> bool:
    """تأیید امضای QR"""
    expected = _sign_qr_data(company, secret)
    return hmac.compare_digest(expected, signature)


def _generate_qr_image(data: str, size: int = 10) -> bytes:
    """تولید تصویر QR به صورت PNG"""
    if not HAS_QR:
        frappe.throw(_("لطفاً کتابخانه qrcode را نصب کنید: pip install qrcode[pil]"))

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


def _get_company_location(company: str) -> dict:
    """دریافت مختصات شرکت"""
    lat, lng, radius = frappe.db.get_value(
        "Company", company,
        ["qr_attendance_latitude", "qr_attendance_longitude", "qr_attendance_radius_meters"]
    )
    return {
        "latitude": flt(lat) if lat else None,
        "longitude": flt(lng) if lng else None,
        "radius": cint(radius) if radius else 200,
    }


def _check_location(user_lat: float, user_lng: float, company: str) -> dict:
    """بررسی فاصله کارمند از شرکت"""
    loc = _get_company_location(company)

    if loc["latitude"] is None or loc["longitude"] is None:
        return {"allowed": True, "message": _("مختصات شرکت تنظیم نشده — بدون بررسی لوکیشن")}

    # Haversine formula
    import math
    R = 6371000  # شعاع زمین به متر

    lat1 = math.radians(loc["latitude"])
    lat2 = math.radians(user_lat)
    dlat = math.radians(user_lat - loc["latitude"])
    dlng = math.radians(user_lng - loc["longitude"])

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c

    allowed = distance <= loc["radius"]
    return {
        "allowed": allowed,
        "distance": round(distance),
        "radius": loc["radius"],
        "message": (
            _("فاصله شما از شرکت: {0} متر — داخل محدوده").format(round(distance))
            if allowed
            else _("فاصله شما از شرکت: {0} متر — خارج از محدوده مجاز ({1} متر)").format(
                round(distance), loc["radius"]
            )
        ),
    }


def _get_employee_from_user() -> str | None:
    """دریافت Employee مرتبط با کاربر فعلی"""
    user = frappe.session.user
    if user in ("Guest", "Administrator"):
        return None
    employee = frappe.db.get_value("Employee", {"user_id": user, "status": "Active"}, "name")
    return employee


def _get_default_company() -> str | None:
    """دریافت شرکت پیش‌فرض"""
    company = frappe.defaults.get_user_default("company")
    if not company:
        companies = frappe.get_all("Company", limit=1, pluck="name")
        company = companies[0] if companies else None
    return company


# ──────────────────────────────────────────────
# API: دریافت QR شرکت
# ──────────────────────────────────────────────

@frappe.whitelist()
def get_company_qr_code():
    """تولید و دریافت کد QR شرکت برای چاپ"""
    # بررسی دسترسی
    if not any(role in frappe.get_roles() for role in ["HR Manager", "System Manager"]):
        frappe.throw(_("فقط مدیر منابع انسانی یا مدیر سیستم مجاز است"), frappe.PermissionError)

    company = _get_default_company()
    if not company:
        frappe.throw(_("شرکت پیش‌فرض یافت نشد"))

    secret = _get_secret_key(company)
    signature = _sign_qr_data(company, secret)

    # ساخت لینک QR
    qr_payload = frappe.utils.get_url() + f"/hrms/qr-scan?company={company}&sig={signature}"

    # تولید تصویر
    qr_bytes = _generate_qr_image(qr_payload)
    qr_base64 = base64.b64encode(qr_bytes).decode("utf-8")

    # ذخیره تصویر روی شرکت
    filename = f"qr-{company}-{frappe.utils.now_datetime().strftime('%Y%m%d%H%M%S')}.png"
    saved = save_file(
        fname=filename,
        content=qr_bytes,
        dt="Company",
        dn=company,
        is_private=0,
    )

    if not saved or not saved.file_url:
        frappe.throw(_("خطا در ذخیره تصویر QR. لطفاً مجدداً تلاش کنید"), frappe.ValidationError)

    frappe.db.set_value("Company", company, "qr_code_image", saved.file_url)
    frappe.db.set_value("Company", company, "qr_generated_on", now_datetime())
    frappe.db.commit()

    return {
        "company": company,
        "qr_code": f"data:image/png;base64,{qr_base64}",
        "qr_image_url": saved.file_url,
        "qr_link": qr_payload,
        "message": _("کد QR شرکت {0} با موفقیت تولید شد").format(company),
    }


# ──────────────────────────────────────────────
# API: دریافت QR شخصی کارمند
# ──────────────────────────────────────────────

@frappe.whitelist()
def get_employee_qr_code():
    """تولید و دریافت کد QR شخصی کارمند"""
    employee = _get_employee_from_user()
    if not employee:
        frappe.throw(_("کارمند فعال یافت نشد"))

    company = _get_default_company()
    if not company:
        frappe.throw(_("شرکت پیش‌فرض یافت نشد"))

    secret = _get_secret_key(company)
    signature = _sign_qr_data(company, secret)

    qr_payload = frappe.utils.get_url() + f"/hrms/qr-scan?company={company}&sig={signature}&employee={employee}"

    qr_bytes = _generate_qr_image(qr_payload)
    qr_base64 = base64.b64encode(qr_bytes).decode("utf-8")

    return {
        "employee": employee,
        "company": company,
        "qr_code": f"data:image/png;base64,{qr_base64}",
        "qr_link": qr_payload,
        "message": _("کد QR شخصی شما تولید شد"),
    }


# ──────────────────────────────────────────────
# API: ثبت اسکن QR
# ──────────────────────────────────────────────

@frappe.whitelist()
def scan_qr_attendance(company: str = None, sig: str = None, qr_data: str = None,
                       latitude: float = None, longitude: float = None):
    """ثبت ورود/خروج کارمند از طریق اسکن QR"""

    # ── استخراج داده از پارامترها ──
    if qr_data and not company:
        # qr_data می‌تواند URL کامل یا payload خام باشد
        try:
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(qr_data)
            params = parse_qs(parsed.query)
            company = params.get("company", [None])[0]
            sig = params.get("sig", [None])[0]
        except Exception:
            pass

    if not company:
        frappe.throw(_("پارامتر company الزامی است"))

    # ── تأیید امضا ──
    secret = frappe.db.get_value("Company", company, "qr_secret_key")
    if not secret:
        frappe.throw(_("کلید امنیتی شرکت یافت نشد. لطفاً ابتدا QR جدید تولید کنید"))

    if sig and not _verify_qr_data(company, secret, sig):
        frappe.throw(_("کد QR نامعتبر است"), frappe.AuthenticationError)

    # ── بررسی لاگین ──
    employee = _get_employee_from_user()
    if not employee:
        frappe.throw(_("لطفاً ابتدا وارد سیستم شوید"), frappe.AuthenticationError)

    # ── بررسی لوکیشن ──
    if latitude is None or longitude is None:
        frappe.throw(
            _("دسترسی به موقعیت جغرافیایی الزامی است. لطفاً اجازه دسترسی به لوکیشن را بدهید"),
            frappe.ValidationError,
        )

    loc_result = _check_location(latitude, longitude, company)
    if not loc_result["allowed"]:
        frappe.throw(loc_result["message"], frappe.ValidationError)

    # ── تعیین نوع ورود/خروج ──
    last_checkin = frappe.db.get_value(
        "Employee Checkin",
        {"employee": employee},
        ["name", "log_type", "time"],
        order_by="time desc",
        as_dict=True,
    )

    if last_checkin and last_checkin.log_type == "IN":
        log_type = "OUT"
    else:
        log_type = "IN"

    # ── ثبت در Employee Checkin ──
    checkin = frappe.new_doc("Employee Checkin")
    checkin.employee = employee
    checkin.log_type = log_type
    checkin.time = now_datetime()
    checkin.device_id = f"QR:{latitude},{longitude}"
    checkin.skip_auto_attendance = 1
    checkin.insert(ignore_permissions=True)
    frappe.db.commit()

    employee_name = frappe.db.get_value("Employee", employee, "employee_name")

    return {
        "success": True,
        "employee": employee,
        "employee_name": employee_name,
        "log_type": log_type,
        "time": str(now_datetime()),
        "message": _("{0} — ورود/خروج ثبت شد ({1})").format(
            employee_name, _("ورود") if log_type == "IN" else _("خروج")
        ),
        "location_check": loc_result,
    }
