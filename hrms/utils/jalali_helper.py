from datetime import date, datetime, timedelta

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
		input_is_string = isinstance(gregorian_date, str)
		has_time = False

		if isinstance(gregorian_date, str):
			date_text = gregorian_date.strip()
			for fmt, includes_time in (
				("%Y-%m-%d %H:%M:%S.%f", True),
				("%Y-%m-%d %H:%M:%S", True),
				("%Y-%m-%d", False),
			):
				try:
					gregorian_date = datetime.strptime(date_text, fmt)
					has_time = includes_time
					break
				except ValueError:
					continue

		if isinstance(gregorian_date, datetime):
			dt = gregorian_date
			if not input_is_string:
				has_time = True
		elif isinstance(gregorian_date, date):
			dt = datetime.combine(gregorian_date, datetime.min.time())
			if not input_is_string:
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


def gregorian_to_jalali_date(gregorian_date):
	"""Convert Gregorian date/datetime/string to a jdatetime.date."""
	if not gregorian_date or not JDATETIME_AVAILABLE:
		return None

	if isinstance(gregorian_date, str):
		text = gregorian_date.strip().split(" ", 1)[0]
		try:
			gregorian_date = datetime.strptime(text, "%Y-%m-%d").date()
		except ValueError:
			return None
	elif isinstance(gregorian_date, datetime):
		gregorian_date = gregorian_date.date()
	elif not isinstance(gregorian_date, date):
		return None

	return jdatetime.date.fromgregorian(date=gregorian_date)


def get_jalali_month_last_date(year, month):
	"""Return the last day of a Jalali month as jdatetime.date."""
	if not JDATETIME_AVAILABLE:
		return None

	if month == 12:
		next_month_start = jdatetime.date(year + 1, 1, 1)
	else:
		next_month_start = jdatetime.date(year, month + 1, 1)

	return jdatetime.date.fromgregorian(date=next_month_start.togregorian() - timedelta(days=1))


def get_jalali_month_start_end(gregorian_date):
	"""Return Gregorian start/end dates of the Jalali month containing the input date."""
	if not JDATETIME_AVAILABLE:
		return None, None

	jalali_date = gregorian_to_jalali_date(gregorian_date)
	if not jalali_date:
		return None, None

	start = jdatetime.date(jalali_date.year, jalali_date.month, 1)
	end = get_jalali_month_last_date(jalali_date.year, jalali_date.month)
	return start.togregorian(), end.togregorian()


def add_jalali_months(gregorian_date, months, day=None):
	"""Shift a Gregorian date by Jalali months and return a Gregorian date."""
	if not JDATETIME_AVAILABLE:
		return gregorian_date

	jalali_date = gregorian_to_jalali_date(gregorian_date)
	if not jalali_date:
		return gregorian_date

	month_index = (jalali_date.year * 12) + (jalali_date.month - 1) + months
	year = month_index // 12
	month = (month_index % 12) + 1

	last_day = get_jalali_month_last_date(year, month).day
	target_day = min(day or jalali_date.day, last_day)
	return jdatetime.date(year, month, target_day).togregorian()


def get_same_jalali_day_in_month(reference_date, target_date):
	"""Return Gregorian date for the reference Jalali day in the target Jalali month."""
	if not JDATETIME_AVAILABLE:
		return target_date

	reference_jalali = gregorian_to_jalali_date(reference_date)
	target_jalali = gregorian_to_jalali_date(target_date)
	if not reference_jalali or not target_jalali:
		return target_date

	last_day = get_jalali_month_last_date(target_jalali.year, target_jalali.month).day
	target_day = min(reference_jalali.day, last_day)
	return jdatetime.date(target_jalali.year, target_jalali.month, target_day).togregorian()
