from datetime import date, datetime

import frappe

try:
	import jdatetime

	JDATETIME_AVAILABLE = True
except ImportError:
	JDATETIME_AVAILABLE = False


def gregorian_to_jalali(gregorian_date, format_string="jYYYY/jMM/jDD"):
	"""Convert Gregorian date/datetime to Jalali format string."""
	if not gregorian_date:
		return ""

	if not JDATETIME_AVAILABLE:
		return str(gregorian_date)

	try:
		if isinstance(gregorian_date, str):
			for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
				try:
					gregorian_date = datetime.strptime(gregorian_date, fmt)
					break
				except ValueError:
					continue

		if isinstance(gregorian_date, datetime):
			dt = gregorian_date
			has_time = True
		elif isinstance(gregorian_date, date):
			dt = datetime.combine(gregorian_date, datetime.min.time())
			has_time = False
		else:
			return str(gregorian_date)

		jdt = jdatetime.datetime.fromgregorian(datetime=dt)
		if format_string == "jYYYY/jMM/jDD":
			output = f"{jdt.year}/{jdt.month:02d}/{jdt.day:02d}"
		elif format_string == "jYYYY-jMM-jDD":
			output = f"{jdt.year}-{jdt.month:02d}-{jdt.day:02d}"
		else:
			output = jdt.strftime(format_string)

		if has_time:
			output = f"{output} {dt.strftime('%H:%M:%S')}"

		return output
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Jalali Conversion Error")
		return str(gregorian_date)


def jalali_to_gregorian(jalali_date, format_string=None):
	"""Convert Jalali date string to Gregorian string."""
	if not jalali_date:
		return ""

	if not JDATETIME_AVAILABLE:
		return str(jalali_date)

	try:
		text = str(jalali_date)
		date_part, _, time_part = text.partition(" ")
		year, month, day = [int(v) for v in date_part.replace("-", "/").split("/")]

		jdt = jdatetime.datetime(year, month, day)
		gdt = jdt.togregorian()
		if time_part:
			return f"{gdt.strftime('%Y-%m-%d')} {time_part}"
		return gdt.strftime("%Y-%m-%d")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Jalali Conversion Error")
		return str(jalali_date)
