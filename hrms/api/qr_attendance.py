# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import base64
import hashlib
import hmac
import json
import secrets
from urllib.parse import parse_qs, urlparse

import frappe
from frappe import _
from frappe.utils import flt, now_datetime

from hrms.hr.utils import get_distance_between_coordinates

QR_MANAGER_ROLES = ("HR Manager", "System Manager")
DEFAULT_QR_RADIUS_METERS = 200


def _generate_qr_secret(company):
	seed = f"{company.name}:{frappe.local.site}:{secrets.token_hex(8)}"
	return hashlib.sha256(seed.encode()).hexdigest()[:32]


def _extract_qr_data(qr_data):
	value = str(qr_data or "").strip()
	if not value:
		return value
	try:
		parsed = urlparse(value)
		params = parse_qs(parsed.query or "")
		if params.get("qr_data"):
			return params["qr_data"][0]
	except Exception:
		pass
	return value


def _decode_qr_payload(qr_data):
	try:
		padded = qr_data + "=" * (-len(qr_data) % 4)
		return json.loads(base64.urlsafe_b64decode(padded.encode()).decode())
	except Exception:
		frappe.throw(_("کد QR نامعتبر است."))


def _payload_signature(company, payload):
	message = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
	return hmac.new(str(company.qr_secret_key).encode(), message, hashlib.sha256).hexdigest()


def _build_qr_payload(company):
	payload = {
		"t": "hrms_attendance",
		"v": 2,
		"co": company.name,
		"site": frappe.local.site,
	}
	payload["sig"] = _payload_signature(company, payload)
	return base64.urlsafe_b64encode(
		json.dumps(payload, separators=(",", ":")).encode()
	).decode().rstrip("=")


def _validate_qr_signature(company, decoded):
	signature = decoded.get("sig")
	if not signature:
		frappe.throw(_("این کد QR قدیمی یا نامعتبر است. لطفاً QR شرکت را دوباره تولید و چاپ کنید."))

	payload = dict(decoded)
	payload.pop("sig", None)
	expected_signature = _payload_signature(company, payload)
	if not hmac.compare_digest(str(signature), expected_signature):
		frappe.throw(_("امضای امنیتی کد QR معتبر نیست."))


def _company_qr_needs_refresh(company):
	if not company.get("qr_code_data"):
		return True
	try:
		decoded = _decode_qr_payload(company.qr_code_data)
		return decoded.get("v") != 2 or not decoded.get("sig") or decoded.get("co") != company.name
	except Exception:
		return True


def _parse_coordinate(value, label):
	if value in (None, ""):
		frappe.throw(_("برای ثبت حضور، دریافت لوکیشن الزامی است."))
	try:
		return float(value)
	except (TypeError, ValueError):
		frappe.throw(_("مقدار {0} معتبر نیست.").format(label))


def _validate_company_location(company, latitude, longitude):
	company_latitude = company.get("qr_attendance_latitude")
	company_longitude = company.get("qr_attendance_longitude")
	if company_latitude in (None, "") or company_longitude in (None, ""):
		frappe.throw(_("محدوده مجاز حضور و غیاب QR برای این شرکت تنظیم نشده است."))

	radius = flt(company.get("qr_attendance_radius_meters")) or DEFAULT_QR_RADIUS_METERS
	if radius <= 0:
		frappe.throw(_("شعاع مجاز حضور و غیاب QR باید بیشتر از صفر باشد."))

	distance = get_distance_between_coordinates(
		float(company_latitude),
		float(company_longitude),
		latitude,
		longitude,
	)
	if distance > radius:
		frappe.throw(
			_("شما خارج از محدوده مجاز شرکت هستید. فاصله شما {0} متر است و حد مجاز {1} متر است.").format(
				int(round(distance)),
				int(round(radius)),
			)
		)
	return distance, radius


def _make_geolocation(latitude, longitude):
	return frappe.json.dumps(
		{
			"type": "FeatureCollection",
			"features": [
				{
					"type": "Feature",
					"properties": {"source": "QR Code"},
					"geometry": {"type": "Point", "coordinates": [longitude, latitude]},
				}
			],
		}
	)


@frappe.whitelist()
def get_company_qr_code():
	frappe.only_for(QR_MANAGER_ROLES)

	employee = frappe.db.get_value(
		"Employee",
		{"user_id": frappe.session.user, "status": "Active"},
		["name", "company", "employee_name"],
		as_dict=True,
	)
	if not employee:
		frappe.throw(_("کارمند فعالی برای حساب کاربری شما یافت نشد."))

	company = frappe.get_doc("Company", employee.company)

	if not company.get("qr_secret_key"):
		company.db_set("qr_secret_key", _generate_qr_secret(company))
		company.reload()

	if _company_qr_needs_refresh(company):
		company.db_set("qr_code_data", _build_qr_payload(company))
		company.db_set("qr_generated_on", now_datetime())
		company.reload()

	return {
		"qr_data": company.qr_code_data,
		"company": company.name,
		"employee": employee.name,
	}


@frappe.whitelist()
def get_employee_qr_code():
	frappe.throw(_("کد QR اختصاصی کارمند غیرفعال شده است. فقط کد QR شرکت استفاده می‌شود."))


@frappe.whitelist()
def scan_qr_attendance(qr_data, log_type=None, latitude=None, longitude=None):
	if not qr_data:
		frappe.throw(_("داده کد QR الزامی است."))

	latitude = _parse_coordinate(latitude, _("عرض جغرافیایی"))
	longitude = _parse_coordinate(longitude, _("طول جغرافیایی"))
	qr_data = _extract_qr_data(qr_data)
	decoded = _decode_qr_payload(qr_data)

	if decoded.get("t") != "hrms_attendance":
		frappe.throw(_("این کد QR برای سیستم حضور و غیاب معتبر نیست."))

	company_name = decoded.get("co")
	if not company_name:
		frappe.throw(_("داده کد QR ناقص است."))

	if decoded.get("emp"):
		frappe.throw(_("کد QR اختصاصی کارمند پذیرفته نمی‌شود. باید QR شرکت را اسکن کنید."))

	if not frappe.db.exists("Company", company_name):
		frappe.throw(_("شرکت یافت نشد."))

	company = frappe.get_doc("Company", company_name)
	if not company.get("qr_secret_key"):
		frappe.throw(_("این شرکت کد QR حضور و غیاب ندارد."))

	_validate_qr_signature(company, decoded)
	distance, radius = _validate_company_location(company, latitude, longitude)

	employee = frappe.db.get_value(
		"Employee",
		{"user_id": frappe.session.user, "status": "Active"},
		["name", "company", "status", "employee_name"],
		as_dict=True,
	)
	if not employee:
		frappe.throw(_("کارمند فعالی برای حساب کاربری شما یافت نشد."))

	if employee.company != company_name:
		frappe.throw(_("شما به این شرکت دسترسی ندارید."))

	if employee.status != "Active":
		frappe.throw(_("حساب کاربری شما فعال نیست."))

	if log_type and log_type not in ("IN", "OUT"):
		frappe.throw(_("نوع عملیات حضور و غیاب معتبر نیست."))

	if not log_type:
		last_checkin = frappe.db.get_all(
			"Employee Checkin",
			filters={"employee": employee.name},
			fields=["log_type"],
			order_by="time desc",
			limit=1,
		)
		log_type = "OUT" if last_checkin and last_checkin[0].log_type == "IN" else "IN"

	now = now_datetime()
	checkin = frappe.get_doc({
		"doctype": "Employee Checkin",
		"employee": employee.name,
		"employee_name": employee.employee_name,
		"log_type": log_type,
		"time": now,
		"device_id": "QR Code",
		"latitude": latitude,
		"longitude": longitude,
		"geolocation": _make_geolocation(latitude, longitude),
	})
	checkin.insert(ignore_permissions=True)
	frappe.db.commit()

	return {
		"status": "success",
		"employee": employee.name,
		"employee_name": employee.employee_name,
		"log_type": log_type,
		"action": "ورود" if log_type == "IN" else "خروج",
		"time": str(now),
		"source": "QR Code",
		"checkin": checkin.name,
		"distance_meters": round(distance, 2),
		"allowed_radius_meters": round(radius, 2),
	}
